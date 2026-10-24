"""Synthetic-only Stage 6 gates, loss, metrics, and state persistence."""

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn
from torch.optim import Adamax
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nine_class_metrics import summarize_predictions
from nine_class_evaluation import predict
from nine_class_protocol import LOCKED_FIELDS, file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES
from nine_class_training import focal_loss, load_config, load_checkpoint, run_epoch, save_checkpoint, training_class_weights


def fixture_files(tmp_path):
    rows = []
    for index, name in enumerate(CLASS_NAMES):
        for split in ("train", "validation"):
            rel = f"images/{index}_{split}.jpg"
            path = tmp_path / rel
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(f"synthetic fixture {index} {split}, not a clinical image".encode())
            row = {key: "" for key in LOCKED_FIELDS}
            row.update(image_path=rel, source_dataset="SYNTHETIC_TEST_ONLY", original_label=name.lower(),
                       class_name=name, class_index=str(index), source_split="train",
                       sha256=file_sha256(path), overlap_group=f"g-{index}-{split}",
                       duplicate_overlap_evidence_tier="NONE_RECORDED")
            rows.append(dict(row, provisional_eligibility_status="APPROVED_ELIGIBLE", split=split))
    return rows, tmp_path / "inventory.csv", tmp_path / "approved_split.csv", tmp_path / "approval.json"


def write_fixture(rows, inventory, split, approval):
    with inventory.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOCKED_FIELDS)
        writer.writeheader()
        writer.writerows({key: row[key] for key in LOCKED_FIELDS} for row in rows)
    with split.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=(*LOCKED_FIELDS, "provisional_eligibility_status", "split"))
        writer.writeheader()
        writer.writerows(rows)
    approval.write_text(json.dumps({
        "synthetic_fixture": True,
        "approval_status": "APPROVED_BY_RESEARCHER",
        "approved_by": "SYNTHETIC_TEST_ONLY",
        "approval_date_utc": "2000-01-01T00:00:00Z",
        "adjudication_reference": "SYNTHETIC_TEST_ONLY",
        "source_rights_reference": "SYNTHETIC_TEST_ONLY",
        "protected_test_policy_reference": "SYNTHETIC_TEST_ONLY",
        "approved_split_sha256": file_sha256(split),
        "source_inventory_sha256": file_sha256(inventory),
    }), encoding="utf-8")


def test_approval_gate_and_no_real_training_on_synthetic_fixture(tmp_path):
    rows, inventory, split, approval = fixture_files(tmp_path)
    write_fixture(rows, inventory, split, approval)
    with pytest.raises(ValueError, match="Synthetic test approval"):
        validate_approved_split(tmp_path, split, approval, inventory)
    accepted, provenance = validate_approved_split(tmp_path, split, approval, inventory,
                                                    allow_synthetic_fixture=True)
    assert len(accepted) == 18
    assert set(provenance["counts"]["train"]) == set(CLASS_NAMES)
    with pytest.raises(FileNotFoundError):
        validate_approved_split(tmp_path, split, tmp_path / "missing_approval.json", inventory)
    rows[0]["provisional_eligibility_status"] = "AI_SAME_PHOTO_QUARANTINE"
    write_fixture(rows, inventory, split, approval)
    with pytest.raises(ValueError, match="Unapproved"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)


def test_cross_split_and_publisher_test_rejected(tmp_path):
    rows, inventory, split, approval = fixture_files(tmp_path)
    rows[1]["overlap_group"] = rows[0]["overlap_group"]
    write_fixture(rows, inventory, split, approval)
    with pytest.raises(ValueError, match="Cross-split overlap"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)
    rows[1]["overlap_group"] = "separate"
    rows[0]["source_split"] = "test"
    write_fixture(rows, inventory, split, approval)
    with pytest.raises(ValueError, match="Publisher source-test"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)


