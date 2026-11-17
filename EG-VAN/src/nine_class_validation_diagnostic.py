"""Validation-only diagnostics for one frozen exploratory EG-VAN run.

This module never trains, calibrates, selects thresholds, or evaluates other
partitions. All generated files go to a new directory outside the training run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
from torch.utils.data import DataLoader

from nine_class_dataset import NineClassDataset, preprocessing_for_training, preprocessing_hash
from nine_class_evaluation import predict
from nine_class_metrics import summarize_predictions
from nine_class_stage4 import CLASS_NAMES, ROOT, VALIDATION_DIAGNOSTICS_ROOT
from nine_class_training import build_model, load_config

RESEARCH_STATUS = "EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION"
RUN_NAME = "EXPLORATORY_ONLY_20261108T193315Z_d50a9c07"
RUN_DIR = ROOT / "analysis/nine_class_exploratory/runs" / RUN_NAME
CHECKPOINT = RUN_DIR / "best.pt"
RUN_PROVENANCE = RUN_DIR / "run_provenance.json"
CONFIG = ROOT / "config/nine_class_training_t4_four_way_v2.json"
SPLIT = ROOT / "analysis/nine_class_exploratory/exploratory_split.csv"
SOURCE_PREVIEW = ROOT / "analysis/nine_class_final_cohort/four_way_planning_assignment_v1.csv"
OUTPUT_ROOT = VALIDATION_DIAGNOSTICS_ROOT

EXPECTED_CHECKPOINT_SHA256 = "3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08"
EXPECTED_CONFIG_SHA256 = "916508faaac87b4268ac0cf8aa45c682d4b03079e71322386823a83adc49755d"
EXPECTED_SPLIT_SHA256 = "d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740"
EXPECTED_PREPROCESS_SHA256 = "93ea2577432511fd047f3d5a855d498aaabe63e6ff69094b5b758c16f85a3c68"
EXPECTED_SOURCE_PREVIEW_SHA256 = "b2658168a620a857bf366bf1fafb2a7a5c7e7e5808dd600de36b6e29f0f97279"
EXPECTED_LABEL_ORDER = (
    "AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_inputs() -> tuple[dict, dict, object]:
    if RUN_DIR.name != RUN_NAME or not RUN_DIR.is_dir():
        raise FileNotFoundError(f"Recovered run directory not found: {RUN_DIR}")
    if CHECKPOINT.parent.resolve() != RUN_DIR.resolve() or CHECKPOINT.name != "best.pt":
        raise ValueError("Only this recovered run's best.pt may be evaluated")
    if not RUN_PROVENANCE.is_file():
        raise FileNotFoundError(f"Missing run provenance: {RUN_PROVENANCE}")

    provenance = json.loads(RUN_PROVENANCE.read_text(encoding="utf-8"))
    config_sha = sha256_file(CONFIG)
    split_sha = sha256_file(SPLIT)
    source_preview_sha = sha256_file(SOURCE_PREVIEW)
    if config_sha != EXPECTED_CONFIG_SHA256:
        raise ValueError("Training config SHA-256 differs from the recovered run")
    if split_sha != EXPECTED_SPLIT_SHA256:
        raise ValueError("Exploratory split SHA-256 differs from the recovered run")
    if source_preview_sha != EXPECTED_SOURCE_PREVIEW_SHA256:
        raise ValueError("Source preview SHA-256 differs from the recovered run")

    config = load_config(CONFIG)
    if tuple(config["label_order"]) != EXPECTED_LABEL_ORDER or tuple(CLASS_NAMES) != EXPECTED_LABEL_ORDER:
        raise ValueError("Training config or model label order differs from the recovered run")
    if config["image_size"] != 384 or config["preprocessing_mode"] != "raw_resize_imagenet_v2":
        raise ValueError("Training image size or preprocessing mode differs from the recovered run")
    preprocess = preprocessing_for_training(config)
    preprocess_sha = preprocessing_hash(preprocess)
    if preprocess_sha != EXPECTED_PREPROCESS_SHA256:
        raise ValueError("Resolved preprocessing fingerprint differs from the recovered run")

    expected_provenance = {
        "research_status": RESEARCH_STATUS,
        "config_sha256": config_sha,
        "split_sha256": split_sha,
        "preprocess_config_sha256": preprocess_sha,
        "source_preview_sha256": source_preview_sha,
        "config": config,
    }
    if any(provenance.get(key) != value for key, value in expected_provenance.items()):
        raise ValueError("Run provenance does not match the frozen config and data manifests")

    checkpoint_sha = sha256_file(CHECKPOINT)
    if checkpoint_sha != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Recovered best.pt SHA-256 does not match the supplied checkpoint identity")
    return config, provenance, preprocess


def load_verified_state(*, trust_project_owned_checkpoint: bool) -> dict:
    """Prefer safe tensor-only deserialization; permit pickle only by explicit trust."""
    try:
        state = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    except pickle.UnpicklingError as error:
        if not trust_project_owned_checkpoint:
            raise RuntimeError(
                "weights_only=True rejected this checkpoint. Confirm it is the trusted "
                "project-owned best.pt and rerun with --trust-project-owned-checkpoint "
                "before allowing pickle deserialization."
            ) from error
        state = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
    except TypeError as error:
        if "weights_only" not in str(error):
            raise
        if not trust_project_owned_checkpoint:
            raise RuntimeError(
                "This PyTorch does not support weights_only=True. Use a compatible "
                "runtime, or confirm the trusted project-owned checkpoint and rerun "
                "with --trust-project-owned-checkpoint."
            ) from error
        state = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)

    if not isinstance(state, dict):
        raise ValueError("Checkpoint is not a state dictionary")
    required_keys = {
        "research_status", "config_sha256", "split_sha256", "preprocess_config_sha256",
        "epoch", "model_state", "optimizer_state", "scheduler_state", "scaler_state",
        "best_validation_loss", "train_metrics", "validation_metrics",
    }
    if not required_keys.issubset(state):
        raise ValueError("Checkpoint is missing expected exploratory training fields")
    return state


def create_output_directory() -> Path:
    run_resolved = RUN_DIR.resolve()
    output_root = OUTPUT_ROOT.resolve()
    if output_root == run_resolved or run_resolved in output_root.parents:
        raise ValueError("Diagnostic outputs must be outside the original training run")
    output_root.mkdir(parents=True, exist_ok=True)
    output_dir = output_root / (
        "EXPLORATORY_ONLY_VALIDATION_" +
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    )
    output_dir.mkdir(exist_ok=False)
    return output_dir


def write_json_exclusive(path: Path, content: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(content, handle, indent=2)
        handle.write("\n")


def write_outputs(output_dir: Path, dataset: NineClassDataset,
                  probabilities: np.ndarray, targets: np.ndarray,
                  checkpoint_sha: str, provenance: dict) -> dict:
    predicted = probabilities.argmax(axis=1)
    report = summarize_predictions(probabilities, targets, split="validation")
    if not report["all_nine_classes_present"]:
        raise ValueError("Validation partition does not contain all nine classes")
    if report["n_samples"] != len(dataset) or int(np.asarray(report["confusion_matrix"]).sum()) != len(dataset):
        raise ValueError("Validation metrics do not cover the complete validation dataset")

    report["balanced_accuracy"] = float(np.mean([
        report["per_class"][name]["recall"] for name in EXPECTED_LABEL_ORDER
    ]))
    report["label_order"] = list(EXPECTED_LABEL_ORDER)
    report["research_status"] = RESEARCH_STATUS
    report["evaluation_scope"] = "validation_only"
    report["checkpoint_sha256"] = checkpoint_sha
    report["split_sha256"] = provenance["split_sha256"]
    report["config_sha256"] = provenance["config_sha256"]
    report["preprocess_config_sha256"] = provenance["preprocess_config_sha256"]

    write_json_exclusive(output_dir / "validation_metrics.json", report)
    with (output_dir / "validation_confusion_matrix.csv").open(
        "x", newline="", encoding="utf-8"
    ) as handle:
        fields = ["true_class"] + [f"predicted_{name}" for name in EXPECTED_LABEL_ORDER]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, name in enumerate(EXPECTED_LABEL_ORDER):
            writer.writerow({
                "true_class": name,
                **{f"predicted_{pred_name}": int(report["confusion_matrix"][index][column])
                   for column, pred_name in enumerate(EXPECTED_LABEL_ORDER)},
            })

    with (output_dir / "validation_predictions.csv").open(
        "x", newline="", encoding="utf-8"
    ) as handle:
        fields = ["research_status", "image_path", "source_dataset", "true_class", "predicted_class"]
        fields.extend(f"prob_{name}" for name in EXPECTED_LABEL_ORDER)
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(dataset.rows):
            writer.writerow({
                "research_status": RESEARCH_STATUS,
                "image_path": row["image_path"],
                "source_dataset": row.get("source_dataset", ""),
                "true_class": EXPECTED_LABEL_ORDER[int(targets[index])],
                "predicted_class": EXPECTED_LABEL_ORDER[int(predicted[index])],
                **{f"prob_{name}": float(probabilities[index, class_index])
                   for class_index, name in enumerate(EXPECTED_LABEL_ORDER)},
            })
    return report


def evaluate(*, trust_project_owned_checkpoint: bool) -> Path:
    config, provenance, preprocess = verify_inputs()
    state = load_verified_state(
        trust_project_owned_checkpoint=trust_project_owned_checkpoint
    )
    checkpoint_provenance = {
        "research_status": RESEARCH_STATUS,
        "config_sha256": provenance["config_sha256"],
        "split_sha256": provenance["split_sha256"],
        "preprocess_config_sha256": provenance["preprocess_config_sha256"],
    }
    if any(state.get(key) != value for key, value in checkpoint_provenance.items()):
        raise ValueError("Checkpoint provenance does not match the recovered run")

    model, _ = build_model(config, ROOT)
    model.load_state_dict(state["model_state"], strict=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    validation_dataset = NineClassDataset(ROOT, SPLIT, "validation", preprocess)
    validation_loader = DataLoader(
        validation_dataset, batch_size=int(config["batch_size"]),
        shuffle=False, num_workers=int(config["num_workers"])
    )
    probabilities, targets = predict(model, validation_loader, device)
    output_dir = create_output_directory()
    checkpoint_sha = sha256_file(CHECKPOINT)
    write_outputs(output_dir, validation_dataset, probabilities, targets,
                  checkpoint_sha, provenance)
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trust-project-owned-checkpoint", action="store_true",
        help="Permit pickle loading only after weights_only=True fails and the checkpoint is trusted.",
    )
    args = parser.parse_args()
    output_dir = evaluate(
        trust_project_owned_checkpoint=args.trust_project_owned_checkpoint
    )
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
