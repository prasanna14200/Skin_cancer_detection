"""Synthetic-only tests of nine-class image-quality proxies and artifact gates."""

import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import nine_class_iqa as iqa
from nine_class_dataset import PreprocessConfig, image_tensor
from nine_class_iqa import (IQA_VERSION, collect_record, measure_rgb,
                            select_rows, stage4_processed_rgb)
from nine_class_iqa_performance import (join_quality_predictions, summarize_associations,
                                         validate_evaluation_artifact)
import nine_class_iqa_performance as performance
from nine_class_protocol import LOCKED_FIELDS, file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES


def test_focus_brightness_contrast_exposure_and_uniform_edge_case():
    rng = np.random.default_rng(19)
    texture = rng.integers(20, 235, size=(96, 96), dtype=np.uint8)
    sharp = np.repeat(texture[:, :, None], 3, axis=2)
    blurred = cv2.GaussianBlur(sharp, (15, 15), 4)
    sharp_metrics, _ = measure_rgb(sharp)
    blurred_metrics, _ = measure_rgb(blurred)
    assert sharp_metrics["sharpness_laplacian_variance"] > blurred_metrics["sharpness_laplacian_variance"]
    dark, dark_flags = measure_rgb(np.zeros((32, 32, 3), dtype=np.uint8))
    bright, bright_flags = measure_rgb(np.full((32, 32, 3), 255, dtype=np.uint8))
    assert dark["brightness_mean"] < bright["brightness_mean"]
    assert dark["underexposed_fraction"] == 1 and dark["overexposed_fraction"] == 0
    assert bright["overexposed_fraction"] == 1 and bright["underexposed_fraction"] == 0
    assert dark["contrast_std"] == 0 and dark["sharpness_laplacian_variance"] == 0
    assert "UNIFORM_LUMINANCE" in dark_flags and "UNIFORM_LUMINANCE" in bright_flags
    low = np.full((32, 32, 3), 128, dtype=np.uint8)
    high = np.tile(np.array([0, 255], dtype=np.uint8), (32, 16))
    high = np.repeat(high[:, :, None], 3, axis=2)
    assert measure_rgb(high)[0]["contrast_std"] > measure_rgb(low)[0]["contrast_std"]
    assert all(np.isfinite(v) for v in dark.values())
    with pytest.raises(ValueError):
        measure_rgb(np.zeros((2, 2, 3), dtype=np.float32))


