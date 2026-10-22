"""Reconciliation tests use synthetic temporary ledgers, never production reviews."""

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nine_class_benign_review import read_csv
from nine_class_blinded_validation_review import BlindStore, QUEUE
from nine_class_validation_reconcile import reconcile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_reconciliation_requires_two_complete_independent_reviews(tmp_path):
    queue = ROOT / QUEUE
    original_hash = digest(queue)
    first = BlindStore("R1", ROOT, tmp_path / "r1.csv")
    second = BlindStore("R2", ROOT, tmp_path / "r2.csv")
    output = tmp_path / "reconciled"
    with pytest.raises(ValueError, match="incomplete"):
        reconcile(queue, first.ledger, second.ledger, output)
    assert not output.exists()
    for row in first.rows:
        first.save(row["blind_case_id"], "DISTINCT", "Synthetic test fixture")
    with pytest.raises(ValueError, match="incomplete"):
        reconcile(queue, first.ledger, second.ledger, output)
    assert not output.exists()
    for row in second.rows:
        second.save(row["blind_case_id"], "DISTINCT", "Synthetic test fixture")
    case_id = second.rows[0]["blind_case_id"]
    with pytest.raises(ValueError, match="explanation"):
        second.save(case_id, "SAME_PHOTO", "short")
    second.save(case_id, "SAME_PHOTO", "Synthetic test fixture for separate reconciliation")
    source_hashes = tuple(digest(p) for p in (queue, first.ledger, second.ledger))
    summary = reconcile(queue, first.ledger, second.ledger, output)
    assert summary["cases"] == 40
    assert summary["status_counts"] == {
        "UNRESOLVED_DISAGREEMENT": 1,
        "AGREEMENT_REQUIRES_SOURCE_CHECK": 39,
    }
    assert not summary["detector_error_metrics_available"]
    rows = read_csv(output / "validation_reconciliation.csv")
    assert rows[0]["reconciliation_status"] == "UNRESOLVED_DISAGREEMENT"
    assert "source_image_path" not in rows[0]
    adjudications = read_csv(output / "validation_adjudication.csv")
    assert len(adjudications) == 40
    assert all(not row["final_adjudication"] for row in adjudications)
    assert tuple(digest(p) for p in (queue, first.ledger, second.ledger)) == source_hashes
    with pytest.raises(FileExistsError):
        reconcile(queue, first.ledger, second.ledger, output)
    assert digest(queue) == original_hash


def test_blind_reviewers_do_not_see_each_others_decisions(tmp_path):
    first = BlindStore("R1", ROOT, tmp_path / "r1.csv")
    second = BlindStore("R2", ROOT, tmp_path / "r2.csv")
    case_id = first.rows[0]["blind_case_id"]
    first.save(case_id, "UNCERTAIN", "Synthetic test fixture")
    assert second.snapshot()["reviewed"] == 0
    assert second.by_id[case_id]["reviewer_decision"] == ""
    assert "reviewer_a_decision" not in second.snapshot()["cases"][0]
