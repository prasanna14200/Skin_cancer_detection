"""Stage 3G generated evidence and blind workflow checks."""

import csv
import hashlib
import json
import sys
import threading
from collections import Counter
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nine_class_blinded_validation_review import BlindStore, handler_for
from nine_class_stage3g_verification import OUTPUT, analyze_pair
from nine_class_benign_review import LEDGER
from nine_class_geometric_verification import OUTPUT as GEOMETRY
from nine_class_benign_review import read_csv


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_83_reports_and_visualizations_exist():
    rows = read_csv(ROOT / OUTPUT / "strong_pair_identity_evidence.csv")
    assert len(rows) == len({r["candidate_pair_id"] for r in rows}) == 83
    assert Counter(r["source_partition"] for r in rows) == {"test": 19, "train": 64}
    assert all(r["binary_image_path"].startswith("data/isic/data/") for r in rows)
    assert all(r["ham_candidate_path"].startswith("data/raw/HAM10000_images_part_") for r in rows)
    assert all(r["lesion_structure_match_status"] == "not_independently_verified_no_lesion_mask" for r in rows)
    assert all(r["identity_conclusion_status"] not in {"VERIFIED_SAME_PHOTO", "VERIFIED_DISTINCT"} for r in rows)
    for row in rows:
        for field in ("overlay_reference", "difference_reference", "landmark_reference"):
            assert (ROOT / row[field]).is_file()
    assert len(list((ROOT / OUTPUT / "overlays").glob("*.jpg"))) == 83
    assert len(list((ROOT / OUTPUT / "differences").glob("*.jpg"))) == 83
    gallery = (ROOT / OUTPUT / "strong_pair_gallery.html").read_text(encoding="utf-8")
    assert gallery.count("<article id=\"pair-") == 83
    assert "../../../data/isic/data/test/benign/802.jpg" in gallery


def test_recompute_one_pair_without_touching_sources():
    pair = read_csv(ROOT / OUTPUT / "strong_pair_identity_evidence.csv")[0]
    geometry = {r["candidate_pair_id"]: r for r in read_csv(ROOT / GEOMETRY)}[pair["candidate_pair_id"]]
    human = {r["candidate_pair_id"]: r for r in read_csv(ROOT / LEDGER)}[pair["candidate_pair_id"]]
    paths = [ROOT / human["binary_image_path"], ROOT / human["candidate_path"], ROOT / LEDGER]
    before = [digest(p) for p in paths]
    metrics, images = analyze_pair(ROOT, human, geometry)
    assert float(pair["aligned_grayscale_mae_8bit"]) == metrics["aligned_grayscale_mae_8bit"]
    assert all(data[:3] == b"\xff\xd8\xff" for data in images.values())
    assert [digest(p) for p in paths] == before


def test_blind_cases_hide_metadata_and_save_separately(tmp_path):
    ledger = tmp_path / "blind_r1.csv"
    source_paths = (ROOT / OUTPUT / "blinded_validation_queue.csv", ROOT / LEDGER)
    source_hashes = [digest(path) for path in source_paths]
    store = BlindStore("R1", ROOT, ledger)
    assert store.snapshot()["reviewed"] == 0
    assert len(store.snapshot()["cases"]) == 40
    assert "source_image_path" not in store.snapshot()["cases"][0]
    assert "metadata_relation_status" not in store.snapshot()["cases"][0]
    case_id = store.snapshot()["cases"][0]["blind_case_id"]
    assert store.image(case_id, "a").is_file()
    with pytest.raises(ValueError):
        store.image("unknown", "a")
    with pytest.raises(ValueError):
        store.save(case_id, "MAYBE", "")
    store.save(case_id, "UNCERTAIN", "Need another independent view")
    reopened = BlindStore("R1", ROOT, ledger)
    assert reopened.snapshot()["reviewed"] == 1
    assert reopened.by_id[case_id]["reviewer_decision"] == "UNCERTAIN"
    assert all(not row["reviewer_decision"] for row in reopened.rows[1:])
    assert [digest(path) for path in source_paths] == source_hashes


def test_blind_http_does_not_expose_mapping(tmp_path):
    store = BlindStore("R2", ROOT, tmp_path / "blind_r2.csv")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(store))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        raw = urlopen(base + "/api/cases").read()
        assert b"source_image_path" not in raw and b"lesion_id" not in raw
        case_id = store.snapshot()["cases"][0]["blind_case_id"]
        assert urlopen(base + "/image/" + case_id + "/a").read(3) == b"\xff\xd8\xff"
        request = Request(base + "/api/decision",
                          data=json.dumps({"case_id": case_id, "decision": "INVALID"}).encode(),
                          headers={"Content-Type": "application/json"})
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
