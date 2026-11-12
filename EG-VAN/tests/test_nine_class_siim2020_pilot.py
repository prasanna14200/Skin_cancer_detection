"""Focused checks for the bounded, deterministic SIIM 2020 pilot."""

import csv
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nine_class_siim2020_pilot import duplicate_components, select, sha256


def example(image_id, patient, label="benign"):
    return {"image_name": image_id, "patient_id": patient, "lesion_id": "IL_" + image_id[-7:],
            "benign_malignant": label, "target": "0" if label == "benign" else "1", "diagnosis": "unknown"}


def test_selection_is_deterministic_and_excludes_duplicate_list_members():
    metadata = [example(f"ISIC_{i:07d}", f"IP_{i:07d}") for i in range(8)]
    metadata[2]["patient_id"] = metadata[3]["patient_id"]
    metadata[7] = example("ISIC_0000007", "IP_0000007", "malignant")
    duplicates = [{"image_name_1": "ISIC_0000000", "image_name_2": "ISIC_0000001"}]
    a = select(metadata, duplicates, seed=42, limit=4)
    b = select(list(reversed(metadata)), duplicates, seed=42, limit=4)
    assert a == b
    assert len({r["patient_id"] for r in a}) == 4
    assert not {r["image_id"] for r in a} & {"ISIC_0000000", "ISIC_0000001", "ISIC_0000007"}
    assert all(r["duplicate_component_size"] == 1 for r in a)
    assert all(r["original_label"] == "benign" and r["original_target"] == "0" for r in a)


def test_duplicate_components_preserve_membership_and_reject_unknown_ids():
    metadata = [example(f"ISIC_{i:07d}", f"IP_{i:07d}") for i in range(3)]
    duplicates = [{"image_name_1": "ISIC_0000000", "image_name_2": "ISIC_0000001"}]
    components, listed = duplicate_components(metadata, duplicates)
    assert components["ISIC_0000000"] == components["ISIC_0000001"] == ("ISIC_0000000", 2)
    assert listed == {"ISIC_0000000", "ISIC_0000001"}
    with pytest.raises(ValueError, match="missing metadata"):
        duplicate_components(metadata, [{"image_name_1": "ISIC_0000000", "image_name_2": "ISIC_9999999"}])


def test_frozen_real_manifest_matches_official_inputs():
    manifest = ROOT / "analysis/nine_class_siim2020_pilot/pilot_manifest.csv"
    if not manifest.exists():
        pytest.skip("Real pilot has not been frozen")
    with manifest.open(newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))
    assert len(records) == 100
    assert len({r["image_id"] for r in records}) == 100
    assert len({r["patient_id"] for r in records}) == 100
    assert all(r["official_duplicate_listed"] == "false" for r in records)
    assert {r["metadata_sha256"] for r in records} == {sha256(ROOT / "analysis/nine_class_dataset_recovery/ISIC_2020_Training_GroundTruth_v2.csv")}
    assert {r["duplicates_sha256"] for r in records} == {sha256(ROOT / "analysis/nine_class_dataset_recovery/ISIC_2020_Training_Duplicates.csv")}
