"""Small fixtures for the exploratory path's split and label safeguards."""

import csv
import json
from pathlib import Path

import pytest

import nine_class_exploratory as exploratory
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
            (tmp_path / "images").mkdir(exist_ok=True)
            (tmp_path / path).write_bytes(image_id.encode())
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
                "sha256": file_sha256(tmp_path / path), "overlap_group": f"group_{image_id}",
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
    root, rows, _ = preview_fixture
    checked, report = exploratory.validate_preview(root, verify_bytes=True)
    assert len(checked) == 36
    assert report["known_group_crossings"] == 0
    assert report["status"].startswith("EXPLORATORY_ONLY")


def test_exploratory_preview_rejects_group_crossing(preview_fixture):
    root, rows, save = preview_fixture
    rows[9]["overlap_group"] = rows[0]["overlap_group"]
    save()
    with pytest.raises(ValueError, match="group crosses"):
        exploratory.validate_preview(root)


def test_exploratory_preview_rejects_quarantined_siim(preview_fixture):
    root, rows, save = preview_fixture
    row = next(r for r in rows if r["class_name"] == "BENIGN")
    row["automated_status"] = "QUARANTINE_CANDIDATE_RELATION"
    save()
    with pytest.raises(ValueError, match="SIIM image"):
        exploratory.validate_preview(root)


def test_notebook_is_unexecuted_and_exploratory_only():
    notebook = json.loads((Path(__file__).resolve().parents[1] /
        "notebooks/nine_class_exploratory_colab.ipynb").read_text(encoding="utf-8"))
    assert all(cell.get("execution_count") is None and not cell.get("outputs")
               for cell in notebook["cells"] if cell["cell_type"] == "code")
    assert "EXPLORATORY ONLY" in "".join(notebook["cells"][0]["source"])
