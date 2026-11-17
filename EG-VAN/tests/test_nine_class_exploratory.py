"""Small fixtures for the exploratory path's split and label safeguards."""

import csv
import hashlib
import json
from pathlib import Path

import pytest
import torch

import nine_class_exploratory as exploratory
import nine_class_dataset as dataset_module
import nine_class_three_arm_diagnostic as diagnostic
from nine_class_protocol import file_sha256
from nine_class_stage4 import CLASS_NAMES


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def preview_fixture(tmp_path, monkeypatch):
    preview = tmp_path / "preview.csv"
    report = tmp_path / "report.json"
    decisions = tmp_path / "decisions.csv"
    monkeypatch.setattr(exploratory, "PREVIEW", preview)
    monkeypatch.setattr(exploratory, "REPORT", report)
    monkeypatch.setattr(exploratory, "SIIM_DECISIONS", decisions)
    rows, siim = [], []
    for partition in exploratory.PARTITIONS:
        for index, name in enumerate(CLASS_NAMES):
            image_id = f"{partition}_{name}"
            path = f"images/{image_id}.jpg"
            if partition in {"train", "validation"}:
                (tmp_path / "images").mkdir(exist_ok=True)
                (tmp_path / path).write_bytes(image_id.encode())
                image_sha256 = file_sha256(tmp_path / path)
            else:
                image_sha256 = hashlib.sha256(image_id.encode()).hexdigest()
            source = ("SIIM-ISIC 2020 training v2" if name == "BENIGN" else
                      "FANCONIC_LOCAL_UNVERIFIED_VERSION" if name == "MALIGNANT" else "HAM10000")
            status = ("PRELIMINARY_NO_CANDIDATE_NOT_APPROVED" if name == "BENIGN" else
                      "BINARY_PROVISIONAL_SOURCE_TRAIN" if name == "MALIGNANT" else
                      "HAM_AVAILABLE_NOT_FINAL_ELIGIBLE")
            patient = f"patient_{partition}" if name == "BENIGN" else ""
            rows.append({"image_path": path, "source_dataset": source,
                "original_label": name.lower(), "class_name": name, "class_index": str(index),
                "image_id": image_id, "lesion_id": f"lesion_{image_id}", "patient_id": patient,
                "source_split": "2020_training" if name == "BENIGN" else "train" if name == "MALIGNANT" else "",
                "sha256": image_sha256, "overlap_group": f"group_{image_id}",
                "automated_status": status, "approval_status": "NOT_APPROVED",
                "proposed_partition": partition})
            if name == "BENIGN":
                siim.append({"image_id": image_id, "original_target": "0", "patient_id": patient,
                             "actual_automated_status": status, "approval_status": "NOT_APPROVED"})
    write_csv(decisions, siim)

    def save():
        write_csv(preview, rows)
        report.write_text(json.dumps({"status": "PLANNING_ONLY_NOT_APPROVED",
            "planning_assignment_sha256": file_sha256(preview), "planning_inventory_rows": len(rows)}), encoding="utf-8")

    save()
    return tmp_path, rows, save


def test_exploratory_preview_accepts_source_defined_fixture(preview_fixture):
    root, _, _ = preview_fixture
    checked, report = exploratory.validate_preview(
        root, verify_bytes=True, image_partitions={"train", "validation"}
    )
    assert len(checked) == 36
    assert report["known_group_crossings"] == 0
    assert report["status"].startswith("EXPLORATORY_ONLY")


def test_diagnostic_integrity_scope_never_checks_calibration_or_test_images(
    preview_fixture, monkeypatch
):
    root, _, _ = preview_fixture
    image_operations = {"resolve": [], "is_file": [], "open": [], "hash": []}
    original_is_file = Path.is_file
    original_resolve = Path.resolve
    original_open = Path.open
    original_file_sha256 = exploratory.file_sha256

    def tracked_is_file(path):
        if path.suffix.lower() == ".jpg":
            image_operations["is_file"].append(path.name)
        return original_is_file(path)

    def tracked_resolve(path, *args, **kwargs):
        if path.suffix.lower() == ".jpg":
            image_operations["resolve"].append(path.name)
        return original_resolve(path, *args, **kwargs)

    def tracked_open(path, *args, **kwargs):
        if path.suffix.lower() == ".jpg":
            image_operations["open"].append(path.name)
        return original_open(path, *args, **kwargs)

    def tracked_file_sha256(path):
        if path.suffix.lower() == ".jpg":
            image_operations["hash"].append(path.name)
        return original_file_sha256(path)

    monkeypatch.setattr(Path, "is_file", tracked_is_file)
    monkeypatch.setattr(Path, "resolve", tracked_resolve)
    monkeypatch.setattr(Path, "open", tracked_open)
    monkeypatch.setattr(exploratory, "file_sha256", tracked_file_sha256)
    checked, _ = exploratory.validate_preview(
        root,
        verify_bytes=True,
        image_partitions={"train", "validation"},
    )

    assert len(checked) == 36
    assert len(image_operations["is_file"]) == 18
    assert len(image_operations["hash"]) == 18
    assert len(image_operations["open"]) == 18
    assert len(image_operations["resolve"]) == 18
    assert all(
        name.startswith(("train_", "validation_"))
        for names in image_operations.values()
        for name in names
    )


