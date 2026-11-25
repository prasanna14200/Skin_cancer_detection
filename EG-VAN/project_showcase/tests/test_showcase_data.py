from __future__ import annotations

import sys
from pathlib import Path

import pytest

SHOWCASE = Path(__file__).resolve().parents[1]
ROOT = SHOWCASE.parent
sys.path.insert(0, str(SHOWCASE))

from showcase_data import CLASS_NAMES, get_validation_metrics, project_path  # noqa: E402


def test_validation_metrics_are_loaded_from_saved_evidence():
    metrics = get_validation_metrics()
    assert metrics["n_samples"] == 1028
    assert metrics["correct"] == 628
    assert metrics["incorrect"] == 400
    assert metrics["predicted_nv"] == 1012
    assert metrics["accuracy"] == pytest.approx(0.6108949416342413)
    assert metrics["macro_f1"] == pytest.approx(0.0975323660847642)


def test_architecture_sources_and_synthetic_probe_exist():
    required = (
        "src/models/egvan/egvan.py",
        "src/models/egvan/efficientnet_branch.py",
        "src/models/egvan/modified_resnet50.py",
        "src/models/egvan/scga.py",
        "src/models/egvan/non_local.py",
        "src/models/egvan/mff.py",
        "analysis/nine_class_stage5/architecture_probe.json",
    )
    assert len(CLASS_NAMES) == 9
    assert all(project_path(path).is_file() for path in required)


def test_evidence_paths_cannot_escape_repository():
    with pytest.raises(ValueError):
        project_path("..\\outside.txt")
    assert ROOT in project_path("analysis/nine_class_stage5/architecture_probe.json").parents


def test_exact_eight_page_structure_and_no_unverified_overview_accuracy():
    pages = sorted((SHOWCASE / "pages").glob("*.py"))
    names = [page.name for page in pages]
    assert len(pages) == 7
    assert "1_EG-VAN_Reconstruction_Explorer.py" in names
    assert "2_Image_Prediction_Demo.py" in names
    assert all(f"{number}_{suffix}" in names for number, suffix in [
        ("4", "Image_Quality_Assessment.py"),
        ("5", "Uncertainty & Calibration.py"),
        ("6", "External_Validation.py"),
        ("7", "Research_Workflow.py"),
        ("8", "Results_and_Limitations.py"),
    ])
    home = (SHOWCASE / "Home.py").read_text(encoding="utf-8")
    assert "61.09%" in home
    assert "80.09%" not in home


def test_illustrative_80_percent_demo_is_separate_from_saved_accuracy():
    home = (SHOWCASE / "Home.py").read_text(encoding="utf-8")
    styles = (SHOWCASE / "assets" / "style.css").read_text(encoding="utf-8")

    assert "Illustrative Presentation Demo — Not Actual Measured Accuracy" in home
    assert '"61.09%"' in home
    assert 'aria-valuenow="80"' in home
    assert 'aria-label="Illustrative indicator: 80 percent"' in home
    assert 'aria-label="Illustrative chart: presentation demo, 80 percent"' in home
    assert ".illustrative-progress-fill" in styles
    assert ".illustrative-ring" in styles
    assert ".illustrative-chart-fill" in styles
    assert "width: 80%;" in styles
