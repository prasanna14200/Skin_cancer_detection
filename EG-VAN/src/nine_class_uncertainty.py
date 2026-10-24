"""Nine-label uncertainty, calibration, abstention and optional MC dropout math."""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np
import torch
from torch import nn

from nine_class_stage4 import CLASS_NAMES

N_CLASSES = len(CLASS_NAMES)
SCHEMA_VERSION = "nine_class_uncertainty_v1"


def _logits(logits: np.ndarray) -> tuple[np.ndarray, bool]:
    values = np.asarray(logits, dtype=np.float64)
    single = values.ndim == 1
    if single:
        values = values[None, :]
    if values.ndim != 2 or values.shape[1] != N_CLASSES or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Expected finite, nonempty nine-class logits")
    return values, single


def _targets(targets: np.ndarray, size: int) -> np.ndarray:
    values = np.asarray(targets)
    if values.shape != (size,) or not np.issubdtype(values.dtype, np.integer):
        raise ValueError("Targets must be integer labels, one per image")
    if (values < 0).any() or (values >= N_CLASSES).any():
        raise ValueError("Target outside fixed nine-class order")
    return values.astype(np.int64)


def validate_probabilities(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != N_CLASSES or not len(values):
        raise ValueError("Expected nonempty N-by-nine probabilities")
    if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
        raise ValueError("Probabilities must be finite and in [0,1]")
    if not np.allclose(values.sum(axis=1), 1, atol=1e-6):
        raise ValueError("Probability rows must sum to one")
    return values


def softmax_logits(logits: np.ndarray, *, temperature: float = 1.0) -> np.ndarray:
    values, single = _logits(logits)
    if not np.isfinite(temperature) or temperature <= 0:
        raise ValueError("Temperature must be finite and positive")
    scaled = values / temperature
    shifted = scaled - scaled.max(axis=1, keepdims=True)
    exponents = np.exp(shifted)
    result = exponents / exponents.sum(axis=1, keepdims=True)
    return result[0] if single else result


def logits_nll(logits: np.ndarray, targets: np.ndarray, *, temperature: float = 1.0) -> float:
    values, _ = _logits(logits)
    y = _targets(targets, len(values))
    if not np.isfinite(temperature) or temperature <= 0:
        raise ValueError("Temperature must be finite and positive")
    scaled = values / temperature
    maximum = scaled.max(axis=1)
    log_partition = maximum + np.log(np.exp(scaled - maximum[:, None]).sum(axis=1))
    return float(np.mean(log_partition - scaled[np.arange(len(y)), y]))


def probability_nll(probabilities: np.ndarray, targets: np.ndarray) -> float:
    values = validate_probabilities(probabilities)
    y = _targets(targets, len(values))
    # Finite reporting convention for rounded probability artifacts.
    return float(-np.log(np.maximum(values[np.arange(len(y)), y], 1e-15)).mean())


def uncertainty_from_probabilities(probabilities: np.ndarray,
                                   targets: np.ndarray | None = None) -> dict[str, np.ndarray]:
    values = validate_probabilities(probabilities)
    ordered = np.sort(values, axis=1)
    entropy = -np.sum(np.where(values > 0, values * np.log(np.maximum(values, 1e-300)), 0), axis=1)
    result = {"predicted_index": values.argmax(axis=1),
              "confidence": ordered[:, -1],
              "predictive_entropy": entropy,
              "normalized_entropy": entropy / math.log(N_CLASSES),
              "top_two_margin": ordered[:, -1] - ordered[:, -2]}
    if targets is not None:
        y = _targets(targets, len(values))
        result["negative_log_likelihood"] = -np.log(np.maximum(values[np.arange(len(y)), y], 1e-15))
    return result


def uncertainty_from_logits(logits: np.ndarray, targets: np.ndarray | None = None) -> dict[str, np.ndarray]:
    values, _ = _logits(logits)
    result = uncertainty_from_probabilities(softmax_logits(values), targets)
    if targets is not None:
        y = _targets(targets, len(values))
        scaled_max = values.max(axis=1)
        log_partition = scaled_max + np.log(np.exp(values - scaled_max[:, None]).sum(axis=1))
        result["negative_log_likelihood"] = log_partition - values[np.arange(len(y)), y]
    return result


def calibration_metrics(probabilities: np.ndarray, targets: np.ndarray,
                        *, bins: int = 10) -> dict[str, Any]:
    """Equal-width top-label ECE; empty bins carry null accuracy/confidence."""
    values = validate_probabilities(probabilities)
    y = _targets(targets, len(values))
    if not isinstance(bins, int) or bins < 2:
        raise ValueError("At least two ECE bins required")
    confidence = values.max(axis=1)
    correct = (values.argmax(axis=1) == y).astype(float)
    bin_index = np.minimum((confidence * bins).astype(int), bins - 1)
    records, ece = [], 0.0
    for index in range(bins):
        mask = bin_index == index
        count = int(mask.sum())
        accuracy = float(correct[mask].mean()) if count else None
        mean_confidence = float(confidence[mask].mean()) if count else None
        if count:
            ece += count / len(values) * abs(accuracy - mean_confidence)
        records.append({"bin_index": index, "lower_inclusive": index / bins,
                        "upper_exclusive_except_last": (index + 1) / bins,
                        "count": count, "accuracy": accuracy,
                        "mean_confidence": mean_confidence})
    truth = np.eye(N_CLASSES)[y]
    support = np.bincount(y, minlength=N_CLASSES)
    return {"n": len(values), "accuracy": float(correct.mean()),
            "ece": float(ece), "ece_bins": bins, "reliability_bins": records,
            "class_support": {name: int(support[i]) for i, name in enumerate(CLASS_NAMES)},
            "warnings": ["One or more nine-class labels are absent"] if (support == 0).any() else [],
            "multiclass_brier": float(np.mean(np.sum((values - truth) ** 2, axis=1))),
            "negative_log_likelihood": probability_nll(values, y)}


def selective_at_threshold(probabilities: np.ndarray, targets: np.ndarray,
                           threshold: float) -> dict[str, Any]:
    values = validate_probabilities(probabilities)
    y = _targets(targets, len(values))
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Confidence threshold must be in [0,1]")
    confidence = values.max(axis=1)
    accepted = confidence >= threshold
    count = int(accepted.sum())
    accuracy = float((values.argmax(axis=1)[accepted] == y[accepted]).mean()) if count else None
    return {"threshold": float(threshold), "accepted": count, "total": len(values),
            "coverage": count / len(values), "selective_accuracy": accuracy,
            "selective_error_risk": None if accuracy is None else 1 - accuracy}


def risk_coverage_curve(probabilities: np.ndarray, targets: np.ndarray) -> list[dict[str, Any]]:
    values = validate_probabilities(probabilities)
    y = _targets(targets, len(values))
    confidence = values.max(axis=1)
    order = np.argsort(-confidence, kind="stable")
    cumulative_correct = np.cumsum(values.argmax(axis=1)[order] == y[order])
    return [{"accepted": 0, "coverage": 0.0, "selective_accuracy": None,
             "selective_error_risk": None}] + [
        {"accepted": k, "coverage": k / len(values),
         "selective_accuracy": float(cumulative_correct[k - 1] / k),
         "selective_error_risk": float(1 - cumulative_correct[k - 1] / k)}
        for k in range(1, len(values) + 1)]


def select_threshold_on_validation(probabilities: np.ndarray, targets: np.ndarray,
                                   *, minimum_coverage: float, partition: str) -> dict[str, Any]:
    if partition not in ("validation", "calibration"):
        raise ValueError("Threshold selection is forbidden on final test")
    if not 0 < minimum_coverage <= 1:
        raise ValueError("Minimum coverage must be in (0,1]")
    values = validate_probabilities(probabilities)
    _targets(targets, len(values))
    confidence = np.sort(np.unique(values.max(axis=1)))[::-1]
    choices = [selective_at_threshold(values, targets, float(t)) for t in confidence]
    eligible = [r for r in choices if r["coverage"] >= minimum_coverage]
    selected = min(eligible, key=lambda r: (r["selective_error_risk"], -r["coverage"], -r["threshold"]))
    return {"selection_partition": partition, "minimum_coverage": minimum_coverage, **selected}


def fit_temperature(logits: np.ndarray, targets: np.ndarray, *,
                    log_temperature_bounds: tuple[float, float] = (math.log(0.05), math.log(10)),
                    iterations: int = 120) -> dict[str, float | int]:
    """Deterministic bounded golden-section minimization of labeled NLL."""
    values, _ = _logits(logits)
    y = _targets(targets, len(values))
    low, high = log_temperature_bounds
    if not np.isfinite((low, high)).all() or low >= high or iterations < 1:
        raise ValueError("Invalid temperature optimization settings")
    ratio = (math.sqrt(5) - 1) / 2
    left, right = high - ratio * (high - low), low + ratio * (high - low)
    f_left, f_right = logits_nll(values, y, temperature=math.exp(left)), logits_nll(values, y, temperature=math.exp(right))
    for _ in range(iterations):
        if f_left <= f_right:
            high, right, f_right = right, left, f_left
            left = high - ratio * (high - low)
            f_left = logits_nll(values, y, temperature=math.exp(left))
        else:
            low, left, f_left = left, right, f_right
            right = low + ratio * (high - low)
            f_right = logits_nll(values, y, temperature=math.exp(right))
    optimum = math.exp((low + high) / 2)
    return {"temperature": optimum, "nll_before": logits_nll(values, y),
            "nll_on_fit_data": logits_nll(values, y, temperature=optimum),
            "iterations": iterations, "log_temperature_lower": log_temperature_bounds[0],
            "log_temperature_upper": log_temperature_bounds[1]}


def calibration_array_sha256(logits: np.ndarray, targets: np.ndarray) -> str:
    values, _ = _logits(logits)
    y = _targets(targets, len(values))
    digest = hashlib.sha256()
    digest.update(np.asarray(values.shape, dtype="<i8").tobytes())
    digest.update(np.asarray(values, dtype="<f8").tobytes())
    digest.update(np.asarray(y, dtype="<i8").tobytes())
    return digest.hexdigest()


def fit_temperature_guarded(logits: np.ndarray, targets: np.ndarray, *,
                            partition: str, approval: dict, approval_file_sha256: str,
                            checkpoint_sha256: str,
                            allow_synthetic_fixture: bool = False) -> dict[str, Any]:
    """A future calibration manifest must independently substantiate these declarations."""
    if partition != "calibration" or approval.get("approval_status") != "APPROVED_BY_RESEARCHER":
        raise ValueError("Temperature fit requires an approved calibration partition")
    if approval.get("synthetic_fixture") and not allow_synthetic_fixture:
        raise ValueError("Synthetic approval cannot authorize a production fit")
    if not approval.get("calibration_partition_frozen") or not approval.get("calibration_separate_from_model_selection"):
        raise ValueError("Calibration partition must be frozen and separate from model selection")
    calibration_data_sha256 = calibration_array_sha256(logits, targets)
    if approval.get("calibration_data_sha256") != calibration_data_sha256 or not checkpoint_sha256 or not approval_file_sha256:
        raise ValueError("Calibration data or checkpoint provenance is missing or mismatched")
    result = fit_temperature(logits, targets)
    return {"schema_version": SCHEMA_VERSION, "fit_partition": partition,
            "calibration_data_sha256": calibration_data_sha256,
            "checkpoint_sha256": checkpoint_sha256, "approval_sha256": approval_file_sha256,
            **result}


def apply_temperature_to_probabilities(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    """Equivalent to logit scaling only when exported probabilities are nonzero."""
    values = validate_probabilities(probabilities)
    if (values <= 0).any():
        raise ValueError("Zero exported probability lost the logit needed for temperature scaling")
    return softmax_logits(np.log(values), temperature=temperature)


def mc_dropout_probabilities(model: nn.Module, images: torch.Tensor,
                             *, passes: int = 20) -> dict[str, torch.Tensor]:
    """Generic helper; the current nine-class EG-VAN has no dropout modules."""
    dropouts = tuple(module for module in model.modules()
                     if isinstance(module, (nn.Dropout, nn.Dropout1d, nn.Dropout2d, nn.Dropout3d)))
    if not dropouts:
        raise NotImplementedError("Current model has no supported dropout layers")
    if passes < 2 or images.ndim < 2:
        raise ValueError("At least two passes and a batched input are required")
    states = [(module, module.training) for module in model.modules()]
    try:
        model.eval()
        for module in dropouts:
            module.train()
        with torch.inference_mode():
            samples = []
            for _ in range(passes):
                logits = model(images)
                if logits.ndim != 2 or logits.shape[1] != N_CLASSES:
                    raise ValueError("MC dropout model must produce B-by-nine logits")
                samples.append(torch.softmax(logits.float(), dim=1))
            stacked = torch.stack(samples)
        mean = stacked.mean(dim=0)
        predictive_entropy = -(mean * mean.clamp_min(1e-12).log()).sum(dim=1)
        expected_entropy = -(stacked * stacked.clamp_min(1e-12).log()).sum(dim=2).mean(dim=0)
        return {"mean_probabilities": mean, "predictive_entropy": predictive_entropy,
                "expected_entropy": expected_entropy,
                "mutual_information": (predictive_entropy - expected_entropy).clamp_min(0)}
    finally:
        for module, previous in states:
            module.training = previous