@pytest.mark.parametrize(
    ("partition", "unsafe_path"),
    [
        ("calibration", "../outside.jpg"),
        ("test", r"C:\outside\image.jpg"),
        ("test", r"C:relative\image.jpg"),
        ("calibration", r"\\server\share\image.jpg"),
        ("test", "/absolute/image.jpg"),
        ("calibration", r"\rooted\image.jpg"),
    ],
)
def test_unsafe_protected_partition_paths_are_rejected(
    preview_fixture, partition, unsafe_path
):
    root, rows, save = preview_fixture
    row = next(item for item in rows if item["proposed_partition"] == partition)
    row["image_path"] = unsafe_path
    save()

    with pytest.raises(ValueError, match="image_path"):
        exploratory.validate_preview(
            root,
            verify_bytes=True,
            image_partitions={"train", "validation"},
        )


@pytest.mark.parametrize("unsafe_path", ["", "   ", "images//empty.jpg", "images/./dot.jpg"])
def test_empty_or_malformed_image_paths_are_rejected(preview_fixture, unsafe_path):
    root, rows, save = preview_fixture
    row = next(item for item in rows if item["proposed_partition"] == "calibration")
    row["image_path"] = unsafe_path
    save()

    with pytest.raises(ValueError, match="image_path"):
        exploratory.validate_preview(
            root,
            verify_bytes=True,
            image_partitions={"train", "validation"},
        )


