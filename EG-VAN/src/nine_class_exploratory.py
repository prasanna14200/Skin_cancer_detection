"""EXPLORATORY_ONLY nine-label experiment; never confers clinical approval.

Uses the frozen planning preview and original source-defined labels. This runner
is intentionally separate from the approved Stage 6 training/evaluation gates.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Collection
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from uuid import uuid4

import cv2
import numpy as np
import torch
from torch.optim import Adamax
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from nine_class_dataset import NineClassDataset, preprocessing_for_training, preprocessing_hash
from nine_class_iqa import measure_rgb
from nine_class_metrics import summarize_predictions
from nine_class_protocol import file_sha256, read_rows
from nine_class_stage4 import CLASS_NAMES, ROOT
from nine_class_uncertainty import (calibration_metrics, fit_temperature,
                                    softmax_logits, uncertainty_from_probabilities)

PREVIEW = ROOT / "analysis/nine_class_final_cohort/four_way_planning_assignment_v1.csv"
REPORT = ROOT / "analysis/nine_class_final_cohort/four_way_feasibility_report_v1.json"
SIIM_DECISIONS = ROOT / "analysis/nine_class_final_cohort/candidate_decision_manifest_v2.csv"
CONFIG = ROOT / "config/nine_class_training_t4_four_way_v2.json"
OUT = ROOT / "analysis/nine_class_exploratory"
RUNS_ROOT = OUT / "runs"
SPLIT = OUT / "exploratory_split.csv"
META = OUT / "exploratory_provenance.json"
PARTITIONS = ("train", "validation", "calibration", "test")
RESEARCH_STATUS = "EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION"
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _safe_relative_image_path(value: object) -> Path:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Malformed or empty image_path")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError("Malformed image_path")

    windows_path = PureWindowsPath(value)
    if (windows_path.drive or windows_path.root or windows_path.is_absolute()
            or PurePosixPath(value).is_absolute()):
        raise ValueError(f"image_path must be relative: {value!r}")

    components = value.replace("\\", "/").split("/")
    if any(
        component in ("", ".", "..")
        or any(character in '<>:"|?*' for character in component)
        or component.endswith((" ", "."))
        or component.rstrip(" .").split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
        for component in components
    ):
        raise ValueError(f"Unsafe or malformed image_path: {value!r}")
    return Path(*components)


def validate_preview(root: Path = ROOT, *, verify_bytes: bool = False,
                     image_partitions: Collection[str] | None = None) -> tuple[list[dict], dict]:
    """Reject known/suspected crossings; leave unknown identity uncertainty explicit."""
    root = root.resolve()
    checked_partitions = set(PARTITIONS if image_partitions is None else image_partitions)
    if not checked_partitions <= set(PARTITIONS):
        raise ValueError("Unknown image partition in integrity scope")
    rows = read_rows(PREVIEW)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report["status"] != "PLANNING_ONLY_NOT_APPROVED" or report["planning_assignment_sha256"] != file_sha256(PREVIEW):
        raise ValueError("Frozen planning preview or its evidence report changed")
    if not rows or len(rows) != report["planning_inventory_rows"]:
        raise ValueError("Planning inventory count changed")
    siim = {r["image_id"]: r for r in read_rows(SIIM_DECISIONS)}
    unique_paths = set()
    group_splits = defaultdict(set)
    hash_splits = defaultdict(set)
    lesion_splits = defaultdict(set)
    patient_splits = defaultdict(set)
    counts = {part: Counter() for part in PARTITIONS}
    for row in rows:
        path = row.get("image_path")
        relative_path = _safe_relative_image_path(path)
        canonical_path = relative_path.as_posix()
        if canonical_path in unique_paths or row["approval_status"] != "NOT_APPROVED":
            raise ValueError("Duplicate path or false approval in exploratory preview")
        unique_paths.add(canonical_path)
        label, partition = row["class_name"], row["proposed_partition"]
        if label not in CLASS_NAMES or int(row["class_index"]) != CLASS_NAMES.index(label) or partition not in PARTITIONS:
            raise ValueError("Invalid nine-label index or partition")
        if row["source_split"] == "test" and partition != "test":
            raise ValueError("Publisher test record outside test")
        if row["source_dataset"] == "HAM10000":
            if label in ("BENIGN", "MALIGNANT") or row["original_label"].upper() != label:
                raise ValueError("HAM diagnosis changed")
            if row["automated_status"] != "HAM_AVAILABLE_NOT_FINAL_ELIGIBLE":
                raise ValueError("Unexpected HAM eligibility status")
        elif row["source_dataset"] == "FANCONIC_LOCAL_UNVERIFIED_VERSION":
            if label != "MALIGNANT" or row["original_label"] != "malignant" or row["automated_status"] not in (
                "BINARY_PROVISIONAL_SOURCE_TRAIN", "PROTECTED_SOURCE_TEST_UNADJUDICATED"
            ):
                raise ValueError("Unexpected Fanconic label or status")
        elif row["source_dataset"] == "SIIM-ISIC 2020 training v2":
            source = siim.get(row["image_id"])
            if (label != "BENIGN" or row["original_label"] != "benign" or source is None
                or source["original_target"] != "0" or source["patient_id"] != row["patient_id"]
                or row["automated_status"] != "PRELIMINARY_NO_CANDIDATE_NOT_APPROVED"
                or source["actual_automated_status"] != "PRELIMINARY_NO_CANDIDATE_NOT_APPROVED"
                or source["approval_status"] != "NOT_APPROVED"):
                raise ValueError("SIIM image is not a source-defined, no-candidate preliminary record")
        else:
            raise ValueError("Unexpected source dataset")
        if partition in checked_partitions:
            absolute = (root / relative_path).resolve()
            if not absolute.is_relative_to(root) or not absolute.is_file():
                raise FileNotFoundError(absolute)
            if verify_bytes and file_sha256(absolute) != row["sha256"]:
                raise ValueError(f"Source image bytes changed: {path}")
        group_splits[row["overlap_group"]].add(partition)
        hash_splits[row["sha256"]].add(partition)
        if row["lesion_id"]:
            lesion_splits[(row["source_dataset"], row["lesion_id"])].add(partition)
        if row["patient_id"]:
            patient_splits[(row["source_dataset"], row["patient_id"])].add(partition)
        counts[partition][label] += 1
    for name, table in (("overlap", group_splits), ("SHA-256", hash_splits),
                        ("lesion", lesion_splits), ("patient", patient_splits)):
        if any(len(parts) > 1 for parts in table.values()):
            raise ValueError(f"Known {name} group crosses exploratory partitions")
    if any(counts[part][name] < 1 for part in PARTITIONS for name in CLASS_NAMES):
        raise ValueError("Nine-label exploratory split lacks a class")
    return rows, {"status": RESEARCH_STATUS, "counts": {part: dict(counts[part]) for part in PARTITIONS},
                  "unknown_patient_and_photo_identity": True, "known_group_crossings": 0,
                  "source_preview_sha256": file_sha256(PREVIEW)}


def prepare(root: Path, *, verify_bytes: bool = True) -> dict:
    rows, report = validate_preview(root, verify_bytes=verify_bytes)
    derived = [{**r, "split": r["proposed_partition"], "research_status": RESEARCH_STATUS} for r in rows]
    if SPLIT.exists():
        existing = read_rows(SPLIT)
        if existing != derived:
            raise ValueError("Existing exploratory split differs; refuse overwrite")
    else:
        _write_csv(SPLIT, derived, list(derived[0]))
    report = {**report, "split_sha256": file_sha256(SPLIT), "config_sha256": file_sha256(CONFIG),
              "limitations": ["All records remain NOT_APPROVED", "Fanconic patient IDs and rights unverified",
                              "No-candidate SIIM status does not prove photographic independence",
                              "Source-defined labels are not mutually exclusive diagnoses"]}
    if META.exists() and json.loads(META.read_text(encoding="utf-8")) != report:
        raise ValueError("Existing exploratory provenance differs; refuse overwrite")
    META.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def validate_frozen(root: Path, *, verify_bytes: bool = False,
                    image_partitions: Collection[str] | None = None) -> tuple[list[dict], dict]:
    if not SPLIT.is_file() or not META.is_file():
        raise FileNotFoundError("Run prepare before training")
    rows, report = validate_preview(root, verify_bytes=verify_bytes,
                                    image_partitions=image_partitions)
    frozen = json.loads(META.read_text(encoding="utf-8"))
    if frozen["status"] != RESEARCH_STATUS or frozen["source_preview_sha256"] != report["source_preview_sha256"]:
        raise ValueError("Exploratory provenance mismatch")
    if frozen["split_sha256"] != file_sha256(SPLIT) or frozen["config_sha256"] != file_sha256(CONFIG):
        raise ValueError("Exploratory split or T4 config changed")
    actual = read_rows(SPLIT)
    expected_rows = [{**r, "split": r["proposed_partition"], "research_status": RESEARCH_STATUS} for r in rows]
    if actual != expected_rows:
        raise ValueError("Exploratory split is not the frozen preview")
    return actual, frozen


def preflight(root: Path) -> dict:
    from nine_class_training import load_config
    rows, frozen = validate_frozen(root, verify_bytes=True)
    config = load_config(CONFIG)
    if config["batch_size"] != 8 or config["gradient_accumulation_steps"] != 4 or config["epochs"] != 25 or config["mixed_precision"] != "cuda_if_available":
        raise ValueError("T4 exploratory settings changed")
    preprocess = preprocessing_for_training(config)
    loaded = {}
    for part in PARTITIONS:
        dataset = NineClassDataset(root, SPLIT, part, preprocess)
        first_by_class = {}
        for index, row in enumerate(dataset.rows):
            first_by_class.setdefault(row["class_name"], index)
        for name, index in first_by_class.items():
            image, target = dataset[index]
            if image.shape != (3, 384, 384) or not torch.isfinite(image).all() or target != CLASS_NAMES.index(name):
                raise ValueError("Real-image loader failed")
        loaded[part] = len(first_by_class)
    return {"status": RESEARCH_STATUS, "verified_image_hashes": len(rows),
            "real_images_loaded_per_partition": loaded, "counts": frozen["counts"],
            "preprocess_sha256": preprocessing_hash(preprocess)}


def _checkpoint_state(expected: dict, epoch: int, model: torch.nn.Module, optimizer,
                      scheduler, scaler, best_loss: float, train_metrics: dict,
                      validation_metrics: dict) -> dict:
    from nine_class_training import capture_rng_state

    return {**expected, "epoch": epoch, "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(), "scheduler_state": scheduler.state_dict(),
            "scaler_state": scaler.state_dict(), "best_validation_loss": best_loss,
            **capture_rng_state(),
            "train_metrics": train_metrics, "validation_metrics": validation_metrics}


def train(root: Path, runs_root: Path, resume: Path | None) -> Path:
    from nine_class_training import (build_model, load_checkpoint,
                                     load_config, run_epoch, save_checkpoint, seed_all,
                                     training_class_weights)
    rows, frozen = validate_frozen(root, verify_bytes=True)
    config = load_config(CONFIG)
    seed_all(int(config["seed"]))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("Full exploratory training requires CUDA; run preflight locally")
    model, init_hashes = build_model(config, root)
    model.to(device)
    optimizer = Adamax(model.parameters(), lr=float(config["learning_rate"]))
    scheduler_cfg = config["scheduler"]
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=float(scheduler_cfg["factor"]),
                                  patience=int(scheduler_cfg["patience"]))
    scaler = torch.amp.GradScaler("cuda", enabled=True)
    class_weights = training_class_weights(rows).to(device) if config["class_weighting"] else None
    expected = {"research_status": RESEARCH_STATUS, "config_sha256": frozen["config_sha256"],
                "split_sha256": frozen["split_sha256"],
                "preprocess_config_sha256": preprocessing_hash(preprocessing_for_training(config))}
    if resume is not None:
        resume = resume.resolve()
        if resume.name != "last.pt" or not resume.is_relative_to(runs_root.resolve()):
            raise ValueError("Resume requires exploratory runs-root/…/last.pt")
        run_dir = resume.parent
        info = json.loads((run_dir / "run_provenance.json").read_text(encoding="utf-8"))
        if any(info.get(key) != value for key, value in expected.items()):
            raise ValueError("Resume provenance differs")
        state = load_checkpoint(resume, model, optimizer, scheduler, scaler,
                                expected=expected, restore_rng=True)
        start_epoch, best_loss = int(state["epoch"]) + 1, float(state["best_validation_loss"])
    else:
        run_dir = runs_root / ("EXPLORATORY_ONLY_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / "run_provenance.json").write_text(json.dumps({**expected, "config": config,
            "source_preview_sha256": frozen["source_preview_sha256"], "device": str(device),
            "initialization_hashes": init_hashes, "limitations": frozen["limitations"]}, indent=2) + "\n", encoding="utf-8")
        start_epoch, best_loss = 0, float("inf")
    train_data = NineClassDataset(root, SPLIT, "train", preprocessing_for_training(config))
    val_data = NineClassDataset(root, SPLIT, "validation", preprocessing_for_training(config))
    history = run_dir / "history.csv"
    for epoch in range(start_epoch, int(config["epochs"])):
        seed_all(int(config["seed"]) + epoch)
        generator = torch.Generator().manual_seed(int(config["seed"]) + epoch)
        common = dict(batch_size=8, num_workers=0, pin_memory=True)
        train_loader = DataLoader(train_data, shuffle=True, generator=generator, **common)
        val_loader = DataLoader(val_data, shuffle=False, **common)
        train_result = run_epoch(model, train_loader, device, config, optimizer=optimizer,
                                 scaler=scaler, class_weights=class_weights)
        val_result = run_epoch(model, val_loader, device, config, class_weights=class_weights)
        scheduler.step(val_result["loss"])
        improved = val_result["loss"] < best_loss
        best_loss = min(best_loss, val_result["loss"])
        state = _checkpoint_state(expected, epoch, model, optimizer, scheduler, scaler,
                                  best_loss, train_result, val_result)
        save_checkpoint(run_dir / "last.pt", state)
        if improved:
            save_checkpoint(run_dir / "best.pt", state)
        with history.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=("research_status", "epoch", "train_loss", "train_accuracy",
                "train_macro_f1", "validation_loss", "validation_accuracy", "validation_macro_f1", "learning_rate"))
            if handle.tell() == 0:
                writer.writeheader()
            writer.writerow({"research_status": RESEARCH_STATUS, "epoch": epoch + 1,
                             "train_loss": train_result["loss"],
                             "train_accuracy": train_result["accuracy"], "train_macro_f1": train_result["macro_f1"],
                             "validation_loss": val_result["loss"], "validation_accuracy": val_result["accuracy"],
                             "validation_macro_f1": val_result["macro_f1"], "learning_rate": optimizer.param_groups[0]["lr"]})
        print(json.dumps({"status": RESEARCH_STATUS, "epoch": epoch + 1, "train_loss": train_result["loss"],
                          "validation_loss": val_result["loss"], "run_dir": str(run_dir)}), flush=True)
    return run_dir


def _plot_history(run_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = read_rows(run_dir / "history.csv")
    if not history:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, metric, label in ((axes[0], "loss", "Focal loss"), (axes[1], "macro_f1", "Macro F1")):
        for part in ("train", "validation"):
            ax.plot([int(r["epoch"]) for r in history], [float(r[f"{part}_{metric}"]) for r in history], label=part)
        ax.set(xlabel="Epoch", ylabel=label, title=f"EXPLORATORY ONLY: {label}")
        ax.legend()
    fig.tight_layout()
    fig.savefig(run_dir / "training_curves.png", dpi=140)
    plt.close(fig)


def evaluate(root: Path, checkpoint: Path, output_dir: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from nine_class_evaluation import predict
    from nine_class_training import build_model, load_checkpoint, load_config
    _, frozen = validate_frozen(root, verify_bytes=True)
    checkpoint = checkpoint.resolve()
    if checkpoint.name != "best.pt":
        raise ValueError("Evaluate the validation-selected best.pt only")
    run_dir = checkpoint.parent
    info = json.loads((run_dir / "run_provenance.json").read_text(encoding="utf-8"))
    expected = {"research_status": RESEARCH_STATUS, "config_sha256": frozen["config_sha256"],
                "split_sha256": frozen["split_sha256"]}
    if any(info.get(k) != v for k, v in expected.items()):
        raise ValueError("Evaluation cohort/config differs from training")
    config = load_config(CONFIG)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _ = build_model(config, root)
    state = load_checkpoint(checkpoint, model, expected=expected, restore_rng=False)
    model.to(device).eval()
    output_dir.mkdir(parents=True, exist_ok=False)
    predictions = {}
    reports = {}
    for part in ("validation", "calibration", "test"):
        dataset = NineClassDataset(root, SPLIT, part, preprocessing_for_training(config))
        loader = DataLoader(dataset, batch_size=8, shuffle=False, num_workers=0)
        probabilities, targets, logits = predict(model, loader, device, return_logits=True)
        predictions[part] = (probabilities, targets, logits)
        report = summarize_predictions(probabilities, targets, split=part)
        report["macro_precision"] = float(np.mean([r["precision"] for r in report["per_class"].values()]))
        report["macro_recall"] = float(np.mean([r["recall"] for r in report["per_class"].values()]))
        report["research_status"] = RESEARCH_STATUS
        report["checkpoint_sha256"] = file_sha256(checkpoint)
        reports[part] = report
        (output_dir / f"{part}_metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        uncertainty = uncertainty_from_probabilities(probabilities, targets)
        fields = ["research_status", "image_path", "source_dataset", "original_label", "target_index",
                  "predicted_index", "confidence", "normalized_entropy"] + [f"prob_{name}" for name in CLASS_NAMES] + [
                      f"logit_{name}" for name in CLASS_NAMES]
        records = []
        for i, row in enumerate(dataset.rows):
            records.append({"research_status": RESEARCH_STATUS, "image_path": row["image_path"],
                "source_dataset": row["source_dataset"],
                "original_label": row["original_label"], "target_index": int(targets[i]),
                "predicted_index": int(probabilities[i].argmax()), "confidence": float(uncertainty["confidence"][i]),
                "normalized_entropy": float(uncertainty["normalized_entropy"][i]),
                **{f"prob_{name}": float(probabilities[i, j]) for j, name in enumerate(CLASS_NAMES)},
                **{f"logit_{name}": float(logits[i, j]) for j, name in enumerate(CLASS_NAMES)}})
        _write_csv(output_dir / f"{part}_predictions.csv", records, fields)
    _, cal_targets, cal_logits = predictions["calibration"]
    temperature = fit_temperature(cal_logits, cal_targets)
    temperature["fit_partition"] = "calibration"
    temperature["research_status"] = RESEARCH_STATUS
    (output_dir / "calibration_temperature.json").write_text(json.dumps(temperature, indent=2) + "\n", encoding="utf-8")
    test_probs, test_targets, test_logits = predictions["test"]
    calib_report = {"uncalibrated": calibration_metrics(test_probs, test_targets),
                    "temperature_scaled": calibration_metrics(softmax_logits(test_logits, temperature=temperature["temperature"]), test_targets),
                    "temperature_fit_partition": "calibration", "research_status": RESEARCH_STATUS}
    (output_dir / "test_uncertainty_calibration.json").write_text(json.dumps(calib_report, indent=2) + "\n", encoding="utf-8")
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(reports["test"]["confusion_matrix"], cmap="Blues")
    ax.set(xticks=range(9), yticks=range(9), xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
           xlabel="Predicted", ylabel="Source-defined target", title="EXPLORATORY ONLY: test confusion matrix")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / "test_confusion_matrix.png", dpi=150)
    plt.close(fig)
    _plot_history(run_dir)
    # Raw-image quality proxies; report association, not diagnostic image adequacy.
    test_rows = NineClassDataset(root, SPLIT, "test", preprocessing_for_training(config)).rows
    iqa_records = []
    for i, row in enumerate(test_rows):
        bgr = cv2.imread(str(root / row["image_path"]), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError(f"Could not read test image for IQA: {row['image_path']}")
        metrics, flags = measure_rgb(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        iqa_records.append({"research_status": RESEARCH_STATUS, "image_path": row["image_path"],
                            "source_dataset": row["source_dataset"],
                            "error": int(test_probs[i].argmax() != test_targets[i]),
                            "invalid_metric_flags": ";".join(flags), **metrics})
    _write_csv(output_dir / "test_image_quality_vs_error.csv", iqa_records, list(iqa_records[0]))
    association = {}
    errors = np.array([r["error"] for r in iqa_records])
    for key in ("sharpness_laplacian_variance", "brightness_mean", "contrast_std", "dark_border_fraction"):
        values = np.array([r[key] for r in iqa_records], dtype=float)
        median = float(np.median(values))
        low, high = values <= median, values > median
        association[key] = {"median": median, "low_n": int(low.sum()), "low_error_rate": float(errors[low].mean()),
                            "high_n": int(high.sum()), "high_error_rate": float(errors[high].mean()) if high.any() else None}
    (output_dir / "test_image_quality_summary.json").write_text(json.dumps({"research_status": RESEARCH_STATUS,
        "descriptive_only": True, "metrics": association}, indent=2) + "\n", encoding="utf-8")
    summary = {"research_status": RESEARCH_STATUS, "checkpoint_sha256": file_sha256(checkpoint),
               "checkpoint_epoch": int(state["epoch"]) + 1, "split_sha256": frozen["split_sha256"],
               "test_metrics": reports["test"], "limitations": frozen["limitations"],
               "external_validation": "NOT_AVAILABLE_NO_ELIGIBLE_INDEPENDENT_COHORT"}
    (output_dir / "EXPLORATORY_ONLY_final_report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    test = reports["test"]
    lines = ["# EXPLORATORY ONLY — nonclinical nine-label result", "",
             f"Checkpoint: `{checkpoint.name}`, validation-selected epoch {summary['checkpoint_epoch']}; SHA-256 `{summary['checkpoint_sha256']}`.",
             f"Frozen exploratory split SHA-256: `{frozen['split_sha256']}`. Test size: {test['n_samples']} real originals.",
             f"Test accuracy: {test['accuracy']:.4f}; macro-F1: {test['macro_f1']:.4f}; macro precision: {test['macro_precision']:.4f}; macro recall: {test['macro_recall']:.4f}.",
             "", "| Source-defined label | Test n | Precision | Recall | F1 |", "| --- | ---: | ---: | ---: | ---: |"]
    for name in CLASS_NAMES:
        result = test["per_class"][name]
        lines.append(f"| {name} | {result['support']} | {result['precision']:.4f} | {result['recall']:.4f} | {result['f1']:.4f} |")
    lines += ["", f"Calibration: temperature fitted on the separate calibration partition; test ECE before "
              f"{calib_report['uncalibrated']['ece']:.4f}, after {calib_report['temperature_scaled']['ece']:.4f}.",
              "Raw-image quality/error associations are descriptive and appear in `test_image_quality_summary.json`.",
              "No eligible independent external cohort is available, so external validation is absent.", "",
              "## Interpretation", "",
              "This is a modified source-defined nine-label task, not an exact EG-VAN paper reproduction or a clinical claim.",
              "HAM diagnoses, SIIM melanoma-negative BENIGN and Fanconic folder MALIGNANT have different semantics.",
              "Source shortcuts, unresolved near-photo/patient identity and small BENIGN test support (8) limit interpretation.",
              "All records were NOT_APPROVED for clinical use; only known/suspected groups represented in the existing evidence were kept apart.",
              "Do not compare these metrics directly with the paper or claim clinical generalization."]
    (output_dir / "EXPLORATORY_ONLY_final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "preflight", "train", "evaluate"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path, default=RUNS_ROOT)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == "prepare":
        print(json.dumps(prepare(root), indent=2))
    elif args.action == "preflight":
        result = preflight(root)
        (OUT / "real_image_preflight.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    elif args.action == "train":
        print(train(root, args.runs_root, args.resume))
    else:
        if args.checkpoint is None or args.output_dir is None:
            parser.error("evaluate requires --checkpoint and --output-dir")
        print(json.dumps(evaluate(root, args.checkpoint, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
