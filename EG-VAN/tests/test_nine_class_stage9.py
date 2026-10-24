"""Synthetic external-manifest, overlap, checkpoint and subset-evaluation tests."""

import csv
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import nine_class_external_evaluation as external_eval
from nine_class_dataset import PreprocessConfig
from nine_class_external_evaluation import (compare_evaluation_reports, compare_internal_external, evaluate_external,
                                             external_metrics, preprocessing_hash)
from nine_class_external_protocol import (MANIFEST_FIELDS, read_csv, screen_external,
                                          validate_approved_external, validate_manifest_schema)
from nine_class_protocol import file_sha256
from nine_class_similarity_audit import fingerprint
from nine_class_stage4 import CLASS_NAMES


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def image_fixture(tmp_path):
    internal = tmp_path / "internal"
    external = tmp_path / "external"
    internal.mkdir()
    external.mkdir()
    rng = np.random.default_rng(11)
    array = rng.integers(0, 255, (64, 64, 3), dtype=np.uint8)
    assert cv2.imwrite(str(internal / "internal.png"), array)
    shutil.copyfile(internal / "internal.png", external / "exact.png")
    assert cv2.imwrite(str(external / "similar.jpg"), array, [cv2.IMWRITE_JPEG_QUALITY, 93])
    assert cv2.imwrite(str(external / "distinct.png"), rng.integers(0, 255, (64, 64, 3), dtype=np.uint8))
    inventory = tmp_path / "internal_inventory.csv"
    write_csv(inventory, ("image_path", "source_dataset", "sha256", "patient_id", "lesion_id"),
              [{"image_path": "internal.png", "source_dataset": "SYNTHETIC_INTERNAL",
                "sha256": file_sha256(internal / "internal.png"), "patient_id": "", "lesion_id": ""}])
    phash, dhash = fingerprint(internal / "internal.png")
    fingerprints = tmp_path / "internal_fingerprints.csv"
    write_csv(fingerprints, ("image_path", "phash64", "dhash64"),
              [{"image_path": "internal.png", "phash64": f"{phash:016x}", "dhash64": f"{dhash:016x}"}])
    return internal, external, inventory, fingerprints


def manifest_row(external, filename, *, target="BKL", mapping="EXACT", eligibility="UNREVIEWED"):
    row = {field: "" for field in MANIFEST_FIELDS}
    row.update(source_dataset="SYNTHETIC_EXTERNAL", source_version="fixture-v1",
               image_path=filename, original_clinical_label="synthetic-label", target_label=target,
               mapping_status=mapping, mapping_justification="synthetic test mapping only",
               sha256=file_sha256(external / filename), source_license="synthetic test only",
               permitted_use_status="PERMITTED_FOR_RESEARCH_EVALUATION",
               overlap_status="UNREVIEWED", eligibility_status=eligibility)
    return row


def approval_file(tmp_path, manifest, overlap_report, inventory):
    approval = tmp_path / "external_approval.json"
    approval.write_text(json.dumps({"synthetic_fixture": True,
        "approval_status": "APPROVED_EXTERNAL_EVALUATION", "external_test_frozen": True,
        "approved_by": "SYNTHETIC_TEST_ONLY", "approval_date_utc": "2000-01-01T00:00:00Z",
        "label_mapping_reference": "SYNTHETIC_TEST_ONLY", "overlap_review_reference": "SYNTHETIC_TEST_ONLY",
        "source_rights_reference": "SYNTHETIC_TEST_ONLY",
        "preprocessing_protocol_reference": "SYNTHETIC_TEST_ONLY",
        "unknown_identity_limitation_acknowledged": True,
        "approved_external_manifest_sha256": file_sha256(manifest),
        "overlap_report_sha256": file_sha256(overlap_report),
        "internal_inventory_sha256": file_sha256(inventory),
        "checkpoint_sha256": "synthetic-checkpoint",
        "preprocess_config_sha256": "synthetic-preprocess"}), encoding="utf-8")
    return approval


