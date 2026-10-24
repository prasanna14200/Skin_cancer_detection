"""Synthetic-only uncertainty, calibration, abstention and state tests."""

import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nine_class_stage4 import CLASS_NAMES
from nine_class_stage8_analysis import quality_group_calibration, run, synthetic_demo
from nine_class_uncertainty import (apply_temperature_to_probabilities, calibration_array_sha256,
                                    calibration_metrics, fit_temperature, fit_temperature_guarded,
                                    logits_nll, mc_dropout_probabilities, risk_coverage_curve,
                                    select_threshold_on_validation, selective_at_threshold,
                                    softmax_logits, uncertainty_from_logits,
                                    uncertainty_from_probabilities)


def test_nine_logits_entropy_margin_batch_one_and_extremes():
    assert CLASS_NAMES == ("AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT")
    uniform = softmax_logits(np.zeros(9))
    assert uniform.shape == (9,) and np.allclose(uniform, 1 / 9)
    uniform_uncertainty = uncertainty_from_logits(np.zeros((1, 9)), np.array([8]))
    assert uniform_uncertainty["normalized_entropy"].shape == (1,)
    assert uniform_uncertainty["normalized_entropy"][0] == pytest.approx(1)
    assert uniform_uncertainty["top_two_margin"][0] == pytest.approx(0)
    dominant = np.zeros((1, 9))
    dominant[0, 8] = 50
    result = uncertainty_from_logits(dominant, np.array([8]))
    assert result["normalized_entropy"][0] < 0.01
    assert result["confidence"][0] > 0.99 and result["negative_log_likelihood"][0] >= 0
    extreme = softmax_logits(np.array([[1000.0] + [-1000.0] * 8]))
    assert np.isfinite(extreme).all() and extreme.sum() == pytest.approx(1)
    assert np.isfinite(logits_nll(np.array([[1000.0] + [-1000.0] * 8]), np.array([8])))
    with pytest.raises(ValueError):
        softmax_logits(np.full((1, 9), np.nan))
    with pytest.raises(ValueError):
        softmax_logits(np.zeros((1, 8)))


def test_ece_brier_nll_and_missing_class_warning():
    probabilities = np.full((2, 9), 0.2 / 8)
    probabilities[0, 0] = 0.8
    probabilities[1] = 0.4 / 8
    probabilities[1, 1] = 0.6
    targets = np.array([0, 0])
    metrics = calibration_metrics(probabilities, targets, bins=2)
    assert metrics["ece"] == pytest.approx(0.2)
    expected_brier = np.mean(np.sum((probabilities - np.eye(9)[targets]) ** 2, axis=1))
    assert metrics["multiclass_brier"] == pytest.approx(expected_brier)
    assert metrics["negative_log_likelihood"] == pytest.approx(-np.log([0.8, 0.05]).mean())
    assert metrics["class_support"]["MALIGNANT"] == 0 and metrics["warnings"]
    assert metrics["reliability_bins"][0]["count"] == 0
    with pytest.raises(ValueError):
        calibration_metrics(np.zeros((0, 9)), np.array([], dtype=int))


def test_temperature_fit_and_partition_gate():
    logits = np.tile(np.array([5.0] + [0.0] * 8), (18, 1))
    targets = np.tile(np.arange(9), 2)
    fitted = fit_temperature(logits, targets)
    assert fitted["temperature"] > 0
    assert fitted["nll_on_fit_data"] <= fitted["nll_before"] + 1e-8
    probabilities = softmax_logits(logits)
    scaled = apply_temperature_to_probabilities(probabilities, fitted["temperature"])
    assert np.allclose(scaled, softmax_logits(logits, temperature=fitted["temperature"]))
    approval = {"synthetic_fixture": True, "approval_status": "APPROVED_BY_RESEARCHER",
                "calibration_partition_frozen": True,
                "calibration_separate_from_model_selection": True,
                "calibration_data_sha256": calibration_array_sha256(logits, targets)}
    with pytest.raises(ValueError, match="approved calibration"):
        fit_temperature_guarded(logits, targets, partition="test", approval=approval,
                                approval_file_sha256="fixture", checkpoint_sha256="fixture")
    with pytest.raises(ValueError, match="Synthetic approval"):
        fit_temperature_guarded(logits, targets, partition="calibration", approval=approval,
                                approval_file_sha256="fixture", checkpoint_sha256="fixture")
    record = fit_temperature_guarded(logits, targets, partition="calibration", approval=approval,
                                     approval_file_sha256="fixture", checkpoint_sha256="fixture",
                                     allow_synthetic_fixture=True)
    assert record["fit_partition"] == "calibration" and record["calibration_data_sha256"] == approval["calibration_data_sha256"]
    with pytest.raises(ValueError, match="Zero exported probability"):
        apply_temperature_to_probabilities(np.eye(9), 2.0)


