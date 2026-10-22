"""Geometric evidence tests use controlled images and read-only audit outputs."""

import csv
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nine_class_geometric_verification import (OUTPUT, VALIDATION, category,
                                               geometric_evidence, render_landmarks)


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_controlled_rotation_and_blank_failure():
    rng = np.random.default_rng(42)
    image = rng.integers(0, 255, size=(256, 256), dtype=np.uint8)
    rotated = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    good = geometric_evidence(image, rotated)
    assert good["geometry_status"] == "coherent"
    assert good["inlier_count"] >= 12
    blank = geometric_evidence(np.zeros((224, 224), np.uint8), np.zeros((224, 224), np.uint8))
    assert blank["geometry_status"] == "unreliable"
    assert category({"pixel_correlation": "0", "pixel_mae": "255"}, blank)[0] == "INSUFFICIENT_EVIDENCE"


def test_saved_evidence_covers_429_pairs_and_keeps_truth_separate():
    pairs = read_rows(ROOT / OUTPUT)
    validation = read_rows(ROOT / VALIDATION)
    assert len(pairs) == len({row["candidate_pair_id"] for row in pairs}) == 429
    assert set(row["automated_evidence_category"] for row in pairs) <= {
        "NEEDS_HUMAN_REVIEW", "INSUFFICIENT_EVIDENCE"}
    assert Counter(row["truth_status"] for row in validation) == {
        "controlled_same_source_photo": 160,
        "provisional_distinct_requires_independent_verification": 40,
        "verified_byte_identical_files": 1}
    dev = {r["source_image_path"] for r in validation if r["partition"] == "development"}
    hold = {r["source_image_path"] for r in validation if r["partition"] == "held_out"}
    assert len(dev) == len(hold) == 20 and not dev & hold
    coherent = next(row for row in pairs if row["geometry_status"] == "coherent")
    assert render_landmarks(ROOT, coherent)[:3] == b"\xff\xd8\xff"
