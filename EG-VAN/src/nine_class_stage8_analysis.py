"""Gated nine-class uncertainty analysis and synthetic-only plotting demo."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nine_class_iqa_performance import join_quality_predictions, read_csv, validate_evaluation_artifact
from nine_class_protocol import file_sha256
from nine_class_stage4 import CLASS_NAMES, ROOT
from nine_class_uncertainty import (SCHEMA_VERSION, apply_temperature_to_probabilities,
                                    calibration_metrics, risk_coverage_curve,
                                    select_threshold_on_validation,
                                    selective_at_threshold, uncertainty_from_probabilities,
                                    validate_probabilities)


def render_plots(probabilities: np.ndarray, targets: np.ndarray, output_dir: Path,
                 *, title_prefix: str) -> list[str]:
    values = validate_probabilities(probabilities)
    y = np.asarray(targets, dtype=np.int64)
    uncertainty = uncertainty_from_probabilities(values, y)
    calibration = calibration_metrics(values, y)
    outputs = []
    for feature, label, name in ((uncertainty["confidence"], "Maximum class probability", "confidence_histogram.png"),
                                 (uncertainty["normalized_entropy"], "Normalized entropy", "entropy_distribution.png")):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(feature, bins=np.linspace(0, 1, 11), edgecolor="black")
        ax.set(xlabel=label, ylabel="Images", title=f"{title_prefix}: {label}")
        fig.tight_layout()
        fig.savefig(output_dir / name, dpi=140)
        plt.close(fig)
        outputs.append(name)
    bins = [r for r in calibration["reliability_bins"] if r["count"]]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Ideal")
    ax.scatter([r["mean_confidence"] for r in bins], [r["accuracy"] for r in bins],
               s=[max(25, r["count"] * 8) for r in bins], label="Occupied bins")
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Mean confidence", ylabel="Observed accuracy",
           title=f"{title_prefix}: reliability (ECE={calibration['ece']:.3f})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "reliability_diagram.png", dpi=140)
    plt.close(fig)
    outputs.append("reliability_diagram.png")
    curve = risk_coverage_curve(values, y)[1:]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([r["coverage"] for r in curve], [r["selective_error_risk"] for r in curve])
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Coverage", ylabel="Selective error risk",
           title=f"{title_prefix}: risk–coverage")
    fig.tight_layout()
    fig.savefig(output_dir / "risk_coverage.png", dpi=140)
    plt.close(fig)
    outputs.append("risk_coverage.png")
    summaries = []
    for i, name in enumerate(CLASS_NAMES):
        selected = y == i
        summaries.append({"class_name": name, "support": int(selected.sum()),
                          "mean_normalized_entropy": float(uncertainty["normalized_entropy"][selected].mean())
                          if selected.any() else None})
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(CLASS_NAMES, [r["mean_normalized_entropy"] if r["mean_normalized_entropy"] is not None else 0 for r in summaries])
    ax.set(xlabel="Source-defined class", ylabel="Mean normalized entropy",
           title=f"{title_prefix}: per-class uncertainty")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(output_dir / "per_class_uncertainty.png", dpi=140)
    plt.close(fig)
    outputs.append("per_class_uncertainty.png")
    (output_dir / "per_class_uncertainty.json").write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    return outputs


def _prediction_matrix(predictions: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    probabilities = np.asarray([[float(row[f"prob_{name}"]) for name in CLASS_NAMES]
                                for row in predictions], dtype=np.float64)
    targets = np.asarray([int(row["target_index"]) for row in predictions], dtype=np.int64)
    return validate_probabilities(probabilities), targets


def quality_group_calibration(quality_rows: list[dict], probabilities: np.ndarray,
                              targets: np.ndarray, *, groups: int = 4) -> list[dict]:
    """Descriptive equal-count IQA ranks; small groups make ECE unstable."""
    if len(quality_rows) != len(probabilities) or groups < 2:
        raise ValueError("IQA rows must align with predictions and have at least two groups")
    features = ("sharpness_laplacian_variance", "brightness_mean", "contrast_std",
                "underexposed_fraction", "overexposed_fraction")
    records = []
    for feature in features:
        ordered = sorted(range(len(quality_rows)),
                         key=lambda i: (quality_rows[i][feature], quality_rows[i]["source_dataset"],
                                        quality_rows[i]["image_path"]))
        for rank in range(groups):
            indices = [i for position, i in enumerate(ordered)
                       if min(groups - 1, position * groups // len(ordered)) == rank]
            if not indices:
                continue
            result = calibration_metrics(probabilities[indices], targets[indices])
            records.append({"feature": feature, "quality_rank_quantile": rank + 1,
                            "n": len(indices), "feature_min": quality_rows[indices[0]][feature],
                            "feature_max": quality_rows[indices[-1]][feature],
                            "accuracy": result["accuracy"], "ece": result["ece"],
                            "multiclass_brier": result["multiclass_brier"],
                            "negative_log_likelihood": result["negative_log_likelihood"],
                            "small_group_warning": len(indices) < 20})
    return records


def run(root: Path, split_csv: Path, approval: Path, inventory: Path,
        evaluation_dir: Path, output_dir: Path, *, final_test: bool = False,
        iqa_csv: Path | None = None, iqa_view: str | None = None,
        temperature_record: Path | None = None, threshold_record: Path | None = None,
        choose_minimum_coverage: float | None = None) -> dict:
    if output_dir.exists():
        raise FileExistsError(output_dir)
    predictions, cohort = validate_evaluation_artifact(root, split_csv, approval, inventory,
                                                        evaluation_dir, final_test=final_test)
    probabilities, targets = _prediction_matrix(predictions)
    evaluation_metrics = json.loads((evaluation_dir / "metrics.json").read_text(encoding="utf-8"))
    provenance = evaluation_metrics["provenance"]
    calibrated = None
    if temperature_record is not None:
        record = json.loads(temperature_record.read_text(encoding="utf-8"))
        approval_record = json.loads(approval.read_text(encoding="utf-8"))
        if (record.get("schema_version") != SCHEMA_VERSION or record.get("fit_partition") != "calibration"
            or record.get("checkpoint_sha256") != provenance["checkpoint_sha256"]
            or record.get("approval_sha256") != provenance["approval_sha256"]
            or not approval_record.get("calibration_partition_frozen")
            or not approval_record.get("calibration_separate_from_model_selection")
            or record.get("calibration_data_sha256") != approval_record.get("calibration_data_sha256")):
            raise ValueError("Temperature record is not frozen for this approved checkpoint and cohort")
        calibrated = apply_temperature_to_probabilities(probabilities, float(record["temperature"]))
    if choose_minimum_coverage is not None and final_test:
        raise ValueError("Cannot select an abstention threshold on final test")
    selected = (select_threshold_on_validation(probabilities, targets,
                                               minimum_coverage=choose_minimum_coverage,
                                               partition="validation")
                if choose_minimum_coverage is not None else None)
    threshold_result = None
    if threshold_record is not None:
        record = json.loads(threshold_record.read_text(encoding="utf-8"))
        if (record.get("selection_partition") not in ("validation", "calibration")
            or record.get("checkpoint_sha256") != provenance["checkpoint_sha256"]
            or record.get("approval_sha256") != provenance["approval_sha256"]
            or record.get("split_sha256") != provenance["split_sha256"]):
            raise ValueError("Threshold record was not selected on this approved cohort")
        threshold_result = selective_at_threshold(probabilities, targets, float(record["threshold"]))
    quality_join = None
    quality_calibration = None
    if (iqa_csv is None) != (iqa_view is None):
        raise ValueError("IQA CSV and measurement view must be provided together")
    if iqa_csv is not None:
        quality_join = join_quality_predictions(read_csv(iqa_csv), predictions, view=iqa_view,
                                                source_rows=cohort)
        quality_calibration = quality_group_calibration(quality_join, probabilities, targets)
    metrics = calibration_metrics(probabilities, targets)
    entropy = uncertainty_from_probabilities(probabilities, targets)
    output_dir.mkdir(parents=True, exist_ok=False)
    rows = []
    source_index = {(r["source_dataset"], r["image_path"]): r for r in cohort}
    for i, row in enumerate(predictions):
        key = (row["source_dataset"], row["image_path"])
        source = source_index[key]
        item = {"source_dataset": key[0], "image_path": key[1], "source_image_sha256": source["sha256"],
                "target_index": int(targets[i]), "predicted_index": int(entropy["predicted_index"][i]),
                **{f"prob_{name}": float(probabilities[i, j]) for j, name in enumerate(CLASS_NAMES)},
                **{name: float(entropy[name][i]) for name in ("confidence", "predictive_entropy",
                                                               "normalized_entropy", "top_two_margin",
                                                               "negative_log_likelihood")}}
        if calibrated is not None:
            item.update({f"cal_prob_{name}": float(calibrated[i, j]) for j, name in enumerate(CLASS_NAMES)})
        if quality_join is not None:
            from nine_class_iqa import FEATURES
            item.update({feature: quality_join[i][feature] for feature in FEATURES})
            item["measurement_view"] = iqa_view
        rows.append(item)
    with (output_dir / "uncertainty_records.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if quality_calibration is not None:
        with (output_dir / "iqa_calibration_by_quantile.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(quality_calibration[0]))
            writer.writeheader()
            writer.writerows(quality_calibration)
    figures = render_plots(probabilities, targets, output_dir, title_prefix="APPROVED EVALUATION")
    report = {"status": "APPROVED_EVALUATION_ASSOCIATION_NOT_CLINICAL_SAFETY",
              "schema_version": SCHEMA_VERSION, "split": evaluation_metrics["split"],
              "label_order": CLASS_NAMES, "n": len(rows), "uncalibrated_calibration": metrics,
              "calibrated_calibration": calibration_metrics(calibrated, targets) if calibrated is not None else None,
              "threshold_selected_on_validation": selected,
              "frozen_threshold_evaluation": threshold_result,
              "iqa_joined": iqa_csv is not None,
              "iqa_calibration_quantile_rows": len(quality_calibration) if quality_calibration is not None else 0,
              "figures": figures,
              "provenance": {"evaluation_metrics_sha256": file_sha256(evaluation_dir / "metrics.json"),
                             "predictions_sha256": file_sha256(evaluation_dir / "predictions.csv"),
                             "approved_split_sha256": file_sha256(split_csv),
                             "approval_sha256": file_sha256(approval),
                             "iqa_sha256": file_sha256(iqa_csv) if iqa_csv else None,
                             "temperature_record_sha256": file_sha256(temperature_record) if temperature_record else None,
                             "threshold_record_sha256": file_sha256(threshold_record) if threshold_record else None}}
    (output_dir / "uncertainty_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if selected is not None:
        frozen = {**selected, "checkpoint_sha256": provenance["checkpoint_sha256"],
                  "approval_sha256": provenance["approval_sha256"],
                  "split_sha256": provenance["split_sha256"]}
        (output_dir / "selected_threshold.json").write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    return report


def synthetic_demo(output_dir: Path) -> dict:
    if output_dir.exists():
        raise FileExistsError(output_dir)
    # Deterministic contrived probabilities, never a model or clinical image.
    targets = np.tile(np.arange(9), 3)
    probabilities = np.full((len(targets), 9), 0.025)
    for i, target in enumerate(targets):
        dominant = int(target if i % 4 else (target + 1) % 9)
        probabilities[i, dominant] = 0.8
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    output_dir.mkdir(parents=True, exist_ok=False)
    figures = render_plots(probabilities, targets, output_dir,
                           title_prefix="SYNTHETIC ONLY")
    summary = {"status": "SYNTHETIC_DEMONSTRATION_ONLY", "label_order": CLASS_NAMES,
               "n": len(targets), "figures": figures,
               "numeric_values_are_not_model_or_clinical_results": True}
    (output_dir / "synthetic_demo.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-demo", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--approved-split", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--evaluation-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--final-test", action="store_true")
    parser.add_argument("--iqa-csv", type=Path)
    parser.add_argument("--iqa-view", choices=("raw", "stage4_processed"))
    parser.add_argument("--temperature-record", type=Path)
    parser.add_argument("--threshold-record", type=Path)
    parser.add_argument("--choose-minimum-coverage", type=float)
    args = parser.parse_args()
    if args.synthetic_demo:
        if any((args.approved_split, args.approval, args.inventory, args.evaluation_dir,
                args.final_test, args.iqa_csv, args.temperature_record, args.threshold_record,
                args.choose_minimum_coverage is not None)):
            raise ValueError("Synthetic demo cannot be mixed with approved-evaluation options")
        result = synthetic_demo(args.output_dir)
    else:
        if not all((args.approved_split, args.approval, args.inventory, args.evaluation_dir)):
            raise ValueError("Approved split, approval, inventory and evaluation artifacts are required")
        result = run(args.root, args.approved_split, args.approval, args.inventory,
                     args.evaluation_dir, args.output_dir, final_test=args.final_test,
                     iqa_csv=args.iqa_csv, iqa_view=args.iqa_view,
                     temperature_record=args.temperature_record,
                     threshold_record=args.threshold_record,
                     choose_minimum_coverage=args.choose_minimum_coverage)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
