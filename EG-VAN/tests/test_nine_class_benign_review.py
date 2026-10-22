"""Review workflow tests. Decisions are written only inside pytest temp directories."""

import hashlib
import json
import sys
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nine_class_benign_review import PLAN, QUEUE, ReviewStore, handler_for, safe_image_path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_path_resolution_and_pair_coverage(tmp_path):
    store = ReviewStore(ROOT, tmp_path / "ledger.csv", tmp_path / "summary.json")
    assert len(store.rows) == 429
    assert len(store.related) == 83
    assert sum(row["candidate_source"] == "HAM10000" for row in store.rows) == 355
    assert sum(row["candidate_source"] == "binary" for row in store.rows) == 74
    first = store.rows[0]
    assert safe_image_path(ROOT, first["binary_image_path"], store.allowed_images).is_file()
    assert safe_image_path(ROOT, first["candidate_path"], store.allowed_images).is_file()
    with pytest.raises(ValueError):
        safe_image_path(ROOT, "../outside.jpg", store.allowed_images)
    with pytest.raises(ValueError):
        safe_image_path(ROOT, "src/train.py", store.allowed_images)
    assert store.snapshot()["summary"]["remaining_source_test_blockers"] == 19


def test_decision_persistence_reopening_and_invalid_decisions(tmp_path):
    ledger, summary = tmp_path / "ledger.csv", tmp_path / "summary.json"
    store = ReviewStore(ROOT, ledger, summary)
    pair_id = store.rows[0]["candidate_pair_id"]
    before = ledger.read_bytes()
    with pytest.raises(ValueError):
        store.save_decision(pair_id, "MAYBE", "")
    with pytest.raises(ValueError):
        store.save_decision("missing", "DISTINCT", "")
    assert ledger.read_bytes() == before
    saved = store.save_decision(pair_id, "UNCERTAIN", "Needs full-resolution review")
    assert saved["review_status"] == "reviewed"
    assert saved["review_timestamp_utc"]
    reopened = ReviewStore(ROOT, ledger, summary)
    assert reopened.by_id[pair_id]["reviewer_decision"] == "UNCERTAIN"
    assert reopened.by_id[pair_id]["reviewer_notes"] == "Needs full-resolution review"
    assert reopened.snapshot()["summary"]["reviewed_pair_count"] == 1
    assert reopened.snapshot()["summary"]["unreviewed_pair_count"] == 428


def test_uncertain_is_reviewed_but_does_not_resolve_a_record(tmp_path):
    store = ReviewStore(ROOT, tmp_path / "ledger.csv", tmp_path / "summary.json")
    path = next(path for path, ids in store.related.items() if len(ids) == 1)
    pair_id = store.related[path][0]
    store.save_decision(pair_id, "UNCERTAIN", "Cannot tell from the available images")
    assert store.snapshot()["summary"]["reviewed_pair_count"] == 1
    assert store.snapshot()["summary"]["binary_records_all_relations_resolved"] == 0
    store.save_decision(pair_id, "DISTINCT", "Different visual structures")
    assert store.snapshot()["summary"]["binary_records_all_relations_resolved"] >= 1


def test_evidence_disagreement_is_separate_from_human_decision(tmp_path):
    ledger, summary = tmp_path / "ledger.csv", tmp_path / "summary.json"
    store = ReviewStore(ROOT, ledger, summary)
    pair_id = store.rows[0]["candidate_pair_id"]
    before = ledger.read_bytes()
    with pytest.raises(ValueError):
        store.save_feedback(pair_id, True, "")
    saved = store.save_feedback(pair_id, True, "Landmarks cover a background artifact only")
    assert saved["disagrees_with_automated_category"] == "true"
    assert ledger.read_bytes() == before
    reopened = ReviewStore(ROOT, ledger, summary)
    assert reopened.feedback_by_id[pair_id]["disagreement_reason"] == "Landmarks cover a background artifact only"
    assert reopened.by_id[pair_id]["review_status"] == "unreviewed"


