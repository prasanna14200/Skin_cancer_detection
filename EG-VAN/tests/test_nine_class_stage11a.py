"""Synthetic decision checks and read-only verification of the prepared review package."""

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nine_class_stage11a_review import (create_package, initial_ledger, original_image, sha256,
                                        read_csv, validate_decisions)


def sample_mapping():
    return [{"review_id": "R01", "binary_image_path": "a.jpg", "additional_candidate_relations": "0"},
            {"review_id": "R02", "binary_image_path": "b.jpg", "additional_candidate_relations": "3"}]


def test_blank_and_completed_decision_summary_never_approves():
    mapping = sample_mapping()
    ledger = initial_ledger(mapping)
    blank = validate_decisions(ledger, mapping)
    assert blank["reviewed_pairs"] == 0 and blank["unreviewed_pairs"] == 2
    assert not blank["dataset_approval_created"]
    ledger[0].update(reviewer_decision="DISTINCT_PHOTO", reviewer_identity_or_code="reviewer-X",
                     review_date_utc="2026-10-23T10:00:00Z", reviewer_notes="synthetic fixture")
    ledger[1].update(reviewer_decision="SAME_PHOTO", reviewer_identity_or_code="reviewer-X",
                     review_date_utc="2026-10-23T10:00:00+00:00")
    result = validate_decisions(ledger, mapping)
    assert result["reviewed_pairs"] == 2 and result["decision_counts"]["DISTINCT_PHOTO"] == 1
    assert result["remaining_primary_or_related_photo_review_blockers"] == 1
    assert all(not row["approved_eligible"] for row in result["records"])


@pytest.mark.parametrize("change,match", [
    ({"reviewer_decision": "DISTINCT"}, "Invalid reviewer decision"),
    ({"reviewer_decision": "SAME_PHOTO"}, "lacks reviewer"),
    ({"reviewer_notes": "looks similar"}, "Unreviewed row"),
    ({"image_a_identifier": "wrong"}, "identifiers changed"),
    ({"evidence_reference": "another.html"}, "evidence or identifiers changed"),
])
def test_invalid_or_partial_decision_rejected(change, match):
    ledger = initial_ledger(sample_mapping())
    ledger[0].update(change)
    with pytest.raises(ValueError, match=match):
        validate_decisions(ledger, sample_mapping())


def test_missing_utc_duplicate_and_unknown_ids_rejected():
    ledger = initial_ledger(sample_mapping())
    ledger[0].update(reviewer_decision="UNCERTAIN", reviewer_identity_or_code="X",
                     review_date_utc="2026-10-23")
    with pytest.raises(ValueError, match="must be UTC"):
        validate_decisions(ledger, sample_mapping())
    ledger[0]["review_date_utc"] = "2026-10-23T10:00:00+01:00"
    with pytest.raises(ValueError, match="must be UTC"):
        validate_decisions(ledger, sample_mapping())
    ledger[0]["review_date_utc"] = "2026-10-23T10:00:00Z"
    assert validate_decisions(ledger, sample_mapping())["reviewed_pairs"] == 1
    ledger[1] = ledger[0].copy()
    with pytest.raises(ValueError, match="exactly one row"):
        validate_decisions(ledger, sample_mapping())


def test_original_image_missing_or_hash_changed(tmp_path):
    with pytest.raises(ValueError, match="Missing or unsafe"):
        original_image(tmp_path, "missing.jpg", "x")
    path = tmp_path / "not-an-image.jpg"
    path.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="hash mismatch"):
        original_image(tmp_path, path.name, "wrong")


def test_real_package_is_blinded_and_source_references_resolve():
    package = ROOT / "analysis/nine_class_stage11a"
    mapping = read_csv(package / "review_id_mapping.csv")
    ledger = read_csv(package / "decision_ledger.csv")
    additional = read_csv(package / "additional_candidate_relations.csv")
    assert len(mapping) == len(ledger) == 19
    assert len({r["candidate_pair_id"] for r in mapping}) == 19
    assert len({r["binary_image_path"] for r in mapping}) == 19
    assert len(additional) == 101
    assert validate_decisions(ledger, mapping)["unreviewed_pairs"] == 19
    gallery = (package / "gallery.html").read_text(encoding="utf-8")
    assert "AI_SAME_PHOTO" not in gallery and "AI_DISTINCT" not in gallery
    assert 'option value=""' in gallery
    for row in mapping:
        assert (ROOT / row["binary_image_path"]).is_file()
        assert (ROOT / row["ham_image_path"]).is_file()
        assert f'originals/{row["review_id"]}-A.jpg' in gallery
        assert f'originals/{row["review_id"]}-B.jpg' in gallery
        assert sha256(package / "originals" / f'{row["review_id"]}-A.jpg') == row["binary_sha256"]
        assert sha256(package / "originals" / f'{row["review_id"]}-B.jpg') == row["ham_sha256"]
        assert row["binary_image_path"] not in gallery and row["ham_image_path"] not in gallery
    with pytest.raises(FileExistsError):
        create_package(ROOT)