def test_manifest_schema_unknown_identifiers_and_mapping_rejection(tmp_path):
    _, external, _, _ = image_fixture(tmp_path)
    row = manifest_row(external, "distinct.png")
    assert row["patient_id"] == row["lesion_id"] == row["source_image_id"] == ""
    validate_manifest_schema([row])
    with pytest.raises(ValueError, match="Duplicate"):
        validate_manifest_schema([row, row])
    row["mapping_status"] = "MADE_UP"
    with pytest.raises(ValueError, match="mapping"):
        validate_manifest_schema([row])


def test_exact_and_perceptual_screen_and_no_independence_claim(tmp_path):
    _, external, inventory, fingerprints = image_fixture(tmp_path)
    rows = [manifest_row(external, name) for name in ("exact.png", "similar.jpg", "distinct.png")]
    manifest = tmp_path / "external_manifest.csv"
    write_csv(manifest, MANIFEST_FIELDS, rows)
    report = screen_external(external, manifest, inventory, fingerprints, tmp_path / "screen")
    by_path = {r["image_path"]: r for r in report["rows"]}
    assert by_path["exact.png"]["screen_status"] == "EXACT_HASH_OVERLAP"
    assert by_path["similar.jpg"]["screen_status"] == "POSSIBLE_PHOTO_OVERLAP"
    assert by_path["distinct.png"]["screen_status"] == "NO_CANDIDATE_FOUND_IDENTITY_UNKNOWN"
    assert all(not r["patient_independence_verified"] for r in report["rows"])
    assert any(r["match_type"] == "PERCEPTUAL_CANDIDATE" for r in
               csv.DictReader((tmp_path / "screen/overlap_candidates.csv").open(newline="", encoding="utf-8")))
    with pytest.raises(FileExistsError):
        screen_external(external, manifest, inventory, fingerprints, tmp_path / "screen")


def test_approval_rejects_exact_suspected_and_unsupported(tmp_path):
    _, external, inventory, fingerprints = image_fixture(tmp_path)
    row = manifest_row(external, "exact.png", eligibility="APPROVED_EXTERNAL_EVALUATION")
    manifest = tmp_path / "external_manifest.csv"
    write_csv(manifest, MANIFEST_FIELDS, [row])
    screen_external(external, manifest, inventory, fingerprints, tmp_path / "screen_exact")
    report = tmp_path / "screen_exact/overlap_report.json"
    approval = approval_file(tmp_path, manifest, report, inventory)
    with pytest.raises(ValueError, match="Synthetic approval"):
        validate_approved_external(external, manifest, approval, report, inventory,
                                   "synthetic-checkpoint", "synthetic-preprocess")
    with pytest.raises(ValueError, match="Known internal/external overlap"):
        validate_approved_external(external, manifest, approval, report, inventory,
                                   "synthetic-checkpoint", "synthetic-preprocess",
                                   allow_synthetic_fixture=True)
    row = manifest_row(external, "similar.jpg", eligibility="APPROVED_EXTERNAL_EVALUATION")
    write_csv(manifest, MANIFEST_FIELDS, [row])
    screen_external(external, manifest, inventory, fingerprints, tmp_path / "screen_similar")
    report = tmp_path / "screen_similar/overlap_report.json"
    approval_file(tmp_path, manifest, report, inventory)
    with pytest.raises(ValueError, match="Suspected photographic overlap"):
        validate_approved_external(external, manifest, approval, report, inventory,
                                   "synthetic-checkpoint", "synthetic-preprocess",
                                   allow_synthetic_fixture=True)
    row["overlap_status"] = "REVIEWED_DISTINCT"
    row["overlap_decision_reference"] = "synthetic reviewer fixture"
    row["mapping_status"] = "UNSUPPORTED"
    write_csv(manifest, MANIFEST_FIELDS, [row])
    screen_external(external, manifest, inventory, fingerprints, tmp_path / "screen_unsupported")
    report = tmp_path / "screen_unsupported/overlap_report.json"
    approval_file(tmp_path, manifest, report, inventory)
    with pytest.raises(ValueError, match="Unsupported"):
        validate_approved_external(external, manifest, approval, report, inventory,
                                   "synthetic-checkpoint", "synthetic-preprocess",
                                   allow_synthetic_fixture=True)