def test_focused_order_and_independent_reviewer_separation(tmp_path):
    primary_hash = digest(ROOT / "analysis/nine_class_recovery/benign_pair_review_ledger.csv")
    ledger, summary = tmp_path / "identity_reviews_R2.csv", tmp_path / "identity_summary_R2.json"
    secondary = ReviewStore(ROOT, ledger, summary, reviewer_id="R2")
    assert secondary.feedback_path.name == "identity_evidence_feedback_R2.csv"
    snapshot = secondary.snapshot()
    assert len(snapshot["strong"]) == 83
    assert [r["source_split"] for r in snapshot["strong_records"][:19]] == ["test"] * 19
    assert snapshot["strong_records"][19]["image_path"] == "data/isic/data/train/benign/1169.jpg"
    assert all(r["source_split"] == "train" for r in snapshot["strong_records"][20:])
    assert "prior_human_decision" not in next(iter(snapshot["strong"].values()))
    first_id = next(iter(snapshot["strong"]))
    assert all(not row["reviewer_decision"] for row in snapshot["pairs"])
    with pytest.raises(ValueError):
        secondary.save_decision(first_id, "SAME_PHOTO", "too similar")
    secondary.save_decision(first_id, "SAME_PHOTO", "Matching lesion border and nearby hair pattern")
    reopened = ReviewStore(ROOT, ledger, summary, reviewer_id="R2")
    assert reopened.by_id[first_id]["reviewer_decision"] == "SAME_PHOTO"
    assert digest(ROOT / "analysis/nine_class_recovery/benign_pair_review_ledger.csv") == primary_hash


def test_source_audit_files_are_unchanged(tmp_path):
    source_files = (ROOT / PLAN, ROOT / QUEUE,
                    ROOT / "analysis/nine_class_similarity/candidates.csv",
                    ROOT / "analysis/nine_class_similarity/fingerprints.csv",
                    ROOT / "analysis/nine_class_overlap_review/review_decisions.csv",
                    ROOT / "analysis/nine_class_overlap_completion/proposed_binary_exclusions.csv")
    before = [digest(path) for path in source_files]
    store = ReviewStore(ROOT, tmp_path / "ledger.csv", tmp_path / "summary.json")
    store.save_decision(store.rows[0]["candidate_pair_id"], "DISTINCT", "test-only decision")
    assert [digest(path) for path in source_files] == before


def test_local_http_page_image_and_invalid_post(tmp_path):
    store = ReviewStore(ROOT, tmp_path / "ledger.csv", tmp_path / "summary.json")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(store))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert b"EG-VAN BENIGN pair review" in urlopen(base + "/").read()
        assert b"EG-VAN BENIGN pair review" in urlopen(base + "/strong").read()
        snapshot = json.load(urlopen(base + "/api/review"))
        assert snapshot["summary"]["unreviewed_pair_count"] == 429
        assert len(snapshot["geometry"]) == 429
        image_path = store.rows[0]["binary_image_path"]
        assert urlopen(base + "/image/" + image_path).read(3) == b"\xff\xd8\xff"
        assert urlopen(base + "/landmarks/" + store.rows[0]["candidate_pair_id"]).read(3) == b"\xff\xd8\xff"
        assert urlopen(base + "/evidence/overlay/" + store.rows[0]["candidate_pair_id"]).read(3) == b"\xff\xd8\xff"
        request = Request(base + "/api/decision",
                          data=json.dumps({"pair_id": store.rows[0]["candidate_pair_id"],
                                           "decision": "INVALID"}).encode(),
                          headers={"Content-Type": "application/json"})
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 400
        assert store.snapshot()["summary"]["unreviewed_pair_count"] == 429
        bad_feedback = Request(base + "/api/evidence_feedback",
                               data=json.dumps({"pair_id": store.rows[0]["candidate_pair_id"],
                                                "disagrees": True, "reason": ""}).encode(),
                               headers={"Content-Type": "application/json"})
        with pytest.raises(HTTPError) as error:
            urlopen(bad_feedback)
        assert error.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

