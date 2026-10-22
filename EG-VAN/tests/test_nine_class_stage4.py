"""Focused Stage 4 safety and loader checks."""

import csv
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nine_class_dataset import NineClassDataset, PreprocessConfig, image_tensor
from nine_class_stage4 import CLASS_NAMES, ROOT, guarded_group_split, sha256


def test_nine_class_order_and_insufficient_benign():
    assert CLASS_NAMES == ("AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT")
    rows = [dict(class_name=name, overlap_group=f"g{i}", source_split="train", provisional_eligibility_status="APPROVED_ELIGIBLE")
            for i, name in enumerate(CLASS_NAMES) if name != "BENIGN"]
    with pytest.raises(ValueError, match="nine classes"):
        guarded_group_split(rows)


def test_group_split_deterministic_and_protects_test():
    rows = [dict(class_name=name, class_index=str(i), overlap_group=f"{name}-{j}",
                 provisional_eligibility_status="APPROVED_ELIGIBLE",
                 source_split="train", image_path=f"{name}-{j}.jpg")
            for i, name in enumerate(CLASS_NAMES) for j in range(3)]
    a = guarded_group_split(rows, seed=42)
    b = guarded_group_split(rows, seed=42)
    assert a == b
    assert {r["split"] for r in a} == {"train", "validation"}
    assert all(len({r["split"] for r in a if r["overlap_group"] == group}) == 1
               for group in {r["overlap_group"] for r in a})
    with pytest.raises(ValueError, match="source-test"):
        guarded_group_split(rows + [dict(rows[0], source_split="test")])
    with pytest.raises(ValueError, match="APPROVED_ELIGIBLE"):
        guarded_group_split([dict(rows[0], provisional_eligibility_status="AI_SAME_PHOTO_QUARANTINE")] + rows[1:])


def test_preprocessing_deterministic_shape_dtype_and_missing(tmp_path):
    path = tmp_path / "a.jpg"
    image = np.full((48, 64, 3), 120, dtype=np.uint8)
    image[12:35, 18:40] = (30, 80, 190)
    assert cv2.imwrite(str(path), image)
    config = PreprocessConfig(image_size=64)
    first = image_tensor(path, config)
    second = image_tensor(path, config)
    assert first.shape == (3, 64, 64)
    assert first.dtype == torch.float32
    assert torch.isfinite(first).all()
    assert torch.equal(first, second)
    with pytest.raises(FileNotFoundError):
        image_tensor(tmp_path / "missing.jpg", config)


def test_loader_split_policy_and_training_only_augmentation(tmp_path, monkeypatch):
    image = np.zeros((36, 48, 3), dtype=np.uint8)
    image[:15, :12] = (0, 180, 220)
    assert cv2.imwrite(str(tmp_path / "one.jpg"), image)
    csv_path = tmp_path / "split.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("image_path", "class_name", "class_index", "source_split", "split"))
        writer.writeheader()
        writer.writerows([
            dict(image_path="one.jpg", class_name="AKIEC", class_index="0", source_split="train", split="train"),
            dict(image_path="one.jpg", class_name="AKIEC", class_index="0", source_split="train", split="validation"),
        ])
    config = PreprocessConfig(image_size=48)
    val = NineClassDataset(tmp_path, csv_path, "validation", config)
    assert torch.equal(val[0][0], val[0][0])
    train = NineClassDataset(tmp_path, csv_path, "train", config)
    calls = []
    original = torch.rand
    def recorded_rand(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(torch, "rand", recorded_rand)
    train[0]
    assert len(calls) == 2
    calls.clear()
    val[0]
    assert not calls
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow(["one.jpg", "AKIEC", "0", "test", "train"])
    with pytest.raises(ValueError, match="Protected"):
        NineClassDataset(tmp_path, csv_path, "train", config)


def test_real_manifest_source_integrity_and_grouping():
    manifest = ROOT / "analysis/nine_class_stage4/nine_class_source_manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 13312
    by_path = {r["image_path"]: r for r in rows}
    assert len(by_path) == len(rows)
    assert all((ROOT / path).is_file() for path in by_path)
    assert not any(path.startswith(("data/isic/train/", "data/isic/test/")) for path in by_path)
    lesions = {}
    for row in rows:
        if row["lesion_id"]:
            lesions.setdefault(row["lesion_id"], row["overlap_group"])
            assert lesions[row["lesion_id"]] == row["overlap_group"]
    edges = ROOT / "analysis/nine_class_recovery/stage3i/proposed_overlap_edges.csv"
    with edges.open(newline="", encoding="utf-8") as handle:
        for edge in csv.DictReader(handle):
            assert by_path[edge["path_a"]]["overlap_group"] == by_path[edge["path_b"]]["overlap_group"]
    duplicate = ["data/isic/data/train/malignant/768.jpg", "data/isic/data/train/malignant/769.jpg"]
    assert by_path[duplicate[0]]["sha256"] == by_path[duplicate[1]]["sha256"]
    assert by_path[duplicate[0]]["sha256"] == sha256(ROOT / duplicate[0])
    assert by_path[duplicate[0]]["overlap_group"] == by_path[duplicate[1]]["overlap_group"]