def test_subset_metrics_and_compatibility_comparison():
    probabilities = np.eye(9)[[0, 1]]
    metrics = external_metrics(probabilities, np.array([0, 1]), ["AKIEC", "BCC"])
    assert metrics["scope"] == "supported_label_subset"
    assert metrics["full_nine_accuracy"] is None and metrics["subset_accuracy"] == 1
    assert metrics["per_class"]["MALIGNANT"]["support"] == 0 and metrics["warnings"]
    assert metrics["calibration"] is None
    assert not compare_internal_external({"scope": "full_nine_class"}, metrics)["comparable"]
    full = {"scope": "full_nine_class", "supported_classes": list(CLASS_NAMES),
            "preprocess_config_sha256": "same", "source_dataset": "A", "accuracy": 0.8,
            "macro_f1": 0.7, "per_class_recall": {name: 0.7 for name in CLASS_NAMES}}
    other = {**full, "source_dataset": "B", "accuracy": 0.6}
    result = compare_internal_external(full, other)
    assert result["comparable"] and result["metric_changes_external_minus_internal"]["accuracy"] == pytest.approx(-0.2)
    internal_metrics = {"split": "test", "all_nine_classes_present": True,
                        "accuracy": 0.8, "macro_f1": 0.7,
                        "per_class": {name: {"recall": 0.7} for name in CLASS_NAMES},
                        "provenance": {"checkpoint_sha256": "checkpoint", "config_sha256": "config"}}
    run_info = {"config_sha256": "config",
                "preprocess_config_sha256": preprocessing_hash(PreprocessConfig()),
                "config": {"label_order": list(CLASS_NAMES), "image_size": 384}}
    external_report = {"scope": "full_nine_class", "supported_classes": list(CLASS_NAMES),
                       "preprocess_config_sha256": preprocessing_hash(PreprocessConfig()),
                       "full_nine_accuracy": 0.6, "macro_f1_supported": 0.5,
                       "per_class": {name: {"recall": 0.5} for name in CLASS_NAMES},
                       "provenance": {"checkpoint_sha256": "checkpoint"},
                       "source_dataset_versions": [["SYNTHETIC", "v1"]]}
    comparison = compare_evaluation_reports(internal_metrics, external_report, run_info)
    assert comparison["comparable"] and comparison["metric_changes_external_minus_internal"]["accuracy"] == pytest.approx(-0.2)
    external_report["mapping_status_counts"] = {"CLINICALLY_JUSTIFIED_NONIDENTICAL": 1}
    assert not compare_evaluation_reports(internal_metrics, external_report, run_info)["comparable"]
    assert compare_evaluation_reports(internal_metrics, external_report, run_info,
                                      mapping_comparability_reference="synthetic review")["comparable"]
    external_report["mapping_status_counts"] = {}
    external_report["scope"] = "supported_label_subset"
    assert not compare_evaluation_reports(internal_metrics, external_report, run_info)["comparable"]