def test_raw_processed_separation_determinism_and_original_integrity(tmp_path):
    gradient = np.tile(np.arange(32, dtype=np.uint8) * 8, (32, 1))
    rgb = np.stack((gradient, np.flipud(gradient), np.full_like(gradient, 100)), axis=2)
    image = tmp_path / "source.jpg"
    assert cv2.imwrite(str(image), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    before = file_sha256(image)
    row = {"image_path": image.name, "source_dataset": "SYNTHETIC", "class_name": "BKL",
           "class_index": "2", "source_split": "train", "split": "train", "sha256": before}
    config = PreprocessConfig(image_size=32)
    raw, raw_pixels = collect_record(tmp_path, row, "raw", config, "synthetic-config")
    processed, processed_pixels = collect_record(tmp_path, row, "stage4_processed", config, "synthetic-config")
    repeat, repeated_pixels = collect_record(tmp_path, row, "stage4_processed", config, "synthetic-config")
    assert raw["measurement_view"] == "raw" and processed["measurement_view"] == "stage4_processed"
    assert raw["source_image_key"] == processed["source_image_key"]
    assert raw["processing_status"] == processed["processing_status"] == "OK"
    assert processed == repeat and np.array_equal(processed_pixels, repeated_pixels)
    assert file_sha256(image) == before
    decoded = cv2.imread(str(image), cv2.IMREAD_COLOR)
    assert np.array_equal(processed_pixels, stage4_processed_rgb(decoded, config))
    tensor = image_tensor(image, config, train=False).numpy().transpose(1, 2, 0)
    restored = np.rint((tensor * np.array(config.std) + np.array(config.mean)) * 255).astype(np.uint8)
    assert np.max(np.abs(restored.astype(int) - processed_pixels.astype(int))) <= 1
    assert raw_pixels.shape == processed_pixels.shape == (32, 32, 3)
    row["sha256"] = "wrong"
    with pytest.raises(ValueError, match="hash changed"):
        collect_record(tmp_path, row, "raw", config, "synthetic-config")


def _prediction(key, target=0):
    probabilities = [0.01] * 9
    probabilities[target] = 0.92
    return {"source_dataset": key[0], "image_path": key[1], "target_index": str(target),
            "predicted_index": str(target),
            **{f"prob_{name}": probabilities[i] for i, name in enumerate(CLASS_NAMES)}}


def test_prediction_join_is_source_qualified_and_checks_hash():
    keys = [("A", "same.jpg"), ("B", "same.jpg")]
    predictions = [_prediction(key) for key in keys]
    quality = [{"source_dataset": source, "image_path": path, "source_image_sha256": source,
                "measurement_view": "raw", "iqa_config_version": IQA_VERSION,
                "preprocess_config_sha256": "synthetic-config",
                "processing_status": "OK", **{feature: float(i) for i, feature in enumerate(
                                              ("sharpness_laplacian_variance", "brightness_mean", "contrast_std",
                                               "underexposed_fraction", "overexposed_fraction", "rgb_mean_r", "rgb_mean_g",
                                               "rgb_mean_b", "rgb_std_r", "rgb_std_g", "rgb_std_b", "color_cast_range",
                                               "dark_line_fraction", "dark_border_fraction"))}}
               for source, path in keys]
    source_rows = [{"source_dataset": source, "image_path": path, "sha256": source}
                   for source, path in keys]
    joined = join_quality_predictions(quality, predictions, view="raw", source_rows=source_rows)
    assert len(joined) == 2 and {r["source_dataset"] for r in joined} == {"A", "B"}
    assert all(r["correct"] == 1 and np.isfinite(r["predictive_entropy_normalized"]) for r in joined)
    assert sum(r["n"] for r in summarize_associations(joined, "brightness_mean")) == 2
    with pytest.raises(ValueError, match="Missing"):
        join_quality_predictions(quality[:1], predictions, view="raw")
    quality[0]["source_image_sha256"] = "wrong"
    with pytest.raises(ValueError, match="hash differs"):
        join_quality_predictions(quality, predictions, view="raw", source_rows=source_rows)


def test_missing_or_unapproved_evaluation_artifact_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_evaluation_artifact(tmp_path, tmp_path / "missing_split.csv",
                                     tmp_path / "missing_approval.json", tmp_path / "inventory.csv",
                                     tmp_path / "evaluation")
    for name in ("split.csv", "inventory.csv"):
        (tmp_path / name).write_text("image_path,source_dataset\n", encoding="utf-8")
    (tmp_path / "approval.json").write_text(json.dumps({"approval_status": "UNAPPROVED"}), encoding="utf-8")
    with pytest.raises(ValueError, match="approval"):
        validate_evaluation_artifact(tmp_path, tmp_path / "split.csv", tmp_path / "approval.json",
                                     tmp_path / "inventory.csv", tmp_path / "evaluation")


def _approved_iqa_row(class_index, split, source_split=""):
    return {"image_path": f"synthetic/{class_index}_{split}.jpg",
            "source_dataset": "SYNTHETIC_TEST_ONLY",
            "class_name": CLASS_NAMES[class_index], "class_index": str(class_index),
            "source_split": source_split, "split": split, "sha256": "synthetic-hash",
            "provisional_eligibility_status": "APPROVED_ELIGIBLE"}


def test_iqa_select_rows_uses_approved_model_split_and_excludes_calibration_test(monkeypatch, tmp_path):
    rows = []
    for index in range(len(CLASS_NAMES)):
        rows.extend((_approved_iqa_row(index, "train"),
                     _approved_iqa_row(index, "validation"),
                     _approved_iqa_row(index, "calibration", "train"),
                     _approved_iqa_row(index, "test", "train")))
    provenance = {"split_sha256": "split-hash", "inventory_sha256": "inventory-hash",
                  "approval_sha256": "approval-hash", "split_protocol": "four_way_v1",
                  "approval": {"approval_status": "APPROVED_BY_RESEARCHER"}}
    calls = []

    def validate(root, split, approval, inventory):
        calls.append((root, split, approval, inventory))
        return rows, provenance

    monkeypatch.setattr(iqa, "validate_approved_split", validate)
    selected, returned_provenance = select_rows(
        tmp_path, tmp_path / "approved.csv", tmp_path / "approval.json",
        tmp_path / "inventory.csv", per_class=0)
    assert len(selected) == 2 * len(CLASS_NAMES)
    assert {row["split"] for row in selected} == {"train", "validation"}
    assert all(row["split"] not in ("calibration", "test") for row in selected)
    assert returned_provenance is provenance
    assert calls == [(tmp_path, tmp_path / "approved.csv", tmp_path / "approval.json",
                      tmp_path / "inventory.csv")]


@pytest.mark.parametrize("bad_split", [None, "", "unknown"])
def test_iqa_select_rows_rejects_missing_or_unknown_model_split(monkeypatch, tmp_path, bad_split):
    rows = [_approved_iqa_row(index, "train") for index in range(len(CLASS_NAMES))]
    if bad_split is None:
        rows[0].pop("split")
    else:
        rows[0]["split"] = bad_split
    provenance = {"split_sha256": "split-hash", "inventory_sha256": "inventory-hash",
                  "approval_sha256": "approval-hash", "split_protocol": "three_way_v1",
                  "approval": {"approval_status": "APPROVED_BY_RESEARCHER"}}
    monkeypatch.setattr(iqa, "validate_approved_split", lambda *_: (rows, provenance))
    with pytest.raises(ValueError, match="model split|Unknown"):
        select_rows(tmp_path, tmp_path / "split.csv", tmp_path / "approval.json",
                    tmp_path / "inventory.csv", per_class=1)


@pytest.mark.parametrize("approval_record, row_status", [
    ({"approval_status": "UNAPPROVED"}, "APPROVED_ELIGIBLE"),
    (None, "APPROVED_ELIGIBLE"),
    ({"approval_status": "APPROVED_BY_RESEARCHER"}, "NOT_APPROVED"),
])
def test_iqa_select_rows_rejects_unapproved_cohort_or_missing_approval(
        monkeypatch, tmp_path, approval_record, row_status):
    rows = [_approved_iqa_row(index, "train") for index in range(len(CLASS_NAMES))]
    rows[0]["provisional_eligibility_status"] = row_status
    provenance = {"split_sha256": "split-hash", "inventory_sha256": "inventory-hash",
                  "approval_sha256": "approval-hash", "split_protocol": "three_way_v1",
                  "approval": approval_record}
    monkeypatch.setattr(iqa, "validate_approved_split", lambda *_: (rows, provenance))
    with pytest.raises(ValueError, match="approval|Unapproved"):
        select_rows(tmp_path, tmp_path / "split.csv", tmp_path / "approval.json",
                    tmp_path / "inventory.csv", per_class=1)


def test_iqa_select_rows_with_real_approved_split_validator(tmp_path):
    inventory_path = tmp_path / "inventory.csv"
    split_path = tmp_path / "approved_split.csv"
    approval_path = tmp_path / "approval.json"
    partitions = ("train", "validation", "calibration", "test")
    inventory_rows = []
    split_rows = []
    record_index = 0
    for class_index, class_name in enumerate(CLASS_NAMES):
        for partition in partitions:
            relative_path = f"synthetic/{class_index}_{partition}.jpg"
            image_path = tmp_path / relative_path
            image_path.parent.mkdir(parents=True, exist_ok=True)
            pixels = np.random.default_rng(record_index).integers(
                0, 256, size=(16, 16, 3), dtype=np.uint8
            )
            encoded_ok, encoded = cv2.imencode(".jpg", pixels)
            assert encoded_ok
            image_path.write_bytes(encoded.tobytes())
            source_row = {field: "" for field in LOCKED_FIELDS}
            source_row.update({
                "image_path": relative_path,
                "source_dataset": "SYNTHETIC_TEST_ONLY",
                "original_label": class_name,
                "class_name": class_name,
                "class_index": str(class_index),
                "image_id": f"image-{record_index}",
                "lesion_id": f"lesion-{record_index}",
                "patient_id": f"patient-{record_index}",
                "source_split": "train",
                "sha256": file_sha256(image_path),
                "overlap_group": f"group-{record_index}",
                "duplicate_overlap_evidence_tier": "NONE_RECORDED",
            })
            inventory_rows.append(source_row)
            split_rows.append({
                **source_row,
                "provisional_eligibility_status": "APPROVED_ELIGIBLE",
                "split": partition,
            })
            record_index += 1

    with inventory_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOCKED_FIELDS)
        writer.writeheader()
        writer.writerows(inventory_rows)
    split_fields = (*LOCKED_FIELDS, "provisional_eligibility_status", "split")
    with split_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=split_fields)
        writer.writeheader()
        writer.writerows(split_rows)
    approval_path.write_text(json.dumps({
        "approval_status": "APPROVED_BY_RESEARCHER",
        "approved_by": "SYNTHETIC_TEST_ONLY",
        "approval_date_utc": "2000-01-01T00:00:00Z",
        "adjudication_reference": "SYNTHETIC_TEST_ONLY",
        "source_rights_reference": "SYNTHETIC_TEST_ONLY",
        "protected_test_policy_reference": "SYNTHETIC_TEST_ONLY",
        "split_protocol": "four_way_v1",
        "calibration_partition_frozen": True,
        "calibration_separate_from_model_selection": True,
        "approved_split_sha256": file_sha256(split_path),
        "source_inventory_sha256": file_sha256(inventory_path),
    }), encoding="utf-8")

    validated_rows, _ = validate_approved_split(
        tmp_path, split_path, approval_path, inventory_path
    )
    selected, provenance = select_rows(
        tmp_path, split_path, approval_path, inventory_path, per_class=0
    )
    assert len(validated_rows) == 4 * len(CLASS_NAMES)
    assert len(selected) == 2 * len(CLASS_NAMES)
    assert {row["split"] for row in selected} == {"train", "validation"}
    assert provenance["split_sha256"] == file_sha256(split_path)
    assert provenance["inventory_sha256"] == file_sha256(inventory_path)
    assert provenance["approval_sha256"] == file_sha256(approval_path)