def test_safe_protected_paths_pass_metadata_validation_without_image_io(
    preview_fixture, monkeypatch
):
    root, rows, _ = preview_fixture
    assert all(
        row["image_path"].startswith("images/")
        for row in rows
        if row["proposed_partition"] in {"calibration", "test"}
    )
    operations = []
    original_is_file = Path.is_file
    original_resolve = Path.resolve
    original_open = Path.open
    original_file_sha256 = exploratory.file_sha256

    def is_protected_image(path):
        return path.suffix.lower() == ".jpg" and path.stem.startswith(
            ("calibration_", "test_")
        )

    def record_operation(operation, path, original, *args, **kwargs):
        if is_protected_image(path):
            operations.append((operation, path.name))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(
        Path, "is_file",
        lambda path: record_operation("is_file", path, original_is_file),
    )
    monkeypatch.setattr(
        Path, "resolve",
        lambda path, *args, **kwargs: record_operation(
            "resolve", path, original_resolve, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        Path, "open",
        lambda path, *args, **kwargs: record_operation(
            "open", path, original_open, *args, **kwargs
        ),
    )

    def tracked_file_sha256(path):
        if is_protected_image(path):
            operations.append(("hash", path.name))
        return original_file_sha256(path)

    monkeypatch.setattr(exploratory, "file_sha256", tracked_file_sha256)
    checked, report = exploratory.validate_preview(
        root,
        verify_bytes=True,
        image_partitions={"train", "validation"},
    )
    assert len(checked) == 36
    assert report["known_group_crossings"] == 0
    assert not operations


def test_three_arm_preflight_checks_only_train_validation_images(
    preview_fixture, monkeypatch
):
    root, rows, _ = preview_fixture
    split = root / "synthetic_split.csv"
    meta = root / "synthetic_frozen_provenance.json"
    config_path = root / "synthetic_config.json"
    config = {
        "schema_version": "nine_class_training_v2",
        "split_protocol": "four_way_v1",
        "label_order": list(CLASS_NAMES),
        "seed": 42,
        "image_size": 384,
        "preprocessing_mode": "raw_resize_imagenet_v2",
        "batch_size": 8,
        "gradient_accumulation_steps": 4,
        "batchnorm_policy": "freeze_running_stats",
        "epochs": 25,
        "num_workers": 0,
        "initialization": {
            "mode": "random",
            "efficient_local_state": None,
            "resnet_local_state": None,
        },
        "fusion_channels": 128,
        "optimizer": "Adamax",
        "learning_rate": 0.001,
        "focal_alpha": 0.25,
        "focal_gamma": 2.0,
        "class_weighting": False,
        "scheduler": {"name": "ReduceLROnPlateau", "factor": 0.5, "patience": 2},
        "gradient_clip_norm": 1.0,
        "mixed_precision": "cuda_if_available",
        "early_stopping": {"enabled": False, "patience": 5},
    }
    split_rows = [
        {
            **row,
            "split": row["proposed_partition"],
            "research_status": exploratory.RESEARCH_STATUS,
        }
        for row in rows
    ]
    write_csv(split, split_rows)
    config_path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(exploratory, "SPLIT", split)
    monkeypatch.setattr(exploratory, "META", meta)
    monkeypatch.setattr(exploratory, "CONFIG", config_path)
    meta.write_text(json.dumps({
        "status": exploratory.RESEARCH_STATUS,
        "source_preview_sha256": file_sha256(exploratory.PREVIEW),
        "split_sha256": file_sha256(split),
        "config_sha256": file_sha256(config_path),
        "limitations": ["synthetic fixture"],
    }), encoding="utf-8")

    operations = {"resolve": [], "is_file": [], "open": [], "hash": [], "dataset_split": []}
    original_resolve = Path.resolve
    original_is_file = Path.is_file
    original_open = Path.open
    original_hash = exploratory.file_sha256
    original_dataset = diagnostic.NineClassDataset

    def is_protected_image(path):
        return path.suffix.lower() == ".jpg" and path.stem.startswith(
            ("calibration_", "test_")
        )

    def tracked_resolve(path, *args, **kwargs):
        if path.suffix.lower() == ".jpg":
            operations["resolve"].append(path.name)
        return original_resolve(path, *args, **kwargs)

    def tracked_is_file(path):
        if path.suffix.lower() == ".jpg":
            operations["is_file"].append(path.name)
        return original_is_file(path)

    def tracked_open(path, *args, **kwargs):
        if path.suffix.lower() == ".jpg":
            operations["open"].append(path.name)
        return original_open(path, *args, **kwargs)

    def tracked_hash(path):
        if path.suffix.lower() == ".jpg":
            operations["hash"].append(path.name)
        return original_hash(path)

    def tracked_dataset(*args, **kwargs):
        operations["dataset_split"].append(args[2])
        return original_dataset(*args, **kwargs)

    def synthetic_image_tensor(path, preprocess, *, train=False, generator=None):
        with path.open("rb") as handle:
            assert handle.read()
        return torch.zeros((3, preprocess.image_size, preprocess.image_size))

    monkeypatch.setattr(Path, "resolve", tracked_resolve)
    monkeypatch.setattr(Path, "is_file", tracked_is_file)
    monkeypatch.setattr(Path, "open", tracked_open)
    monkeypatch.setattr(exploratory, "file_sha256", tracked_hash)
    monkeypatch.setattr(diagnostic, "NineClassDataset", tracked_dataset)
    monkeypatch.setattr(dataset_module, "image_tensor", synthetic_image_tensor)

    report = diagnostic.preflight_diagnostic(root)

    assert report["status"] == "PREFLIGHT_PASSED"
    assert report["research_status"] == diagnostic.RESEARCH_STATUS
    assert report["cohort_status"] == "NOT_APPROVED"
    assert report["checked_image_partitions"] == ["train", "validation"]
    assert report["class_order"] == list(CLASS_NAMES)
    assert operations["dataset_split"] == ["train", "validation"]
    assert len(operations["resolve"]) == 18
    assert len(operations["is_file"]) == 18
    assert len(operations["hash"]) == 18
    assert len(operations["open"]) == 36
    assert all(
        name.startswith(("train_", "validation_"))
        for operation, names in operations.items()
        if operation != "dataset_split"
        for name in names
    )
    assert not any(
        is_protected_image(root / "images" / name)
        for operation, names in operations.items()
        if operation != "dataset_split"
        for name in names
    )


def test_exploratory_preview_rejects_group_crossing(preview_fixture):
    root, rows, save = preview_fixture
    rows[9]["overlap_group"] = rows[0]["overlap_group"]
    save()
    with pytest.raises(ValueError, match="group crosses"):
        exploratory.validate_preview(
            root, image_partitions={"train", "validation"}
        )


def test_exploratory_preview_rejects_quarantined_siim(preview_fixture):
    root, rows, save = preview_fixture
    row = next(r for r in rows if r["class_name"] == "BENIGN")
    row["automated_status"] = "QUARANTINE_CANDIDATE_RELATION"
    save()
    with pytest.raises(ValueError, match="SIIM image"):
        exploratory.validate_preview(
            root, image_partitions={"train", "validation"}
        )


def test_notebook_is_unexecuted_and_exploratory_only():
    notebook = json.loads((Path(__file__).resolve().parents[1] /
        "notebooks/nine_class_exploratory_colab.ipynb").read_text(encoding="utf-8"))
    assert all(cell.get("execution_count") is None and not cell.get("outputs")
               for cell in notebook["cells"] if cell["cell_type"] == "code")
    assert "EXPLORATORY ONLY" in "".join(notebook["cells"][0]["source"])
