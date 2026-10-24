"""Read-only Colab preflight around the existing gated Stage 6 training runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from nine_class_dataset import preprocessing_for_training, preprocessing_hash
from nine_class_protocol import validate_approved_split
from nine_class_stage4 import CLASS_NAMES
from nine_class_training import load_config

PARAMETERS = 58_087_667


def validate_colab_config(path: Path) -> dict:
    config = load_config(path)
    if tuple(config["label_order"]) != CLASS_NAMES or config["image_size"] != 384:
        raise ValueError("Nine-class label or input shape differs")
    micro = int(config["batch_size"])
    steps = int(config.get("gradient_accumulation_steps", 1))
    return {"config": config, "microbatch_size": micro, "accumulation_steps": steps,
            "nominal_effective_batch_size": micro * steps,
            "preprocess_config_sha256": preprocessing_hash(preprocessing_for_training(config))}


def gpu_memory_plan(total_bytes: int, free_bytes: int, config: dict) -> dict:
    if total_bytes <= 0 or free_bytes <= 0 or free_bytes > total_bytes:
        raise ValueError("Invalid CUDA memory report")
    parameter_mib = PARAMETERS * 4 / 2**20
    # Adamax stores one first-moment and one infinity-norm buffer per parameter.
    persistent_mib = 4 * parameter_mib  # weights + gradients + 2 optimizer buffers
    return {"total_gib": round(total_bytes / 2**30, 2), "free_gib": round(free_bytes / 2**30, 2),
            "float32_parameters_mib": round(parameter_mib, 1),
            "weights_gradients_adamax_estimate_mib": round(persistent_mib, 1),
            "activation_peak_measured": False,
            "microbatch_size": int(config["batch_size"]),
            "nominal_effective_batch_size": int(config["batch_size"]) * int(config.get("gradient_accumulation_steps", 1)),
            "caution": "Activation, batch-norm, allocator and mixed-precision memory are not measured; run a batch-one smoke pass before training"}


def validate_cohort(root: Path, split: Path, approval: Path, inventory: Path) -> dict:
    rows, provenance = validate_approved_split(root, split, approval, inventory)
    if not provenance["approval"].get("test_partition_frozen") or not provenance["test_has_all_classes"]:
        raise ValueError("Full training requires a frozen protected test containing all nine labels")
    return {"rows": rows, "provenance": provenance}


def validate_resume(checkpoint: Path, runs_root: Path) -> Path:
    checkpoint, runs_root = checkpoint.resolve(), runs_root.resolve()
    if (checkpoint.name != "last.pt" or not checkpoint.is_relative_to(runs_root)
        or not checkpoint.is_file() or not (checkpoint.parent / "run_provenance.json").is_file()):
        raise ValueError("Resume requires a persistent last.pt and adjacent run_provenance.json")
    return checkpoint


def training_command(root: Path, config: Path, split: Path, approval: Path,
                     inventory: Path, runs_root: Path, *, resume: Path | None = None,
                     validate_only: bool = False) -> list[str]:
    command = [sys.executable, str(root / "src/nine_class_training.py"),
               "--root", str(root), "--config", str(config),
               "--approved-split", str(split), "--approval", str(approval),
               "--inventory", str(inventory), "--runs-root", str(runs_root)]
    if resume is not None:
        command += ["--resume", str(validate_resume(resume, runs_root))]
    if validate_only:
        command.append("--validate-only")
    return command


def evaluation_command(root: Path, split: Path, approval: Path, inventory: Path,
                       checkpoint: Path, output: Path, *, final_test: bool = False) -> list[str]:
    command = [sys.executable, str(root / "src/nine_class_evaluation.py"),
               "--root", str(root), "--approved-split", str(split),
               "--approval", str(approval), "--inventory", str(inventory),
               "--checkpoint", str(checkpoint), "--split", "test" if final_test else "validation",
               "--output-dir", str(output)]
    if final_test:
        command.append("--final-test")
    return command
