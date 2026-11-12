"""Synthetic-only tests for metadata screening; no eligibility approval."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nine_class_metadata_screen import screen


def row(image, target, patient, lesion):
    return {"image_name": image, "target": str(target),
            "benign_malignant": "benign" if target == 0 else "malignant",
            "patient_id": patient, "lesion_id": lesion, "diagnosis": "unknown"}


def test_ham_id_and_official_duplicate_link_are_upper_bound_only():
    metadata = [row("ISIC_A", 0, "P1", "L1"), row("ISIC_B", 0, "P1", "L1"),
                row("ISIC_C", 0, "P2", "L2"), row("ISIC_D", 1, "P3", "L3")]
    duplicates = [{"image_name_1": "ISIC_A", "image_name_2": "ISIC_B"}]
    report = screen(metadata, duplicates, [{"image_id": "ISIC_A"}])
    assert report["direct_ham_image_id_overlap_benign"] == 1
    assert report["ham_id_or_official_duplicate_linked_benign"] == 2
    assert report["benign_not_ham_id_linked_records_upper_bound"] == 1
    assert report["benign_official_duplicate_components_upper_bound"] == 1
    assert report["approved_eligible_benign"] == 0
    assert report["four_way_split_approved"] is False


def test_metadata_conflicts_and_invalid_labels_are_not_silently_accepted():
    metadata = [row("ISIC_A", 0, "P1", "L1"), row("ISIC_B", 1, "P2", "L2")]
    duplicates = [{"image_name_1": "ISIC_A", "image_name_2": "ISIC_B"}]
    report = screen(metadata, duplicates, [{"image_id": "HAM_ONLY"}])
    assert report["official_duplicate_label_conflicts"] == 1
    assert report["official_duplicate_patient_id_conflicts"] == 1
    assert report["official_duplicate_lesion_id_conflicts"] == 1
    metadata[0]["target"] = "1"
    with pytest.raises(ValueError, match="conflicting"):
        screen(metadata, duplicates, [{"image_id": "HAM_ONLY"}])
    metadata[0]["target"] = "0"
    with pytest.raises(ValueError, match="absent"):
        screen(metadata, [{"image_name_1": "ISIC_A", "image_name_2": "MISSING"}],
               [{"image_id": "HAM_ONLY"}])