def test_frozen_runner_tiny_synthetic_model_and_no_raw_change(tmp_path, monkeypatch):
    external = tmp_path / "external"
    external.mkdir()
    array = np.full((32, 32, 3), 100, dtype=np.uint8)
    image = external / "one.png"
    assert cv2.imwrite(str(image), array)
    before = file_sha256(image)
    row = manifest_row(external, image.name, eligibility="APPROVED_EXTERNAL_EVALUATION")
    row["overlap_status"] = "NO_KNOWN_OVERLAP_AFTER_REVIEW"
    internal_prov = {"split_sha256": "split", "inventory_sha256": "inventory",
                     "approval_sha256": "approval"}
    monkeypatch.setattr(external_eval, "validate_approved_split", lambda *a, **k: ([], internal_prov))
    monkeypatch.setattr(external_eval, "validate_approved_external",
                        lambda *a, **k: ([row], {"supported_classes": ["BKL"],
                                          "manifest_sha256": "synthetic", "approval_sha256": "synthetic"}))

    class Tiny(nn.Module):
        def __init__(self):
            super().__init__()
            self.head = nn.Linear(3, 9)

        def forward(self, images):
            assert not self.training and not torch.is_grad_enabled()
            return self.head(images.mean(dim=(2, 3)))

    torch.manual_seed(7)
    model = Tiny()
    checkpoint_dir = tmp_path / "run"
    checkpoint_dir.mkdir()
    checkpoint = checkpoint_dir / "best.pt"
    preprocess_sha = preprocessing_hash(PreprocessConfig(image_size=384))
    torch.save({"model_state": model.state_dict(), "epoch": 1, "config_sha256": "config",
                "split_sha256": "split", "inventory_sha256": "inventory",
                "approval_sha256": "approval", "preprocess_config_sha256": preprocess_sha}, checkpoint)
    (checkpoint_dir / "run_provenance.json").write_text(json.dumps({"config_sha256": "config",
        "split_sha256": "split", "inventory_sha256": "inventory", "approval_sha256": "approval",
        "preprocess_config_sha256": preprocess_sha,
        "config": {"label_order": list(CLASS_NAMES), "image_size": 384, "fusion_channels": 128}}), encoding="utf-8")
    output = tmp_path / "output"
    report = evaluate_external(tmp_path, tmp_path / "internal_split.csv", tmp_path / "internal_approval.json",
                               tmp_path / "internal_inventory.csv", external, tmp_path / "external_manifest.csv",
                               tmp_path / "external_approval.json", tmp_path / "overlap_report.json",
                               checkpoint, output, batch_size=1, model_factory=lambda _: Tiny(),
                               allow_synthetic_fixture=True)
    assert report["scope"] == "supported_label_subset" and report["full_nine_accuracy"] is None
    exported = list(csv.DictReader((output / "external_predictions.csv").open(newline="", encoding="utf-8")))
    assert len(exported) == 1 and exported[0]["source_image_key"] == "SYNTHETIC_EXTERNAL:fixture-v1:one.png"
    assert [name for name in CLASS_NAMES if f"prob_{name}" in exported[0]] == list(CLASS_NAMES)
    assert file_sha256(image) == before
    assert preprocessing_hash(PreprocessConfig(image_size=384)) == report["preprocess_config_sha256"]
    with pytest.raises(FileExistsError):
        evaluate_external(tmp_path, tmp_path / "internal_split.csv", tmp_path / "internal_approval.json",
                          tmp_path / "internal_inventory.csv", external, tmp_path / "external_manifest.csv",
                          tmp_path / "external_approval.json", tmp_path / "overlap_report.json",
                          checkpoint, output, model_factory=lambda _: Tiny(), allow_synthetic_fixture=True)
    run_info_path = checkpoint_dir / "run_provenance.json"
    run_info = json.loads(run_info_path.read_text(encoding="utf-8"))
    run_info["config"]["label_order"] = list(reversed(CLASS_NAMES))
    run_info_path.write_text(json.dumps(run_info), encoding="utf-8")
    with pytest.raises(ValueError, match="label order"):
        evaluate_external(tmp_path, tmp_path / "internal_split.csv", tmp_path / "internal_approval.json",
                          tmp_path / "internal_inventory.csv", external, tmp_path / "external_manifest.csv",
                          tmp_path / "external_approval.json", tmp_path / "overlap_report.json",
                          checkpoint, tmp_path / "invalid_order", model_factory=lambda _: Tiny(),
                          allow_synthetic_fixture=True)
    assert not (tmp_path / "invalid_order").exists()
