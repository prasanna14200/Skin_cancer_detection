"""Gated nine-class EG-VAN training runner. No training occurs on import."""

from __future__ import annotations

import argparse
import csv
import json
import math
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

from nine_class_dataset import NineClassDataset, preprocessing_for_training, preprocessing_hash
from nine_class_metrics import summarize_predictions
from nine_class_protocol import file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES, ROOT

DEFAULT_CONFIG = ROOT / "config/nine_class_training_v1.json"
DEFAULT_INVENTORY = ROOT / "analysis/nine_class_stage4/nine_class_source_manifest.csv"
DEFAULT_RUNS_ROOT = ROOT / "analysis/nine_class_stage6/runs"


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") not in ("nine_class_training_v1", "nine_class_training_v2") or tuple(config.get("label_order", ())) != CLASS_NAMES:
        raise ValueError("Unknown training config or nine-class order")
    if config["schema_version"] == "nine_class_training_v2" and config.get("split_protocol") != "four_way_v1":
        raise ValueError("Version-2 training requires the four-way split protocol")
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
    if config.get("batchnorm_policy", "train_running_stats") not in ("train_running_stats", "freeze_running_stats"):
        raise ValueError("Unknown BatchNorm running-statistics policy")
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


def _serialize_numpy_rng_state() -> dict:
    algorithm, keys, position, has_gauss, cached_gaussian = np.random.get_state()
    return {
        "algorithm": algorithm,
        "keys": keys.tolist(),
        "position": int(position),
        "has_gauss": int(has_gauss),
        "cached_gaussian": float(cached_gaussian),
    }