def test_selective_coverage_empty_subset_and_test_selection_rejected():
    probabilities = np.full((3, 9), 0.1 / 8)
    probabilities[0, 0] = 0.9
    probabilities[1] = 0.4 / 8
    probabilities[1, 1] = 0.6
    probabilities[2] = 0.6 / 8
    probabilities[2, 2] = 0.4
    targets = np.array([0, 0, 2])
    threshold = selective_at_threshold(probabilities, targets, 0.6)
    assert threshold["accepted"] == 2 and threshold["coverage"] == pytest.approx(2 / 3)
    assert threshold["selective_accuracy"] == 0.5 and threshold["selective_error_risk"] == 0.5
    empty = selective_at_threshold(probabilities, targets, 1.0)
    assert empty["coverage"] == 0 and empty["selective_accuracy"] is None and empty["selective_error_risk"] is None
    curve = risk_coverage_curve(probabilities, targets)
    assert len(curve) == 4 and curve[0]["selective_error_risk"] is None and curve[-1]["coverage"] == 1
    selected = select_threshold_on_validation(probabilities, targets, minimum_coverage=2 / 3,
                                              partition="validation")
    assert selected["coverage"] >= 2 / 3
    with pytest.raises(ValueError, match="forbidden"):
        select_threshold_on_validation(probabilities, targets, minimum_coverage=0.5, partition="test")


def test_mc_dropout_restores_dropout_and_batchnorm_states():
    class Tiny(nn.Module):
        def __init__(self):
            super().__init__()
            self.bn = nn.BatchNorm1d(4)
            self.dropout = nn.Dropout(0.5)
            self.head = nn.Linear(4, 9)

        def forward(self, image):
            assert not self.bn.training
            return self.head(self.dropout(self.bn(image)))

    model = Tiny()
    model.train()
    before = [module.training for module in model.modules()]
    result = mc_dropout_probabilities(model, torch.ones(3, 4), passes=5)
    assert result["mean_probabilities"].shape == (3, 9)
    assert torch.allclose(result["mean_probabilities"].sum(dim=1), torch.ones(3))
    assert torch.all(result["mutual_information"] >= 0)
    assert [module.training for module in model.modules()] == before
    with pytest.raises(NotImplementedError, match="no supported dropout"):
        mc_dropout_probabilities(nn.Linear(4, 9), torch.ones(1, 4))


def test_synthetic_plots_only_and_no_overwrite(tmp_path):
    destination = tmp_path / "synthetic_demo"
    result = synthetic_demo(destination)
    assert result["status"] == "SYNTHETIC_DEMONSTRATION_ONLY"
    assert len(result["figures"]) == 5
    assert all((destination / name).is_file() for name in result["figures"])
    with pytest.raises(FileExistsError):
        synthetic_demo(destination)


def test_iqa_group_calibration_alignment_and_small_group_warning():
    probabilities = np.full((9, 9), 0.1 / 8)
    np.fill_diagonal(probabilities, 0.9)
    quality = [{"source_dataset": "SYNTHETIC", "image_path": f"{i}.jpg",
                **{feature: float(i) for feature in (
                    "sharpness_laplacian_variance", "brightness_mean", "contrast_std",
                    "underexposed_fraction", "overexposed_fraction")}}
               for i in range(9)]
    result = quality_group_calibration(quality, probabilities, np.arange(9))
    assert sum(r["n"] for r in result if r["feature"] == "brightness_mean") == 9
    assert all(r["small_group_warning"] for r in result)
    with pytest.raises(ValueError, match="align"):
        quality_group_calibration(quality[:-1], probabilities, np.arange(9))


def test_stage8_runner_rejects_missing_approved_artifacts(tmp_path):
    with pytest.raises(FileNotFoundError):
        run(tmp_path, tmp_path / "missing_split.csv", tmp_path / "missing_approval.json",
            tmp_path / "missing_inventory.csv", tmp_path / "missing_evaluation",
            tmp_path / "must_not_be_created")
    assert not (tmp_path / "must_not_be_created").exists()
