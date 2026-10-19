"""Focused Stage 3 evidence and boundary checks; no project images are written."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nine_class_overlap_review import (  # noqa: E402
    duplicate_groups, exclusion_reasons, read_inputs, render, source_record,
)


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class OverlapReviewTests(unittest.TestCase):
    def test_transitive_groups_and_protected_test(self):
        ham = "data/raw/HAM10000_images_part_1/ISIC_0000001.jpg"
        train = "data/isic/data/train/benign/1.jpg"
        test = "data/isic/data/test/benign/2.jpg"
        records = {
            ham: {"source": "HAM10000", "label": "nv", "source_split": ""},
            train: {"source": "binary", "label": "benign", "source_split": "train"},
            test: {"source": "binary", "label": "benign", "source_split": "test"},
        }
        groups = duplicate_groups(list(records), [(ham, train), (train, test)])
        self.assertEqual(groups, [sorted(records)])
        self.assertEqual(exclusion_reasons(groups[0], records),
                         {train: "same_photograph_as_HAM", test: "same_photograph_as_HAM"})
        self.assertEqual(exclusion_reasons([train, test], records),
                         {train: "binary_duplicate_keep_source_test"})

    def test_source_aware_ids_and_label_conflict(self):
        self.assertEqual(source_record("data/isic/data/test/benign/1003.jpg", {})["label"], "benign")
        self.assertEqual(source_record("data/isic/data/test/malignant/1003.jpg", {})["label"], "malignant")
        with self.assertRaises(ValueError):
            source_record("data/isic/test/benign/1003.jpg", {})
        a = "data/isic/data/train/benign/1.jpg"
        b = "data/isic/data/test/malignant/1.jpg"
        records = {a: {"source": "binary", "label": "benign", "source_split": "train"},
                   b: {"source": "binary", "label": "malignant", "source_split": "test"}}
        self.assertEqual(exclusion_reasons([a, b], records), {})

    def test_deterministic_render_and_unresolved_pair(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            ham = "data/raw/HAM10000_images_part_1/ISIC_0000001.jpg"
            test = "data/isic/data/test/benign/1.jpg"
            train = "data/isic/data/train/benign/2.jpg"
            other = "data/isic/data/train/malignant/3.jpg"
            rng = np.random.default_rng(7)
            image = rng.integers(0, 256, (48, 48, 3), dtype=np.uint8)
            for path in (ham, test, train):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(target), image)
            target = root / other
            target.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(target), 255 - image)
            write_csv(root / "data/raw/HAM10000_metadata.csv",
                      ("lesion_id", "image_id", "dx"),
                      [{"lesion_id": "HAM_L1", "image_id": "ISIC_0000001", "dx": "nv"}])
            write_csv(root / "analysis/nine_class_similarity/fingerprints.csv",
                      ("image_path", "phash64", "dhash64"),
                      [{"image_path": p, "phash64": "0000000000000000",
                        "dhash64": "0000000000000000"} for p in (ham, test, train, other)])
            write_csv(root / "analysis/nine_class_similarity/candidates.csv",
                      ("path_a", "path_b", "scope", "phash_distance", "dhash_distance"),
                      [{"path_a": a, "path_b": b, "scope": scope,
                        "phash_distance": "0", "dhash_distance": "0"}
                       for a, b, scope in ((test, ham, "binary_ham"),
                                            (train, test, "binary_binary"),
                                            (train, other, "binary_binary"))])
            first = render(root, root / "review_one")
            second = render(root, root / "review_two")
            self.assertEqual(first["output_sha256"], second["output_sha256"])
            self.assertEqual(first["counts"]["proposed_binary_exclusions"], 2)
            self.assertEqual(first["counts"]["unresolved_priority_pairs"], 1)
            self.assertGreaterEqual(first["counts"]["source_test_conflict_rows"], 1)
            with (root / "review_one/binary_eligibility_review.csv").open(newline="", encoding="utf-8") as handle:
                rows = {r["image_path"]: r for r in csv.DictReader(handle)}
            self.assertEqual(rows[test]["source_split"], "test")
            self.assertEqual(rows[test]["eligibility_status"], "proposed_exclude_confirmed")
            self.assertEqual(rows[other]["eligibility_status"], "unresolved_priority_candidate")
            self.assertEqual(len(read_inputs(root)[0]), 4)
            with self.assertRaises(FileExistsError):
                render(root, root / "review_one")
            replaced = render(root, root / "review_one", replace_existing=True)
            self.assertEqual(first["output_sha256"], replaced["output_sha256"])

    def test_repeated_pair_rejected(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            write_csv(root / "data/raw/HAM10000_metadata.csv",
                      ("lesion_id", "image_id", "dx"), [])
            a = "data/isic/data/train/benign/1.jpg"
            b = "data/isic/data/test/benign/2.jpg"
            for p in (a, b):
                target = root / p
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"x")
            write_csv(root / "analysis/nine_class_similarity/fingerprints.csv",
                      ("image_path", "phash64", "dhash64"),
                      [{"image_path": p, "phash64": "0000000000000000",
                        "dhash64": "0000000000000000"} for p in (a, b)])
            row = {"path_a": a, "path_b": b, "scope": "binary_binary",
                   "phash_distance": "0", "dhash_distance": "0"}
            write_csv(root / "analysis/nine_class_similarity/candidates.csv",
                      ("path_a", "path_b", "scope", "phash_distance", "dhash_distance"),
                      [row, row])
            with self.assertRaisesRegex(ValueError, "Repeated candidate"):
                read_inputs(root)


if __name__ == "__main__":
    unittest.main()