def capture_rng_state() -> dict:
    return {
        "python_rng": random.getstate(),
        "numpy_rng": _serialize_numpy_rng_state(),
        "torch_rng": torch.get_rng_state(),
        "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def _validated_rng_states(state: dict) -> tuple[tuple, tuple, torch.Tensor, list[torch.Tensor]]:
    try:
        python_rng = state["python_rng"]
        numpy_payload = state["numpy_rng"]
        torch_rng = state["torch_rng"]
        cuda_rng = state["cuda_rng"]
        random.Random().setstate(python_rng)
        if not isinstance(numpy_payload, dict):
            raise ValueError("NumPy RNG state must use the safe mapping format")
        numpy_keys = np.asarray(numpy_payload["keys"], dtype=np.uint32)
        numpy_rng = (
            numpy_payload["algorithm"],
            numpy_keys,
            int(numpy_payload["position"]),
            int(numpy_payload["has_gauss"]),
            float(numpy_payload["cached_gaussian"]),
        )
        np.random.RandomState().set_state(numpy_rng)
        if (not isinstance(torch_rng, torch.Tensor) or torch_rng.dtype != torch.uint8
                or torch_rng.ndim != 1):
            raise ValueError("Torch RNG state must be a one-dimensional uint8 tensor")
        torch.Generator(device="cpu").set_state(torch_rng)
        if not isinstance(cuda_rng, list):
            raise ValueError("CUDA RNG state must be a list of uint8 tensors")
        if any(not isinstance(rng, torch.Tensor) or rng.dtype != torch.uint8 or rng.ndim != 1
               for rng in cuda_rng):
            raise ValueError("CUDA RNG states must be one-dimensional uint8 tensors")
        if torch.cuda.is_available():
            if len(cuda_rng) != torch.cuda.device_count():
                raise ValueError("Checkpoint CUDA RNG state does not match the available device count")
            for index, rng in enumerate(cuda_rng):
                torch.Generator(device=f"cuda:{index}").set_state(rng)
        elif cuda_rng:
            raise ValueError("Cannot restore CUDA RNG state without CUDA")
    except (KeyError, TypeError, ValueError, OverflowError, RuntimeError) as error:
        raise ValueError("Checkpoint RNG state is missing, malformed, or unsupported") from error
    return python_rng, numpy_rng, torch_rng, cuda_rng


def configure_batchnorm_mode(model: nn.Module, training: bool, policy: str) -> None:
    model.train(training)
    if training and policy == "freeze_running_stats":
        for module in model.modules():
            if isinstance(module, nn.modules.batchnorm._BatchNorm):
                module.eval()


def training_class_weights(rows: list[dict[str, str]]) -> torch.Tensor:
    counts = torch.tensor([sum(r["split"] == "train" and r["class_name"] == name for r in rows)
                           for name in CLASS_NAMES], dtype=torch.float32)
    if (counts <= 0).any():
        raise ValueError("Class weights require approved training examples in all nine classes")
    weights = counts.reciprocal()
    return weights / weights.mean()


def focal_loss(logits: torch.Tensor, targets: torch.Tensor, *, alpha: float = 0.25,
               gamma: float = 2.0, class_weights: torch.Tensor | None = None) -> torch.Tensor:
    if logits.ndim != 2 or logits.shape[1] != 9 or logits.shape[0] < 1:
        raise ValueError("Focal logits must have shape (batch, 9) with a nonempty batch")
    if targets.ndim != 1 or targets.shape[0] != logits.shape[0] or targets.dtype != torch.long:
        raise ValueError("Focal targets must be a torch.long vector matching the batch")
    if (targets.min() < 0).item() or (targets.max() >= 9).item():
        raise ValueError("Focal targets must contain class indices in [0, 8]")
    try:
        alpha_value = float(alpha)
        gamma_value = float(gamma)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(
            "Invalid focal hyperparameters: alpha must be positive and gamma nonnegative"
        ) from error
    if (
        not math.isfinite(alpha_value)
        or alpha_value <= 0
        or not math.isfinite(gamma_value)
        or gamma_value < 0
    ):
        raise ValueError("Invalid focal hyperparameters: alpha must be positive and gamma nonnegative")
    if not torch.isfinite(logits).all().item():
        raise FloatingPointError("Focal logits contain non-finite values")
    ce = F.cross_entropy(logits.float(), targets, reduction="none")
    loss = alpha_value * (1 - (-ce).exp()).pow(gamma_value) * ce
    if class_weights is not None:
        if (
            class_weights.shape != (9,)
            or not torch.isfinite(class_weights).all().item()
            or (class_weights < 0).any().item()
        ):
            raise ValueError("Class weights must be a finite nonnegative vector of length nine")
        loss = loss * class_weights.to(device=logits.device, dtype=loss.dtype)[targets]
    if not torch.isfinite(loss).all().item():
        raise FloatingPointError("Focal loss is non-finite")
    reduced_loss = loss.mean()
    if not torch.isfinite(reduced_loss).all().item():
        raise FloatingPointError("Reduced focal loss is non-finite")
    return reduced_loss


def build_model(config: dict, root: Path) -> tuple[nn.Module, dict[str, str]]:
    from models.egvan import build_nine_class_egvan

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
                    scaler=None, *, expected: dict[str, str] | None = None,
                    restore_rng: bool = True) -> dict:
    state = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(state, dict) or not isinstance(state.get("model_state"), dict):
        raise ValueError("Checkpoint must contain a model state mapping")
    if expected and any(state.get(key) != value for key, value in expected.items()):
        raise ValueError("Checkpoint configuration or cohort provenance mismatch")
    if optimizer is not None and not isinstance(state.get("optimizer_state"), dict):
        raise ValueError("Checkpoint is missing a supported optimizer state")
    if scheduler is not None and not isinstance(state.get("scheduler_state"), dict):
        raise ValueError("Checkpoint is missing a supported scheduler state")
    if scaler is not None and not isinstance(state.get("scaler_state"), dict):
        raise ValueError("Checkpoint is missing a supported gradient-scaler state")
    if not isinstance(restore_rng, bool):
        raise TypeError("restore_rng must be a boolean")
    rng_states = _validated_rng_states(state) if restore_rng else None
    model.load_state_dict(state["model_state"])
    if optimizer is not None:
        optimizer.load_state_dict(state["optimizer_state"])
    if scheduler is not None:
        scheduler.load_state_dict(state["scheduler_state"])
    if scaler is not None:
        scaler.load_state_dict(state["scaler_state"])
    if rng_states is not None:
        random.setstate(rng_states[0])
        np.random.set_state(rng_states[1])
        torch.set_rng_state(rng_states[2])
        if torch.cuda.is_available():
            torch.cuda.set_rng_state_all(rng_states[3])
    return state


def _nested_tensors(value):
    if isinstance(value, torch.Tensor):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _nested_tensors(nested)
    elif isinstance(value, (tuple, list)):
        for nested in value:
            yield from _nested_tensors(nested)


def _assert_finite_tensors(tensors, message: str) -> None:
    checks_by_device = {}
    for tensor in tensors:
        checks_by_device.setdefault(tensor.device, []).append(torch.isfinite(tensor).all())
    if any(not torch.stack(checks).all().item() for checks in checks_by_device.values()):
        raise FloatingPointError(message)


