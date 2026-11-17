# Methodology

**EXPLORATORY / NON-CLINICAL; cohort not approved; not a paper reproduction.**

## Inputs and matching

The analysis reuses the saved validation prediction CSV containing nine softmax probabilities, true and predicted labels, and source-qualified image paths. Each row is joined to the unchanged validation split by `(source_dataset, image_path)`. The split supplies original source image ID, class index/name, image hash, and overlap-group metadata. The frozen run verifier checks the recorded checkpoint, configuration, split, preprocessing, source-preview, and run-provenance identities. Image files were decoded and rehashed against the frozen split. No checkpoint weights were loaded for inference.

## Probability-based metrics

The existing `nine_class_uncertainty.py` implementations were reused:

- Confidence: maximum class probability.
- Predictive entropy: `-sum(p * log(p))` in nats; normalized entropy divides by `log(9)`.
- Top-two margin: largest probability minus second-largest probability.
- Top-label calibration: equal-width, 10-bin expected calibration error (ECE), as implemented by `calibration_metrics`. The last bin includes confidence 1. Empty bins are retained with null accuracy/confidence.
- Multiclass Brier score: mean per-image sum of squared differences between the nine probabilities and one-hot target.
- Negative log-likelihood: mean negative log target probability, clipped below at `1e-15` per the helper's reporting convention.

Class-wise calibration is also reported as one-vs-rest equal-width 10-bin ECE/Brier for each class. A separate predicted-class-conditional reliability summary reports the accuracy and confidence among rows predicted as each class. Sparse and absent predicted classes are explicitly represented.

## Error detection and selective prediction

Three scores available at prediction time are evaluated for detecting incorrect predictions: `1 - confidence`, normalized entropy, and `1 - top-two margin`. AUROC, average precision, error/correct medians, Mann-Whitney comparisons, and Holm-adjusted p-values across the three scores are reported. Precision-recall average precision is compared with the observed error prevalence.

Risk-coverage curves retain images in descending confidence, ascending entropy, or descending margin order. The fixed confidence thresholds in the accompanying CSV are descriptive points, not selected operating thresholds. Ground truth is used only to score validation outcomes; no threshold is fit or recommended.

## Uncertainty intervals

Percentile 95% intervals are calculated from 1,000 deterministic bootstrap replicates, resampling validation overlap-group clusters defined by `(source_dataset, overlap_group)` with seed `20261116`. This accounts for the recorded grouping only; unrecorded dependencies and invalid or incomplete group definitions may remain. Mann-Whitney p-values use image-level ranks and are descriptive, not confirmatory.
