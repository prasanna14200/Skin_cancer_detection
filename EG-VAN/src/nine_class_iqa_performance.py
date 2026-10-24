"""Future gated association of IQA proxies with approved Stage 6 predictions."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nine_class_iqa import FEATURES, IQA_VERSION
from nine_class_protocol import file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES, ROOT


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_evaluation_artifact(root: Path, split_csv: Path, approval: Path,
                                 inventory: Path, evaluation_dir: Path,
                                 *, final_test: bool = False) -> tuple[list[dict], list[dict]]:
    """Require real Stage 6 approval and matching complete evaluation artifacts."""
    split_rows, provenance = validate_approved_split(root, split_csv, approval, inventory)
    metrics_path = evaluation_dir / "metrics.json"
    prediction_path = evaluation_dir / "predictions.csv"
    if not metrics_path.is_file():
        raise FileNotFoundError(metrics_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    partition = metrics.get("split")
    if partition not in ("validation", "test"):
        raise ValueError("Only approved validation or final-test predictions can be joined")
    if partition == "test" and (not final_test or not provenance["approval"].get("test_partition_frozen")
                                or not provenance["test_has_all_classes"]):
        raise ValueError("Protected test analysis requires --final-test and frozen nine-class test")
    if partition == "validation" and final_test:
        raise ValueError("--final-test cannot authorize validation as a test result")
    expected = {"split_sha256": provenance["split_sha256"],
                "inventory_sha256": provenance["inventory_sha256"],
                "approval_sha256": provenance["approval_sha256"]}
    if any(metrics.get("provenance", {}).get(key) != value for key, value in expected.items()):
        raise ValueError("Evaluation provenance does not match approved cohort")
    if not metrics.get("provenance", {}).get("checkpoint_sha256"):
        raise ValueError("Missing checkpoint provenance")
    checkpoint = Path(metrics["provenance"].get("checkpoint_path", ""))
    if not checkpoint.is_file() or file_sha256(checkpoint) != metrics["provenance"]["checkpoint_sha256"]:
        raise ValueError("Evaluation checkpoint is absent or its hash changed")
    predictions = read_csv(prediction_path)
    cohort = {(r["source_dataset"], r["image_path"]): r for r in split_rows if r["split"] == partition}
    keys = [(r.get("source_dataset"), r.get("image_path")) for r in predictions]
    if len(predictions) != metrics.get("n_samples") or len(keys) != len(cohort) or set(keys) != set(cohort):
        raise ValueError("Predictions are incomplete or do not match the approved partition")
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate prediction image keys")
    for row in predictions:
        original = cohort[(row["source_dataset"], row["image_path"])]
        if int(row["target_index"]) != int(original["class_index"]):
            raise ValueError("Prediction target differs from approved label")
        probabilities = np.array([float(row[f"prob_{name}"]) for name in CLASS_NAMES])
        if not np.isfinite(probabilities).all() or (probabilities < 0).any() or not np.isclose(probabilities.sum(), 1, atol=1e-5):
            raise ValueError("Invalid prediction probabilities")
        if int(row["predicted_index"]) != int(probabilities.argmax()):
            raise ValueError("Prediction index and probabilities disagree")
    observed_accuracy = float(np.mean([int(r["target_index"]) == int(r["predicted_index"])
                                       for r in predictions]))
    if metrics.get("accuracy") is None or not np.isclose(metrics["accuracy"], observed_accuracy):
        raise ValueError("Evaluation summary accuracy disagrees with predictions")
    return predictions, split_rows


def join_quality_predictions(quality: list[dict], predictions: list[dict],
                             *, view: str, source_rows: list[dict] | None = None) -> list[dict]:
    if view not in ("raw", "stage4_processed"):
        raise ValueError("Unknown measurement view")
    selected = [r for r in quality if r.get("measurement_view") == view]
    if not selected or any(r.get("iqa_config_version") != IQA_VERSION or
                           r.get("processing_status") != "OK" for r in selected):
        raise ValueError("IQA records absent, invalid, or incompatible")
    if len({r.get("preprocess_config_sha256") for r in selected}) != 1:
        raise ValueError("Mixed IQA preprocessing configurations")
    keys = [(r["source_dataset"], r["image_path"]) for r in selected]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate IQA image keys")
    index = dict(zip(keys, selected))
    source = {(r["source_dataset"], r["image_path"]): r for r in source_rows} if source_rows is not None else None
    result = []
    for prediction in predictions:
        key = (prediction["source_dataset"], prediction["image_path"])
        if key not in index:
            raise ValueError(f"Missing {view} quality measurement for {key}")
        iqa = index[key]
        if source is not None and iqa["source_image_sha256"] != source[key]["sha256"]:
            raise ValueError("IQA source-image hash differs from approved cohort")
        probabilities = np.array([float(prediction[f"prob_{name}"]) for name in CLASS_NAMES])
        target, predicted = int(prediction["target_index"]), int(prediction["predicted_index"])
        result.append({"source_dataset": key[0], "image_path": key[1],
                       "class_name": CLASS_NAMES[target], "correct": int(target == predicted),
                       "confidence": float(probabilities.max()),
                       "predictive_entropy_normalized": float(-np.sum(probabilities * np.log(np.maximum(probabilities, 1e-12))) / math.log(9)),
                       **{name: float(iqa[name]) for name in FEATURES}})
    return result


def summarize_associations(rows: list[dict], feature: str, bins: int = 4) -> list[dict]:
    """Equal-count rank bins with stable tie ordering, reported as associations."""
    if feature not in FEATURES or bins < 2 or not rows:
        raise ValueError("Invalid feature, bin count, or empty association input")
    ordered = sorted(rows, key=lambda r: (r[feature], r["source_dataset"], r["image_path"]))
    result = []
    for index in range(bins):
        subset = [r for position, r in enumerate(ordered) if min(bins - 1, position * bins // len(rows)) == index]
        if not subset:
            continue
        result.append({"feature": feature, "quantile_rank": index + 1, "n": len(subset),
                       "feature_min": subset[0][feature], "feature_max": subset[-1][feature],
                       "accuracy": float(np.mean([r["correct"] for r in subset])),
                       "error_rate": float(1 - np.mean([r["correct"] for r in subset])),
                       "mean_confidence": float(np.mean([r["confidence"] for r in subset])),
                       "mean_predictive_entropy_normalized": float(np.mean([r["predictive_entropy_normalized"] for r in subset]))})
    return result


def run(root: Path, split_csv: Path, approval: Path, inventory: Path,
        evaluation_dir: Path, iqa_csv: Path, output_dir: Path, *, view: str,
        final_test: bool = False) -> dict:
    if output_dir.exists():
        raise FileExistsError(output_dir)
    predictions, source_rows = validate_evaluation_artifact(root, split_csv, approval, inventory,
                                                            evaluation_dir, final_test=final_test)
    quality = read_csv(iqa_csv)
    joined = join_quality_predictions(quality, predictions, view=view, source_rows=source_rows)
    summaries = [item for feature in FEATURES for item in summarize_associations(joined, feature)]
    per_class = []
    for name in CLASS_NAMES:
        subset = [r for r in joined if r["class_name"] == name]
        if subset:
            per_class.append({"class_name": name, "n": len(subset),
                              **{f"{feature}_{stat}": float(value)
                                 for feature in FEATURES
                                 for stat, value in (
                                     ("mean", np.mean([r[feature] for r in subset])),
                                     ("q25", np.quantile([r[feature] for r in subset], 0.25)),
                                     ("median", np.median([r[feature] for r in subset])),
                                     ("q75", np.quantile([r[feature] for r in subset], 0.75)))}})
    output_dir.mkdir(parents=True, exist_ok=False)
    for filename, records in (("quality_prediction_join.csv", joined),
                              ("quality_quantile_summary.csv", summaries),
                              ("per_class_quality.csv", per_class)):
        with (output_dir / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    for feature in ("sharpness_laplacian_variance", "brightness_mean", "contrast_std",
                    "underexposed_fraction", "overexposed_fraction"):
        group = [r for r in summaries if r["feature"] == feature]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot([r["quantile_rank"] for r in group], [r["accuracy"] for r in group], marker="o", label="Accuracy")
        ax.plot([r["quantile_rank"] for r in group], [r["error_rate"] for r in group], marker="s", label="Error rate")
        ax.set(xlabel="Feature rank quantile", ylabel="Observed fraction", ylim=(0, 1),
               title=f"{feature}: approved prediction association")
        ax.legend()
        fig.tight_layout()
        fig.savefig(output_dir / f"quality_performance_{feature}.png", dpi=140)
        plt.close(fig)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].scatter([r[feature] for r in joined], [r["confidence"] for r in joined], s=10)
        axes[0].set(xlabel=feature, ylabel="Maximum class probability")
        axes[1].scatter([r[feature] for r in joined], [r["predictive_entropy_normalized"] for r in joined], s=10)
        axes[1].set(xlabel=feature, ylabel="Normalized predictive entropy")
        fig.tight_layout()
        fig.savefig(output_dir / f"quality_confidence_uncertainty_{feature}.png", dpi=140)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(8, 4))
        class_values = [[r[feature] for r in joined if r["class_name"] == name] for name in CLASS_NAMES]
        ax.boxplot(class_values, tick_labels=CLASS_NAMES, showfliers=False)
        ax.set(xlabel="Source-defined class", ylabel=feature, title="Approved-cohort class distributions")
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        fig.savefig(output_dir / f"per_class_{feature}.png", dpi=140)
        plt.close(fig)
    metadata = {"status": "OBSERVATIONAL_ASSOCIATION_NOT_CAUSAL", "measurement_view": view,
                "evaluation_split": "test" if final_test else "validation", "n": len(joined),
                "evaluation_metrics_sha256": file_sha256(evaluation_dir / "metrics.json"),
                "prediction_sha256": file_sha256(evaluation_dir / "predictions.csv"),
                "iqa_sha256": file_sha256(iqa_csv), "approved_split_sha256": file_sha256(split_csv)}
    (output_dir / "analysis_provenance.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--approved-split", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--evaluation-dir", type=Path, required=True)
    parser.add_argument("--iqa-csv", type=Path, required=True)
    parser.add_argument("--view", choices=("raw", "stage4_processed"), required=True)
    parser.add_argument("--final-test", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.approved_split, args.approval, args.inventory,
                         args.evaluation_dir, args.iqa_csv, args.output_dir,
                         view=args.view, final_test=args.final_test), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
