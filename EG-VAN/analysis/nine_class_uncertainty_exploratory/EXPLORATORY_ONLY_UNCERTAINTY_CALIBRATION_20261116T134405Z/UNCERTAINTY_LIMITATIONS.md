# Limitations

- **EXPLORATORY / NON-CLINICAL.** All source records remain unapproved. No cohort readiness, clinical validity, leakage-safe evaluation, or paper reproduction is claimed.
- Predictions are from a single saved validation artifact; there was no new inference, model training, fine-tuning, or external validation.
- The saved file contains probabilities and hard labels, not logits. Probability-based metrics are calculated, but logits-based analysis is unavailable.
- The split includes 1,023 calibration rows, but they are not approved and have no saved prediction probabilities/logits. Temperature scaling or any other calibration fit was intentionally omitted; fitting on validation would reuse evaluation labels and bias the reported results.
- The model predicts NV for 1,012 of 1,028 validation rows. Overall calibration is dominated by that class; seven classes have no predicted examples. The one MALIGNANT prediction is insufficient for class-level inference.
- A 10-bin top-label ECE can hide class-wise errors, depends on binning, and is not a proper standalone calibration guarantee. The Brier and NLL values are likewise split-specific.
- Recorded overlap groups repeat within validation. Cluster bootstrap intervals use the recorded `(source_dataset, overlap_group)` units, but group correctness/completeness and other patient/image dependencies are unverified. Image-level rank-test p-values are not cluster-adjusted.
- 84 Fanconic records lack source image IDs in the split; exact source-qualified paths and source hashes are available. No IDs were invented.
- High observed accuracy at strict confidence thresholds applies only to the same unapproved validation artifact. No abstention threshold has been independently selected, calibrated, or prospectively validated.
- MC dropout is not applicable to the current architecture according to the existing project audit/helper; no stochastic uncertainty model was added.
- Uncertainty scores can rank errors empirically here but do not determine causality, clinical risk, or whether any image is safe to accept.
