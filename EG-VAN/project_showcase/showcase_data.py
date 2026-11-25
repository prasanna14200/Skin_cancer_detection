from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLASS_NAMES = (
    "AKIEC",
    "BCC",
    "BKL",
    "DF",
    "MEL",
    "NV",
    "VASC",
    "BENIGN",
    "MALIGNANT",
)
EXPLORATORY_LABEL = "EXPLORATORY / NON-CLINICAL"


def project_path(relative_path: str) -> Path:
    path = (ROOT / relative_path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Evidence path must remain inside the project root")
    return path


def load_json(relative_path: str) -> dict[str, Any]:
    path = project_path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"Required evidence file is missing: {relative_path}")
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {relative_path}")
    return value


def relative_reference(path: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError("Evidence reference is outside the project root")
    return resolved.relative_to(ROOT).as_posix()


def get_validation_metrics() -> dict[str, Any]:
    metrics = load_json(
        "analysis/nine_class_validation_diagnostics/"
        "EXPLORATORY_ONLY_VALIDATION_20261112T154709Z_1dca162c/"
        "validation_metrics.json"
    )
    if metrics.get("label_order") != list(CLASS_NAMES):
        raise ValueError("Validation label order differs from the nine-class implementation")
    if metrics.get("research_status") != "EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION":
        raise ValueError("Validation evidence is missing its exploratory status")
    confusion = metrics.get("confusion_matrix")
    if not isinstance(confusion, list) or len(confusion) != len(CLASS_NAMES):
        raise ValueError("Validation confusion matrix has an unexpected shape")
    if any(not isinstance(row, list) or len(row) != len(CLASS_NAMES) for row in confusion):
        raise ValueError("Validation confusion matrix is not square")
    predicted_nv = sum(row[CLASS_NAMES.index("NV")] for row in confusion)
    correct = sum(confusion[index][index] for index in range(len(CLASS_NAMES)))
    n_samples = int(metrics["n_samples"])
    if sum(map(sum, confusion)) != n_samples:
        raise ValueError("Validation confusion matrix total differs from n_samples")
    return {
        "accuracy": float(metrics["accuracy"]),
        "macro_f1": float(metrics["macro_f1"]),
        "balanced_accuracy": float(metrics["balanced_accuracy"]),
        "n_samples": n_samples,
        "correct": correct,
        "incorrect": n_samples - correct,
        "predicted_nv": predicted_nv,
        "source": "analysis/nine_class_validation_diagnostics/"
        "EXPLORATORY_ONLY_VALIDATION_20261112T154709Z_1dca162c/"
        "validation_metrics.json",
        "weighted_f1": float(metrics["weighted_f1"]),
    }


def source_file_status(relative_path: str) -> bool:
    return project_path(relative_path).is_file()
