"""Read-only checks of frozen AI annotations and untouched original evidence."""

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nine_class_stage3i_review import freeze

BASE = ROOT / "analysis/nine_class_recovery/stage3i"


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_pairs_have_one_visual_ai_review_and_valid_evidence():
    reviewed = rows(BASE / "ai_pair_review.csv")
    queue = rows(ROOT / "analysis/nine_class_recovery/benign_pair_review_ledger.csv")
    manifest = rows(BASE / "sheet_manifest.csv")
    assert len(reviewed) == len(manifest) == 429
    assert len({r["candidate_pair_id"] for r in reviewed}) == 429
    assert {r["candidate_pair_id"] for r in reviewed} == {r["candidate_pair_id"] for r in queue}
    assert [int(r["review_order"]) for r in reviewed] == list(range(1, 430))
    assert Counter(r["ai_assessment"] for r in reviewed) == {
        "AI_SAME_PHOTO": 83, "AI_DISTINCT": 326, "AI_UNCERTAIN": 20,
    }
    assert all(r["human_decision_used"] == "no" for r in reviewed)
    assert all(r["review_method"].startswith("AI visual inspection") for r in reviewed)
    assert all(r["review_timestamp_utc"] and r["prompt_configuration_version"] for r in reviewed)
    for record, source in zip(reviewed, manifest, strict=True):
        assert record["candidate_pair_id"] == source["candidate_pair_id"]
        assert (ROOT / record["contact_sheet_reference"]).is_file()
        assert record["original_binary_sha256"] == source["binary_sha256"]
        assert record["original_candidate_sha256"] == source["candidate_sha256"]
        assert (ROOT / record["binary_image_path"]).is_file()
        assert (ROOT / record["candidate_path"]).is_file()
        assert digest(ROOT / record["binary_image_path"]) == source["binary_sha256"]
        assert digest(ROOT / record["candidate_path"]) == source["candidate_sha256"]
        assert record["evidence_summary"] and record["visual_landmarks"]
    assert all((ROOT / r["stage3g_overlay_reference"]).is_file() for r in reviewed[:83])
    assert all(not r["stage3g_overlay_reference"] for r in reviewed[83:])


def test_source_hashes_unchanged_and_group_tiers_are_explicit():
    summary = json.loads((BASE / "review_summary.json").read_text(encoding="utf-8"))
    assert summary["visually_inspected_from_original_image_sheets"] == 429
    assert summary["numerical_only_assessments"] == 0
    assert not summary["prior_human_choices_copied_or_modified"]
    assert not summary["clinical_patient_lesion_identity_verified"]
    assert not summary["stage4_split_ready"]
    for relative, expected in summary["prior_source_evidence_sha256"].items():
        assert digest(ROOT / relative) == expected
    edges = rows(BASE / "proposed_overlap_edges.csv")
    groups = rows(BASE / "proposed_overlap_groups.csv")
    assert len(edges) == summary["overlap_edge_count"]
    assert {e["evidence_tier"] for e in edges} == {
        "PRIOR_ESTABLISHED_PHOTO_RELATION", "AI_SUPPORTED_SAME_PHOTO",
        "SUSPECTED_UNRESOLVED_OVERLAP",
    }
    assert len({r["proposed_group_id"] for r in groups}) == summary["proposed_overlap_group_count"]
    assert {path for e in edges for path in (e["path_a"], e["path_b"])} == {
        r["member_path"] for r in groups}


def test_freeze_refuses_to_overwrite_ai_evidence():
    before = digest(BASE / "ai_pair_review.csv")
    with pytest.raises(FileExistsError):
        freeze(ROOT)
    assert digest(BASE / "ai_pair_review.csv") == before