def test_incompatible_evaluation_provenance_rejected(tmp_path, monkeypatch):
    cohort = [{"source_dataset": "SYNTHETIC", "image_path": "one.jpg",
               "class_index": "0", "split": "validation"}]
    provenance = {"split_sha256": "split-hash", "inventory_sha256": "inventory-hash",
                  "approval_sha256": "approval-hash", "approval": {"test_partition_frozen": False},
                  "test_has_all_classes": False}
    monkeypatch.setattr(performance, "validate_approved_split", lambda *_: (cohort, provenance))
    folder = tmp_path / "evaluation"
    folder.mkdir()
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"synthetic fixture, never torch-loaded")
    record = _prediction(("SYNTHETIC", "one.jpg"))
    with (folder / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(record))
        writer.writeheader()
        writer.writerow(record)
    metrics = {"split": "validation", "n_samples": 1, "accuracy": 1.0,
               "provenance": {"split_sha256": "split-hash", "inventory_sha256": "inventory-hash",
                              "approval_sha256": "approval-hash", "checkpoint_path": str(checkpoint),
                              "checkpoint_sha256": file_sha256(checkpoint)}}
    (folder / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    predictions, rows = validate_evaluation_artifact(tmp_path, tmp_path / "split.csv",
                                                      tmp_path / "approval.json", tmp_path / "inventory.csv", folder)
    assert len(predictions) == len(rows) == 1
    metrics["provenance"]["inventory_sha256"] = "wrong"
    (folder / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    with pytest.raises(ValueError, match="provenance"):
        validate_evaluation_artifact(tmp_path, tmp_path / "split.csv",
                                     tmp_path / "approval.json", tmp_path / "inventory.csv", folder)
    metrics["provenance"]["inventory_sha256"] = "inventory-hash"
    metrics["split"] = "test"
    (folder / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    with pytest.raises(ValueError, match="Protected test"):
        validate_evaluation_artifact(tmp_path, tmp_path / "split.csv",
                                     tmp_path / "approval.json", tmp_path / "inventory.csv", folder)
