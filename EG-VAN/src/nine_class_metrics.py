"""Nine-class metrics with explicit incomplete-test reporting."""

from __future__ import annotations

import numpy as np

from nine_class_stage4 import CLASS_NAMES


def summarize_predictions(probabilities: np.ndarray, targets: np.ndarray,
                          *, split: str, low_support_threshold: int = 5) -> dict:
    probabilities = np.asarray(probabilities, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.int64)
    if probabilities.ndim != 2 or probabilities.shape[1] != len(CLASS_NAMES):
        raise ValueError("Probabilities must have nine columns")
    if targets.shape != (len(probabilities),) or len(targets) == 0:
        raise ValueError("Targets must match nonempty predictions")
    if not np.isfinite(probabilities).all() or (probabilities < 0).any() or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-5):
        raise ValueError("Invalid probabilities")
    if (targets < 0).any() or (targets >= len(CLASS_NAMES)).any():
        raise ValueError("Target outside nine-class mapping")
    predicted = probabilities.argmax(axis=1)
    matrix = np.zeros((9, 9), dtype=np.int64)
    np.add.at(matrix, (targets, predicted), 1)
    support = matrix.sum(axis=1)
    predicted_count = matrix.sum(axis=0)
    true_positive = matrix.diagonal()
    precision = np.divide(true_positive, predicted_count, out=np.zeros(9, dtype=float), where=predicted_count > 0)
    recall = np.divide(true_positive, support, out=np.zeros(9, dtype=float), where=support > 0)
    f1 = np.divide(2 * precision * recall, precision + recall,
                   out=np.zeros(9, dtype=float), where=precision + recall > 0)
    complete = bool((support > 0).all())
    warnings = []
    if not complete:
        warnings.append("One or more nine-class labels have zero support")
    low = [name for name, count in zip(CLASS_NAMES, support) if 0 < count < low_support_threshold]
    if low:
        warnings.append("Low class support (<%d): %s" % (low_support_threshold, ", ".join(low)))
    accuracy = float((predicted == targets).mean())
    return {
        "split": split,
        "n_samples": len(targets),
        "all_nine_classes_present": complete,
        "accuracy": None if split == "test" and not complete else accuracy,
        "macro_f1": float(f1.mean()),
        "weighted_f1": float(np.average(f1, weights=support)),
        "per_class": {name: {"precision": float(precision[i]), "recall": float(recall[i]),
                             "f1": float(f1[i]), "support": int(support[i])}
                      for i, name in enumerate(CLASS_NAMES)},
        "confusion_matrix": matrix.tolist(),
        "warnings": warnings,
    }
