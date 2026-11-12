"""Focused integrity checks for nonapproval cohort planning evidence."""

import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nine_class_final_cohort import OUT, PILOT, assign_group_partitions, fp_array, variants
from nine_class_siim2020_pilot import sha256
from nine_class_similarity_audit import fingerprint
from nine_class_protocol import validate_approved_split


def test_transformed_fingerprints_keep_native_implementation(tmp_path):
    rng = np.random.default_rng(42)
    pixels = rng.integers(0, 256, (100, 120), dtype=np.uint8)
    path = tmp_path / "fixture.jpg"
    assert cv2.imwrite(str(path), pixels)
    decoded = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    assert fp_array(variants(decoded)["native"]) == fingerprint(path)
    assert set(variants(decoded)) == {"native", "rotate90", "rotate180", "rotate270",
                                       "horizontal_flip", "center_crop80"}


def test_frozen_candidate_plan_retains_pilot_and_patient_uniqueness():
    with (OUT / "candidate_manifest_v2.csv").open(newline="", encoding="utf-8") as file:
        candidate = list(csv.DictReader(file))
    with (PILOT / "pilot_manifest.csv").open(newline="", encoding="utf-8") as file:
        pilot = list(csv.DictReader(file))
    plan = json.loads((OUT / "candidate_selection_record_v2.json").read_text())
    assert len(candidate) == 1200
    assert len({r["patient_id"] for r in candidate}) == 1200
    assert [r["image_id"] for r in candidate[:100]] == [r["image_id"] for r in pilot]
    assert all(r["duplicate_component_size"] == "1" and r["original_label"] == "benign"
               for r in candidate)
    assert all(r["acquisition_status"] == "PLANNED_NOT_ACQUIRED" for r in candidate[100:])
    assert "ISIC_3746471" not in {r["image_id"] for r in candidate}
    assert all(r["review_status"] == "UNREVIEWED" for r in candidate)
    assert plan["candidate_manifest_sha256"] == sha256(OUT / "candidate_manifest_v2.csv")


def test_pilot_rescreen_quarantines_without_approval():
    with (OUT / "pilot84_rescreen_outcomes.csv").open(newline="", encoding="utf-8") as file:
        outcomes = list(csv.DictReader(file))
    assert len(outcomes) == 84
    assert all(r["approval_status"] == "NOT_APPROVED" for r in outcomes)
    assert sum(r["screen_status"] == "QUARANTINE_REVIEW" for r in outcomes) == 48
    assert sum(r["screen_status"] == "NO_CANDIDATE_STRONGER_SCREEN" for r in outcomes) == 36


def test_four_way_planning_keeps_known_groups_and_source_test_boundary():
    names = ("AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT")
    groups = {f"g-{name}-{i}": [{"class_name": name, "source_split": "test" if name == "MALIGNANT" and i == 0 else ""}]
              for name in names for i in range(20)}
    groups["g-shared"] = [{"class_name": "BENIGN", "source_split": ""},
                          {"class_name": "NV", "source_split": ""}]
    first = assign_group_partitions(groups)
    assert first == assign_group_partitions(groups)
    assert first["g-MALIGNANT-0"] == "test"
    assert set(first.values()) == {"train", "validation", "calibration", "test"}
    assert len(first) == len(groups)


def test_real_four_way_preview_is_unapproved_and_group_safe():
    report = json.loads((OUT / "four_way_feasibility_report_v1.json").read_text())
    with (OUT / "four_way_planning_assignment_v1.csv").open(newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))
    assert report["status"] == "PLANNING_ONLY_NOT_APPROVED"
    assert report["approved_rows"] == 0
    assert report["known_group_crossings"] == 0
    assert report["source_test_violations"] == []
    assert len(records) == report["planning_inventory_rows"]
    assert all(r["approval_status"] == "NOT_APPROVED" for r in records)
    partitions = {}
    for row in records:
        partitions.setdefault(row["overlap_group"], set()).add(row["proposed_partition"])
        if row["source_split"] == "test":
            assert row["proposed_partition"] == "test"
    assert all(len(value) == 1 for value in partitions.values())
    assert report["counts"]["test"]["BENIGN"] < 40


def test_stage6_gate_rejects_planning_preview_even_with_synthetic_approval(tmp_path):
    split = OUT / "four_way_planning_assignment_v1.csv"
    inventory = OUT / "four_way_planning_inventory_v1.csv"
    approval = tmp_path / "synthetic_approval.json"
    approval.write_text(json.dumps({
        "synthetic_fixture": True, "approval_status": "APPROVED_BY_RESEARCHER",
        "approved_by": "SYNTHETIC_TEST_ONLY", "approval_date_utc": "2000-01-01T00:00:00Z",
        "adjudication_reference": "SYNTHETIC_TEST_ONLY", "source_rights_reference": "SYNTHETIC_TEST_ONLY",
        "protected_test_policy_reference": "SYNTHETIC_TEST_ONLY",
        "approved_split_sha256": sha256(split), "source_inventory_sha256": sha256(inventory)}))
    with pytest.raises(ValueError, match="schema incomplete"):
        validate_approved_split(ROOT, split, approval, inventory, allow_synthetic_fixture=True)