def test_protected_test_link_and_label_tampering_rejected(tmp_path):
    rows, inventory, split, approval = fixture_files(tmp_path)
    protected = dict(rows[0], image_path="images/protected.jpg", split="test", source_split="test")
    (tmp_path / protected["image_path"]).write_bytes(b"synthetic protected record")
    protected["sha256"] = file_sha256(tmp_path / protected["image_path"])
    rows.append(protected)
    write_fixture(rows, inventory, split, approval)
    with pytest.raises(ValueError, match="linked to publisher source test"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)
    rows.pop()
    write_fixture(rows, inventory, split, approval)
    with split.open("r", newline="", encoding="utf-8") as handle:
        altered = list(csv.DictReader(handle))
    altered[0]["class_name"] = "MEL"
    with split.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=altered[0].keys())
        writer.writeheader()
        writer.writerows(altered)
    record = json.loads(approval.read_text(encoding="utf-8"))
    record["approved_split_sha256"] = file_sha256(split)
    approval.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)


def test_source_image_byte_change_rejected(tmp_path):
    rows, inventory, split, approval = fixture_files(tmp_path)
    write_fixture(rows, inventory, split, approval)
    (tmp_path / rows[0]["image_path"]).write_bytes(b"changed synthetic bytes")
    with pytest.raises(ValueError, match="Image bytes differ"):
        validate_approved_split(tmp_path, split, approval, inventory, allow_synthetic_fixture=True)


def test_focal_optimizer_checkpoint_resume_and_metrics(tmp_path):
    torch.manual_seed(4)
    config = load_config(Path(__file__).resolve().parents[1] / "config/nine_class_training_v1.json")
    model = nn.Linear(4, 9)
    optimizer = Adamax(model.parameters(), lr=0.001)
    scheduler = ReduceLROnPlateau(optimizer)
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    x = torch.randn(9, 4)
    y = torch.arange(9)
    weights = training_class_weights([{"split": "train", "class_name": name} for name in CLASS_NAMES])
    logits = model(x)
    loss = focal_loss(logits, y, class_weights=weights)
    assert torch.isfinite(loss)
    loss.backward()
    assert model.weight.grad is not None and torch.isfinite(model.weight.grad).all()
    before = model.weight.detach().clone()
    optimizer.step()
    assert not torch.equal(before, model.weight)
    train_result = run_epoch(model, DataLoader(TensorDataset(x, y), batch_size=9),
                             torch.device("cpu"), config, optimizer=optimizer, scaler=scaler)
    assert train_result["n_samples"] == 9 and np.isfinite(train_result["loss"])
    scheduler.step(train_result["loss"])
    state = {"epoch": 0, "model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(),
             "scheduler_state": scheduler.state_dict(), "scaler_state": scaler.state_dict(),
             "config_sha256": "synthetic", "split_sha256": "synthetic"}
    checkpoint = tmp_path / "run" / "last.pt"
    save_checkpoint(checkpoint, state)
    restored = nn.Linear(4, 9)
    restored_optimizer = Adamax(restored.parameters(), lr=0.001)
    restored_scheduler = ReduceLROnPlateau(restored_optimizer)
    loaded = load_checkpoint(checkpoint, restored, restored_optimizer, restored_scheduler,
                             expected={"config_sha256": "synthetic", "split_sha256": "synthetic"})
    assert loaded["epoch"] == 0 and torch.equal(model.weight, restored.weight)
    assert restored_optimizer.state_dict()["state"] and restored_scheduler.state_dict() == scheduler.state_dict()
    with pytest.raises(ValueError, match="provenance mismatch"):
        load_checkpoint(checkpoint, restored, expected={"split_sha256": "wrong"})
    perfect = summarize_predictions(np.eye(9), np.arange(9), split="validation")
    assert perfect["accuracy"] == perfect["macro_f1"] == perfect["weighted_f1"] == 1.0
    assert perfect["confusion_matrix"] == np.eye(9, dtype=int).tolist()
    incomplete = summarize_predictions(np.eye(9)[:8], np.arange(8), split="test")
    assert incomplete["accuracy"] is None and not incomplete["all_nine_classes_present"]
    assert incomplete["per_class"]["MALIGNANT"]["support"] == 0 and incomplete["warnings"]


def test_prediction_probabilities_have_nine_columns():
    model = nn.Linear(4, 9)
    loader = DataLoader(TensorDataset(torch.zeros(2, 4), torch.tensor([0, 8])), batch_size=1)
    probabilities, targets = predict(model, loader, torch.device("cpu"))
    assert probabilities.shape == (2, 9)
    assert targets.tolist() == [0, 8]
    assert np.allclose(probabilities.sum(axis=1), 1)
