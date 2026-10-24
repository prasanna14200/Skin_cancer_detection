"""Gated nine-class EG-VAN training runner. No training occurs on import."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.optim import Adamax
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from models.egvan import build_nine_class_egvan
from nine_class_dataset import NineClassDataset, preprocessing_for_training, preprocessing_hash
from nine_class_metrics import summarize_predictions
from nine_class_protocol import file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES, ROOT

DEFAULT_CONFIG = ROOT / "config/nine_class_training_v1.json"
DEFAULT_INVENTORY = ROOT / "analysis/nine_class_stage4/nine_class_source_manifest.csv"


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != "nine_class_training_v1" or tuple(config.get("label_order", ())) != CLASS_NAMES:
        raise ValueError("Unknown training config or nine-class order")
    if config.get("image_size") != 384 or config.get("optimizer") != "Adamax":
        raise ValueError("Stage 6 requires 384px input and Adamax")
    if int(config["batch_size"]) < 1 or int(config["epochs"]) < 1 or float(config["learning_rate"]) <= 0:
        raise ValueError("Invalid batch, epoch or learning-rate setting")
    steps = config.get("gradient_accumulation_steps", 1)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("gradient_accumulation_steps must be a positive integer")
    if config["initialization"]["mode"] not in ("random", "local"):
        raise ValueError("Only random or explicitly local weight initialization is allowed")
    if config["initialization"]["mode"] == "local" and not any(
        config["initialization"].get(key) for key in ("efficient_local_state", "resnet_local_state")
    ):
        raise ValueError("Local initialization needs a local state path")
    if config.get("mixed_precision") not in ("off", "cuda_if_available"):
        raise ValueError("Mixed precision must be off or CUDA gated")
    preprocessing_for_training(config)
    return config


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def training_class_weights(rows: list[dict[str, str]]) -> torch.Tensor:
    counts = torch.tensor([sum(r["split"] == "train" and r["class_name"] == name for r in rows)
                           for name in CLASS_NAMES], dtype=torch.float32)
    if (counts <= 0).any():
        raise ValueError("Class weights require approved training examples in all nine classes")
    weights = counts.reciprocal()
    return weights / weights.mean()


def focal_loss(logits: torch.Tensor, targets: torch.Tensor, *, alpha: float = 0.25,
               gamma: float = 2.0, class_weights: torch.Tensor | None = None) -> torch.Tensor:
    if logits.ndim != 2 or logits.shape[1] != 9 or targets.shape != (len(logits),):
        raise ValueError("Focal loss requires B×9 logits and B targets")
    if not torch.isfinite(logits).all() or gamma < 0 or alpha <= 0:
        raise ValueError("Invalid focal inputs or hyperparameters")
    ce = F.cross_entropy(logits.float(), targets, reduction="none")
    loss = alpha * (1 - (-ce).exp()).pow(gamma) * ce
    if class_weights is not None:
        if class_weights.shape != (9,):
            raise ValueError("Nine class weights required")
        loss = loss * class_weights.to(logits.device)[targets]
    return loss.mean()


def build_model(config: dict, root: Path) -> tuple[nn.Module, dict[str, str]]:
    model = build_nine_class_egvan(fusion_channels=int(config["fusion_channels"]))
    hashes = {}
    if config["initialization"]["mode"] == "local":
        for key, branch in (("efficient_local_state", model.efficient),
                            ("resnet_local_state", model.resnet)):
            if config["initialization"].get(key):
                path = (root / config["initialization"][key]).resolve()
                if not path.is_file():
                    raise FileNotFoundError(path)
                # Only use local, explicitly supplied branch state dictionaries.
                branch.load_state_dict(torch.load(path, map_location="cpu", weights_only=True), strict=True)
                hashes[key] = file_sha256(path)
    return model, hashes


def save_checkpoint(path: Path, state: dict) -> None:
    """Atomically replace only a checkpoint belonging to the current run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(temporary)
    try:
        torch.save(state, temporary)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_checkpoint(path: Path, model: nn.Module, optimizer=None, scheduler=None,
                    scaler=None, *, expected: dict[str, str] | None = None) -> dict:
    # Checkpoints are project-owned pickle files. Never load an untrusted path.
    state = torch.load(path, map_location="cpu", weights_only=False)
    if expected and any(state.get(key) != value for key, value in expected.items()):
        raise ValueError("Checkpoint configuration or cohort provenance mismatch")
    model.load_state_dict(state["model_state"])
    if optimizer is not None:
        optimizer.load_state_dict(state["optimizer_state"])
    if scheduler is not None and state.get("scheduler_state") is not None:
        scheduler.load_state_dict(state["scheduler_state"])
    if scaler is not None and state.get("scaler_state") is not None:
        scaler.load_state_dict(state["scaler_state"])
    return state


