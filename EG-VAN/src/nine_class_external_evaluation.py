"""Frozen-checkpoint external evaluation; no fitting or test-time tuning."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from models.egvan import build_nine_class_egvan
from nine_class_dataset import PreprocessConfig, image_tensor, preprocessing_for_training, preprocessing_hash
from nine_class_external_protocol import external_path, validate_approved_external
from nine_class_iqa import measure_rgb
from nine_class_protocol import file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES, ROOT
from nine_class_stage8_analysis import quality_group_calibration
from nine_class_uncertainty import calibration_metrics, uncertainty_from_probabilities


class ExternalImageDataset(Dataset):
    def __init__(self, root: Path, rows: list[dict[str, str]], config: PreprocessConfig):
        self.root, self.rows, self.config = root, rows, config

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        return image_tensor(external_path(self.root, self.rows[index]), self.config, train=False), index


def external_metrics(probabilities: np.ndarray, targets: np.ndarray,
                     supported_classes: list[str]) -> dict:
    """Subset-conditioned metrics retain all nine model output columns."""
    values = np.asarray(probabilities, dtype=float)
    y = np.asarray(targets, dtype=np.int64)
    if values.ndim != 2 or values.shape[1] != 9 or len(values) != len(y) or not len(y):
        raise ValueError("External predictions need nonempty nine-class probabilities and labels")
    if not np.isfinite(values).all() or (values < 0).any() or not np.allclose(values.sum(axis=1), 1, atol=1e-5):
        raise ValueError("Invalid external probabilities")
    supported = [CLASS_NAMES.index(name) for name in supported_classes]
    if not supported or len(set(supported)) != len(supported) or any(target not in supported for target in y):
        raise ValueError("External targets outside explicitly supported classes")
    predicted = values.argmax(axis=1)
    matrix = np.zeros((9, 9), dtype=np.int64)
    np.add.at(matrix, (y, predicted), 1)
    support = matrix.sum(axis=1)
    per_class = {}
    f1s, weights = [], []
    for index, name in enumerate(CLASS_NAMES):
        tp = int(matrix[index, index])
        count = int(support[index])
        called = int(matrix[:, index].sum())
        precision = tp / called if called else 0.0
        recall = tp / count if count else None
        f1 = 2 * precision * recall / (precision + recall) if count and precision + recall else 0.0 if count else None
        per_class[name] = {"support": count, "precision": precision if count else None,
                           "recall": recall, "f1": f1}
        if index in supported:
            f1s.append(float(f1 or 0))
            weights.append(count)
    full = len(supported) == 9 and all(support > 0)
    observed = float(np.mean(predicted == y))
    warnings = []
    if not full:
        warnings.append("Subset-specific external evaluation; no full nine-class accuracy")
    low = [name for name in supported_classes if per_class[name]["support"] < 5]
    if low:
        warnings.append("Low class support (<5): " + ", ".join(low))
    calibration = calibration_metrics(values, y) if len(y) >= 100 else None
    if calibration is None:
        warnings.append("Calibration metrics withheld: fewer than 100 labeled cases")
    return {"scope": "full_nine_class" if full else "supported_label_subset",
            "supported_classes": supported_classes, "missing_classes": [n for n in CLASS_NAMES if n not in supported_classes],
            "n_samples": len(y), "full_nine_accuracy": observed if full else None,
            "subset_accuracy": None if full else observed,
            "macro_f1_supported": float(np.mean(f1s)),
            "weighted_f1_supported": float(np.average(f1s, weights=weights)),
            "per_class": per_class, "confusion_matrix_all_nine_outputs": matrix.tolist(),
            "mean_confidence": float(values.max(axis=1).mean()),
            "mean_normalized_entropy": float(uncertainty_from_probabilities(values)["normalized_entropy"].mean()),
            "calibration": calibration, "warnings": warnings}


def compare_internal_external(internal: dict, external: dict) -> dict:
    """Compare only compatible populations and exactly matching metric definitions."""
    issues = []
    for key in ("scope", "supported_classes", "preprocess_config_sha256"):
        if internal.get(key) != external.get(key) or internal.get(key) is None:
            issues.append(f"{key} differs or is undocumented")
    if internal.get("scope") != "full_nine_class":
        issues.append("A subset requires an independently defined matching internal subset report")
    if issues:
        return {"comparable": False, "reasons": issues,
                "internal_source": internal.get("source_dataset"),
                "external_source": external.get("source_dataset")}
    metrics = ("accuracy", "macro_f1", "ece", "mean_confidence", "mean_iqa_brightness")
    changes = {name: (external[name] - internal[name] if isinstance(external.get(name), (int, float))
                      and isinstance(internal.get(name), (int, float)) else None)
               for name in metrics}
    recalls = {name: (external["per_class_recall"][name] - internal["per_class_recall"][name]
                      if external.get("per_class_recall", {}).get(name) is not None
                      and internal.get("per_class_recall", {}).get(name) is not None else None)
               for name in CLASS_NAMES}
    return {"comparable": True, "metric_changes_external_minus_internal": changes,
            "per_class_recall_changes": recalls,
            "internal_source": internal.get("source_dataset"),
            "external_source": external.get("source_dataset"),
            "interpretation": "Descriptive difference, not a causal or deployment-readiness conclusion"}


def compare_evaluation_reports(internal_metrics: dict, external_report: dict,
                               internal_run_info: dict, *,
                               internal_stage8: dict | None = None,
                               internal_iqa_brightness: float | None = None,
                               mapping_comparability_reference: str | None = None) -> dict:
    """Normalize actual Stage 6/8 and Stage 9 report schemas before comparison."""
    config = internal_run_info.get("config", {})
    if (tuple(config.get("label_order", ())) != CLASS_NAMES or config.get("image_size") != 384
        or internal_run_info.get("config_sha256") != internal_metrics.get("provenance", {}).get("config_sha256")):
        raise ValueError("Internal run configuration or label order is incompatible")
    internal_preprocess = preprocessing_for_training(config)
    if internal_run_info.get("preprocess_config_sha256") != preprocessing_hash(internal_preprocess):
        raise ValueError("Internal run lacks a matching frozen preprocessing configuration")
    if internal_metrics.get("split") != "test" or not internal_metrics.get("all_nine_classes_present"):
        raise ValueError("A frozen full-nine internal test report is required")
    if internal_metrics["provenance"].get("checkpoint_sha256") != external_report.get("provenance", {}).get("checkpoint_sha256"):
        raise ValueError("Internal and external reports use different checkpoints")
    if (external_report.get("mapping_status_counts", {}).get("CLINICALLY_JUSTIFIED_NONIDENTICAL", 0)
        and not mapping_comparability_reference):
        return {"comparable": False,
                "reasons": ["Non-identical external label mapping lacks a comparison-specific justification"],
                "external_source": external_report.get("source_dataset_versions")}
    preprocess_sha = preprocessing_hash(internal_preprocess)
    internal = {"scope": "full_nine_class", "supported_classes": list(CLASS_NAMES),
                "preprocess_config_sha256": preprocess_sha,
                "source_dataset": "approved_internal_cohort",
                "accuracy": internal_metrics["accuracy"], "macro_f1": internal_metrics["macro_f1"],
                "per_class_recall": {name: internal_metrics["per_class"][name]["recall"]
                                     for name in CLASS_NAMES},
                "ece": (internal_stage8 or {}).get("uncalibrated_calibration", {}).get("ece"),
                "mean_confidence": (internal_stage8 or {}).get("mean_confidence"),
                "mean_iqa_brightness": internal_iqa_brightness}
    external = {"scope": external_report.get("scope"),
                "supported_classes": external_report.get("supported_classes"),
                "preprocess_config_sha256": external_report.get("preprocess_config_sha256"),
                "source_dataset": external_report.get("source_dataset_versions"),
                "accuracy": external_report.get("full_nine_accuracy"),
                "macro_f1": external_report.get("macro_f1_supported"),
                "per_class_recall": {name: external_report.get("per_class", {}).get(name, {}).get("recall")
                                     for name in CLASS_NAMES},
                "ece": (external_report.get("calibration") or {}).get("ece"),
                "mean_confidence": external_report.get("mean_confidence"),
                "mean_iqa_brightness": external_report.get("mean_iqa_brightness")}
    result = compare_internal_external(internal, external)
    result["mapping_comparability_reference"] = mapping_comparability_reference
    return result


def evaluate_external(internal_root: Path, internal_split: Path, internal_approval: Path,
                      internal_inventory: Path, external_root: Path, external_manifest: Path,
                      external_approval: Path, overlap_report: Path, checkpoint: Path,
                      output_dir: Path, *, batch_size: int = 8,
                      model_factory: Callable[[dict], nn.Module] | None = None,
                      allow_synthetic_fixture: bool = False) -> dict:
    if output_dir.exists():
        raise FileExistsError(output_dir)
    if batch_size < 1:
        raise ValueError("Positive batch size required")
    _, internal_provenance = validate_approved_split(internal_root, internal_split,
                                                     internal_approval, internal_inventory,
                                                     allow_synthetic_fixture=allow_synthetic_fixture)
    checkpoint = checkpoint.resolve()
    run_info_path = checkpoint.parent / "run_provenance.json"
    if not checkpoint.is_file() or not run_info_path.is_file():
        raise FileNotFoundError("Frozen checkpoint or run provenance missing")
    run_info = json.loads(run_info_path.read_text(encoding="utf-8"))
    config = run_info.get("config", {})
    if tuple(config.get("label_order", ())) != CLASS_NAMES or config.get("image_size") != 384:
        raise ValueError("Checkpoint label order or input size differs from nine-class contract")
    for key in ("split_sha256", "inventory_sha256", "approval_sha256"):
        if run_info.get(key) != internal_provenance[key]:
            raise ValueError("Frozen checkpoint run provenance differs from approved internal cohort")
    preprocess = preprocessing_for_training(config)
    preprocess_sha = preprocessing_hash(preprocess)
    if run_info.get("preprocess_config_sha256") != preprocess_sha:
        raise ValueError("Checkpoint run preprocessing configuration is missing or incompatible")
    checkpoint_sha = file_sha256(checkpoint)
    rows, external_provenance = validate_approved_external(
        external_root, external_manifest, external_approval, overlap_report,
        internal_inventory, checkpoint_sha, preprocess_sha,
        allow_synthetic_fixture=allow_synthetic_fixture)
    # Hash-bind the trusted local checkpoint before invoking pickle deserialization.
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    expected = {"config_sha256": run_info["config_sha256"],
                "split_sha256": internal_provenance["split_sha256"],
                "inventory_sha256": internal_provenance["inventory_sha256"],
                "approval_sha256": internal_provenance["approval_sha256"],
                "preprocess_config_sha256": preprocess_sha}
    if any(state.get(key) != value for key, value in expected.items()) or "model_state" not in state:
        raise ValueError("Checkpoint weights or cohort provenance mismatch")
    model = (model_factory(config) if model_factory else
             build_nine_class_egvan(fusion_channels=int(config["fusion_channels"])))
    model.load_state_dict(state["model_state"], strict=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()
    dataset = ExternalImageDataset(external_root, rows, preprocess)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    probabilities = np.empty((len(rows), 9), dtype=np.float64)
    with torch.inference_mode():
        for images, indices in loader:
            logits = model(images.to(device))
            if logits.shape != (len(indices), 9) or not torch.isfinite(logits).all():
                raise ValueError("Frozen model did not emit finite nine logits")
            probabilities[indices.numpy()] = torch.softmax(logits.float(), dim=1).cpu().numpy()
    targets = np.array([CLASS_NAMES.index(row["target_label"]) for row in rows], dtype=np.int64)
    metrics = external_metrics(probabilities, targets, external_provenance["supported_classes"])
    uncertainty = uncertainty_from_probabilities(probabilities, targets)
    output_rows, quality_rows = [], []
    for index, row in enumerate(rows):
        path = external_path(external_root, row)
        if file_sha256(path) != row["sha256"]:
            raise ValueError("External raw image changed during evaluation")
        bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("External raw image cannot be decoded for IQA")
        features, flags = measure_rgb(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        key = f'{row["source_dataset"]}:{row["source_version"]}:{row["image_path"]}'
        output_rows.append({"source_image_key": key, "source_dataset": row["source_dataset"],
                            "source_version": row["source_version"], "image_path": row["image_path"],
                            "source_image_id": row["source_image_id"], "source_image_sha256": row["sha256"],
                            "target_label": row["target_label"], "target_index": int(targets[index]),
                            "predicted_index": int(uncertainty["predicted_index"][index]),
                            "confidence": float(uncertainty["confidence"][index]),
                            "predictive_entropy": float(uncertainty["predictive_entropy"][index]),
                            "normalized_entropy": float(uncertainty["normalized_entropy"][index]),
                            "top_two_margin": float(uncertainty["top_two_margin"][index]),
                            "iqa_invalid_flags": "|".join(flags),
                            **{f"prob_{name}": float(probabilities[index, j]) for j, name in enumerate(CLASS_NAMES)},
                            **features})
        quality_rows.append({"source_dataset": row["source_dataset"],
                             "image_path": row["image_path"], **features})
    quality_summary = quality_group_calibration(quality_rows, probabilities, targets)
    metrics["mean_iqa_brightness"] = float(np.mean([r["brightness_mean"] for r in quality_rows]))
    output_dir.mkdir(parents=True, exist_ok=False)
    for filename, values in (("external_predictions.csv", output_rows),
                             ("quality_group_calibration.csv", quality_summary)):
        with (output_dir / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(values[0]))
            writer.writeheader()
            writer.writerows(values)
    report = {**metrics, "status": "EXTERNAL_EVALUATION_REQUIRES_SCIENTIFIC_INTERPRETATION",
              "label_order": CLASS_NAMES, "source_dataset_versions": sorted({
                  (r["source_dataset"], r["source_version"]) for r in rows}),
              "mapping_status_counts": {status: sum(r["mapping_status"] == status for r in rows)
                                        for status in ("EXACT", "CLINICALLY_JUSTIFIED_NONIDENTICAL")},
              "preprocess_config_sha256": preprocess_sha, "preprocess_config": asdict(preprocess),
              "iqa_view": "raw", "iqa_quality_group_rows": len(quality_summary),
              "provenance": {**external_provenance, "checkpoint_sha256": checkpoint_sha,
                             "checkpoint_epoch": state.get("epoch"),
                             "internal_split_sha256": internal_provenance["split_sha256"],
                             "run_provenance_sha256": file_sha256(run_info_path)}}
    (output_dir / "external_metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--internal-root", type=Path, default=ROOT)
    parser.add_argument("--internal-split", type=Path, required=True)
    parser.add_argument("--internal-approval", type=Path, required=True)
    parser.add_argument("--internal-inventory", type=Path, required=True)
    parser.add_argument("--external-root", type=Path, required=True)
    parser.add_argument("--external-manifest", type=Path, required=True)
    parser.add_argument("--external-approval", type=Path, required=True)
    parser.add_argument("--overlap-report", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    report = evaluate_external(args.internal_root, args.internal_split, args.internal_approval,
                               args.internal_inventory, args.external_root, args.external_manifest,
                               args.external_approval, args.overlap_report, args.checkpoint,
                               args.output_dir, batch_size=args.batch_size)
    print(json.dumps({"scope": report["scope"], "supported_classes": report["supported_classes"],
                      "n_samples": report["n_samples"], "output_dir": str(args.output_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