def run_epoch(model: nn.Module, loader: DataLoader, device: torch.device,
              config: dict, *, optimizer=None, scaler=None,
              class_weights=None, include_predictions: bool = False) -> dict:
    training = optimizer is not None
    # Keep affine BatchNorm parameters trainable; freeze only their running buffers.
    configure_batchnorm_mode(
        model, training, config.get("batchnorm_policy", "train_running_stats")
    )
    amp = bool(device.type == "cuda" and config["mixed_precision"] == "cuda_if_available")
    losses, probs, targets = [], [], []
    accumulation_steps = int(config.get("gradient_accumulation_steps", 1))
    accumulated_samples = 0
    optimizer_steps = 0
    scaler_skipped_steps = 0
    gradient_norms = []
    if training:
        optimizer.zero_grad(set_to_none=True)
    _assert_finite_tensors(
        (parameter for parameter in model.parameters()),
        "Model parameters contain non-finite values before the epoch",
    )
    for batch_index, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)
        with torch.set_grad_enabled(training):
            with torch.autocast(device_type=device.type, enabled=amp):
                logits = model(images)
                loss = focal_loss(logits, labels, alpha=float(config["focal_alpha"]),
                                  gamma=float(config["focal_gamma"]), class_weights=class_weights)
            if training:
                if not torch.isfinite(loss).all().item():
                    raise FloatingPointError("Training loss is non-finite")
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
                    parameters_with_grad = [
                        parameter for parameter in model.parameters()
                        if parameter.grad is not None
                    ]
                    if not parameters_with_grad:
                        raise FloatingPointError("Training update produced no gradients")
                    _assert_finite_tensors(
                        (parameter.grad for parameter in parameters_with_grad),
                        "Training gradients contain non-finite values",
                    )
                    for parameter in model.parameters():
                        if parameter.grad is not None:
                            parameter.grad.div_(accumulated_samples)
                    clip = config.get("gradient_clip_norm")
                    if clip is None:
                        max_norm = math.inf
                    else:
                        max_norm = float(clip)
                        if not math.isfinite(max_norm) or max_norm <= 0:
                            raise ValueError("gradient_clip_norm must be finite and positive")
                    gradient_norm = torch.nn.utils.clip_grad_norm_(
                        parameters_with_grad, max_norm, error_if_nonfinite=False
                    )
                    if not torch.isfinite(gradient_norm).item():
                        raise FloatingPointError("Gradient norm is non-finite")
                    gradient_norms.append(float(gradient_norm.detach().cpu()))
                    _assert_finite_tensors(
                        (parameter for parameter in model.parameters()),
                        "Model parameters contain non-finite values before optimizer step",
                    )
                    _assert_finite_tensors(
                        _nested_tensors(optimizer.state),
                        "Optimizer state contains non-finite values before optimizer step",
                    )
                    if scaler is not None and amp:
                        scale_before = float(scaler.get_scale())
                        scaler.step(optimizer)
                        scaler.update()
                        if float(scaler.get_scale()) < scale_before:
                            scaler_skipped_steps += 1
                        else:
                            _assert_finite_tensors(
                                (parameter for parameter in model.parameters()),
                                "Model parameters contain non-finite values after optimizer step",
                            )
                            _assert_finite_tensors(
                                _nested_tensors(optimizer.state),
                                "Optimizer state contains non-finite values after optimizer step",
                            )
                            optimizer_steps += 1
                    else:
                        optimizer.step()
                        _assert_finite_tensors(
                            (parameter for parameter in model.parameters()),
                            "Model parameters contain non-finite values after optimizer step",
                        )
                        _assert_finite_tensors(
                            _nested_tensors(optimizer.state),
                            "Optimizer state contains non-finite values after optimizer step",
                        )
                        optimizer_steps += 1
                    optimizer.zero_grad(set_to_none=True)
                    accumulated_samples = 0
        losses.append((float(loss.detach()), len(labels)))
        probs.append(torch.softmax(logits.detach().float(), dim=1).cpu().numpy())
        targets.extend(labels.cpu().tolist())
    report = summarize_predictions(np.concatenate(probs), np.array(targets),
                                   split="train" if training else "validation")
    report["loss"] = sum(loss * count for loss, count in losses) / sum(count for _, count in losses)
    report["optimizer_steps"] = optimizer_steps
    report["scaler_skipped_steps"] = scaler_skipped_steps
    report["max_gradient_norm"] = max(gradient_norms) if gradient_norms else None
    if include_predictions:
        report["probabilities"] = np.concatenate(probs)
        report["targets"] = np.asarray(targets, dtype=np.int64)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--approved-split", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    rows, provenance = validate_approved_split(args.root, args.approved_split, args.approval, args.inventory)
    expected_protocol = "four_way_v1" if config["schema_version"] == "nine_class_training_v2" else "three_way_v1"
    if provenance["split_protocol"] != expected_protocol:
        raise ValueError("Training config and approved split protocol mismatch")
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
        state = load_checkpoint(checkpoint, model, optimizer, scheduler, scaler,
                                expected=expected, restore_rng=True)
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
                 "bad_epochs": bad_epochs, **capture_rng_state(),
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