def run_epoch(model: nn.Module, loader: DataLoader, device: torch.device,
              config: dict, *, optimizer=None, scaler=None,
              class_weights=None) -> dict:
    training = optimizer is not None
    model.train(training)
    amp = bool(device.type == "cuda" and config["mixed_precision"] == "cuda_if_available")
    losses, probs, targets = [], [], []
    accumulation_steps = int(config.get("gradient_accumulation_steps", 1))
    accumulated_samples = 0
    if training:
        optimizer.zero_grad(set_to_none=True)
    for batch_index, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)
        with torch.set_grad_enabled(training):
            with torch.autocast(device_type=device.type, enabled=amp):
                logits = model(images)
                loss = focal_loss(logits, labels, alpha=float(config["focal_alpha"]),
                                  gamma=float(config["focal_gamma"]), class_weights=class_weights)
            if training:
                # Sum sample losses, then divide gradients by the actual number
                # of samples in this update. This handles a partial final batch.
                if scaler is not None and amp:
                    scaler.scale(loss * len(labels)).backward()
                else:
                    (loss * len(labels)).backward()
                accumulated_samples += len(labels)
                if (batch_index + 1) % accumulation_steps == 0 or batch_index + 1 == len(loader):
                    if scaler is not None and amp:
                        scaler.unscale_(optimizer)
                    for parameter in model.parameters():
                        if parameter.grad is not None:
                            parameter.grad.div_(accumulated_samples)
                    clip = config.get("gradient_clip_norm")
                    if clip is not None:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), float(clip))
                    if scaler is not None and amp:
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
                    accumulated_samples = 0
        losses.append((float(loss.detach()), len(labels)))
        probs.append(torch.softmax(logits.detach().float(), dim=1).cpu().numpy())
        targets.extend(labels.cpu().tolist())
    report = summarize_predictions(np.concatenate(probs), np.array(targets),
                                   split="train" if training else "validation")
    report["loss"] = sum(loss * count for loss, count in losses) / sum(count for _, count in losses)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--approved-split", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "analysis/nine_class_stage6/runs")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    rows, provenance = validate_approved_split(args.root, args.approved_split, args.approval, args.inventory)
    if args.validate_only:
        print(json.dumps({"approved_split_valid": True, "counts": provenance["counts"]}, indent=2))
        return 0
    if not provenance["approval"].get("test_partition_frozen") or not provenance["test_has_all_classes"]:
        raise ValueError("Full training requires a frozen protected test with all nine classes")
    seed_all(int(config["seed"]))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, initialization_hashes = build_model(config, args.root)
    model.to(device)
    optimizer = Adamax(model.parameters(), lr=float(config["learning_rate"]))
    scheduler_cfg = config["scheduler"]
    scheduler = (ReduceLROnPlateau(optimizer, mode="min", factor=float(scheduler_cfg["factor"]),
                                   patience=int(scheduler_cfg["patience"]))
                 if scheduler_cfg["name"] == "ReduceLROnPlateau" else None)
    amp = device.type == "cuda" and config["mixed_precision"] == "cuda_if_available"
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    class_weights = training_class_weights(rows).to(device) if config["class_weighting"] else None
    preprocess = preprocessing_for_training(config)
    preprocess_sha = preprocessing_hash(preprocess)
    expected = {"config_sha256": file_sha256(args.config),
                "split_sha256": provenance["split_sha256"],
                "inventory_sha256": provenance["inventory_sha256"],
                "approval_sha256": provenance["approval_sha256"],
                "preprocess_config_sha256": preprocess_sha}
    if args.resume:
        checkpoint = args.resume.resolve()
        run_dir = checkpoint.parent
        if checkpoint.name != "last.pt" or not (run_dir / "run_provenance.json").is_file():
            raise ValueError("Resume requires this runner's last.pt and run provenance")
        state = load_checkpoint(checkpoint, model, optimizer, scheduler, scaler, expected=expected)
        start_epoch = int(state["epoch"]) + 1
        best_loss = float(state["best_validation_loss"])
        bad_epochs = int(state["bad_epochs"])
    else:
        run_dir = args.runs_root / (datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / "run_provenance.json").write_text(json.dumps({**expected, "config": config,
            "approval": provenance["approval"], "initialization_hashes": initialization_hashes,
            "device": str(device)}, indent=2) + "\n", encoding="utf-8")
        start_epoch, best_loss, bad_epochs = 0, float("inf"), 0
    train_data = NineClassDataset(args.root, args.approved_split, "train", preprocess)
    val_data = NineClassDataset(args.root, args.approved_split, "validation", preprocess)
    history = run_dir / "history.csv"
    for epoch in range(start_epoch, int(config["epochs"])):
        # Epoch-boundary deterministic resume, including DataLoader order and augmentation.
        seed_all(int(config["seed"]) + epoch)
        generator = torch.Generator().manual_seed(int(config["seed"]) + epoch)
        common = dict(batch_size=int(config["batch_size"]), num_workers=int(config["num_workers"]),
                      pin_memory=device.type == "cuda")
        train_loader = DataLoader(train_data, shuffle=True, generator=generator, **common)
        val_loader = DataLoader(val_data, shuffle=False, **common)
        train_result = run_epoch(model, train_loader, device, config, optimizer=optimizer,
                                 scaler=scaler, class_weights=class_weights)
        val_result = run_epoch(model, val_loader, device, config, class_weights=class_weights)
        if scheduler is not None:
            scheduler.step(val_result["loss"])
        improved = val_result["loss"] < best_loss
        best_loss = min(best_loss, val_result["loss"])
        bad_epochs = 0 if improved else bad_epochs + 1
        state = {**expected, "epoch": epoch, "model_state": model.state_dict(),
                 "optimizer_state": optimizer.state_dict(),
                 "scheduler_state": scheduler.state_dict() if scheduler else None,
                 "scaler_state": scaler.state_dict(), "best_validation_loss": best_loss,
                 "bad_epochs": bad_epochs, "python_rng": random.getstate(),
                 "numpy_rng": np.random.get_state(), "torch_rng": torch.get_rng_state(),
                 "train_metrics": train_result, "validation_metrics": val_result,
                 "initialization_hashes": initialization_hashes}
        save_checkpoint(run_dir / "last.pt", state)
        if improved:
            save_checkpoint(run_dir / "best.pt", state)
        with history.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=("epoch", "train_loss", "train_accuracy",
                                                     "train_macro_f1", "validation_loss",
                                                     "validation_accuracy", "validation_macro_f1", "learning_rate"))
            if handle.tell() == 0:
                writer.writeheader()
            writer.writerow({"epoch": epoch + 1, "train_loss": train_result["loss"],
                             "train_accuracy": train_result["accuracy"],
                             "train_macro_f1": train_result["macro_f1"],
                             "validation_loss": val_result["loss"],
                             "validation_accuracy": val_result["accuracy"],
                             "validation_macro_f1": val_result["macro_f1"],
                             "learning_rate": optimizer.param_groups[0]["lr"]})
        print(json.dumps({"epoch": epoch + 1, "train_loss": train_result["loss"],
                          "validation_loss": val_result["loss"], "run_dir": str(run_dir)}))
        if config["early_stopping"]["enabled"] and bad_epochs >= int(config["early_stopping"]["patience"]):
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
