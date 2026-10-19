import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nine_class_overlap_completion import classify_full, coarse_evidence, full_review_needed
from nine_class_overlap_review import duplicate_groups, exclusion_reasons


def test_coarse_identical_and_distinct():
    x = np.arange(4096, dtype=np.uint8).reshape(64, 64)
    mae, correlation, gradient = coarse_evidence(x, x.copy())
    assert mae == 0 and correlation > .999 and gradient > .999
    assert coarse_evidence(np.zeros((64, 64), np.uint8), np.full((64, 64), 255, np.uint8))[0] == 255


def test_suspicious_rule_and_pixel_confirmation_are_separate():
    pair = {"phash_distance": "2", "dhash_distance": "21"}
    assert full_review_needed(pair, 80, 0, 0)
    assert not full_review_needed({"phash_distance": "6", "dhash_distance": "30"}, 50, .1, .1)
    assert classify_full({"pixel_mae": 2, "pixel_correlation": .999}) == "confirmed_direct_pixel_automated"
    assert classify_full({"pixel_mae": 1, "pixel_correlation": .998}) == "unresolved_human_review"


def test_transitive_ham_match_excludes_all_binary_members():
    paths = ["ham", "binary_train", "binary_test"]
    group = duplicate_groups(paths, [("ham", "binary_train"), ("binary_train", "binary_test")])[0]
    records = {"ham": {"source": "HAM10000", "label": "nv"},
               "binary_train": {"source": "binary", "label": "benign", "source_split": "train"},
               "binary_test": {"source": "binary", "label": "benign", "source_split": "test"}}
    assert exclusion_reasons(group, records) == {
        "binary_train": "same_photograph_as_HAM",
        "binary_test": "same_photograph_as_HAM"}
