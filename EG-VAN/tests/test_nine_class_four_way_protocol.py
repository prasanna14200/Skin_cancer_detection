"""Synthetic-only checks for the opt-in four-way production gate."""

import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nine_class_dataset import NineClassDataset, PreprocessConfig
from nine_class_protocol import LOCKED_FIELDS, file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES
from nine_class_training import load_config
from nine_class_evaluation import predict
from torch.utils.data import DataLoader, TensorDataset


def fixtures(tmp_path):
    records = []
    for index, name in enumerate(CLASS_NAMES):
        for split in ("train", "validation", "calibration", "test"):
            rel = f"images/{name}_{split}.jpg"
            path = tmp_path / rel
            path.parent.mkdir(exist_ok=True)
            level = index * 20 + ("train", "validation", "calibration", "test").index(split)
            assert cv2.imwrite(str(path), np.full((12, 14, 3), level, np.uint8))
            row = {field: "" for field in LOCKED_FIELDS}
            row.update(image_path=rel, source_dataset="SYNTHETIC_TEST_ONLY",
                       original_label=name.lower(), class_name=name, class_index=str(index),
                       image_id=f"TEST_{name}_{split}", lesion_id=f"LESION_{name}_{split}",
                       patient_id=f"PATIENT_{name}_{split}", source_split="train",
                       sha256=file_sha256(path), overlap_group=f"g-{name}-{split}",
                       duplicate_overlap_evidence_tier="NONE_RECORDED")
            records.append(dict(row, provisional_eligibility_status="APPROVED_ELIGIBLE", split=split))
    inventory, split_path, approval = (tmp_path / name for name in ("inventory.csv", "split.csv", "approval.json"))
    write(records, inventory, split_path, approval)
    return records, inventory, split_path, approval


def write(records, inventory, split_path, approval, *, four_way=True, freeze=True):
    with inventory.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOCKED_FIELDS)
        writer.writeheader()
        writer.writerows({key: r[key] for key in LOCKED_FIELDS} for r in records)
    with split_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=(*LOCKED_FIELDS, "provisional_eligibility_status", "split"))
        writer.writeheader()
        writer.writerows(records)
    approval.write_text(json.dumps({
        "synthetic_fixture": True, "approval_status": "APPROVED_BY_RESEARCHER",
        "approved_by": "SYNTHETIC_TEST_ONLY", "approval_date_utc": "2000-01-01T00:00:00Z",
        "adjudication_reference": "SYNTHETIC_TEST_ONLY", "source_rights_reference": "SYNTHETIC_TEST_ONLY",
        "protected_test_policy_reference": "SYNTHETIC_TEST_ONLY",
        "test_partition_frozen": True,
        **({"split_protocol": "four_way_v1", "calibration_partition_frozen": freeze,
            "calibration_separate_from_model_selection": True} if four_way else {}),
        "approved_split_sha256": file_sha256(split_path),
        "source_inventory_sha256": file_sha256(inventory)}), encoding="utf-8")


def test_four_way_requires_explicit_frozen_calibration_and_keeps_v1_rejection(tmp_path):
    records, inventory, split, approval = fixtures(tmp_path)
    with pytest.raises(ValueError, match="Synthetic test approval"):
        validate_approved_split(tmp_path, split, approval, inventory)
    accepted, provenance = validate_approved_split(tmp_path, split, approval, inventory,
                                                    allow_synthetic_fixture=True)
    assert len(accepted) == 36
    assert provenance["split_protocol"] == "four_way_v1"
    assert all(set(provenance["counts"][part]) == set(CLASS_NAMES)
               for part in ("train", "validation", "calibration", "test"))
    write(records, inventory, split, approval, freeze=False)
    with pytest.raises(ValueError, match="frozen, separate calibration"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)
    write(records, inventory, split, approval, four_way=False)
    with pytest.raises(ValueError, match="Invalid split: calibration"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)


def test_four_way_rejects_cross_partition_identity_and_source_test(tmp_path):
    records, inventory, split, approval = fixtures(tmp_path)
    cal = next(r for r in records if r["class_name"] == "AKIEC" and r["split"] == "calibration")
    train = next(r for r in records if r["class_name"] == "AKIEC" and r["split"] == "train")
    cal["patient_id"] = train["patient_id"]
    write(records, inventory, split, approval)
    with pytest.raises(ValueError, match="Cross-split patient"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)
    cal["patient_id"] = "SEPARATE"
    cal["source_split"] = "test"
    write(records, inventory, split, approval)
    with pytest.raises(ValueError, match="Publisher source-test"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)


def test_v2_t4_config_and_deterministic_calibration_loader(tmp_path):
    config = load_config(ROOT / "config/nine_class_training_t4_four_way_v2.json")
    assert config["schema_version"] == "nine_class_training_v2"
    assert (config["batch_size"], config["gradient_accumulation_steps"], config["optimizer"]) == (8, 4, "Adamax")
    _, _, split, _ = fixtures(tmp_path)
    dataset = NineClassDataset(tmp_path, split, "calibration", PreprocessConfig(image_size=16,
                                                                                  pipeline_version="raw_resize_imagenet_v2"))
    image_a, target_a = dataset[0]
    image_b, target_b = dataset[0]
    assert target_a == target_b == 0
    assert torch.equal(image_a, image_b)


def test_calibration_prediction_exports_raw_logits_separately():
    model = torch.nn.Linear(4, 9)
    loader = DataLoader(TensorDataset(torch.ones(2, 4), torch.tensor([0, 8])), batch_size=1)
    probabilities, targets, logits = predict(model, loader, torch.device("cpu"), return_logits=True)
    assert probabilities.shape == logits.shape == (2, 9)
    assert targets.tolist() == [0, 8]
    assert np.allclose(probabilities, torch.softmax(torch.tensor(logits), dim=1).numpy())
