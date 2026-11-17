# Exploratory uncertainty and calibration experiment

**EXPLORATORY / NON-CLINICAL.** The cohort is not approved. This is not a clinical validation or an exact reproduction of the EG-VAN paper.

## Result

The existing 1,028 saved validation probability vectors were verified against the frozen validation split and checkpoint provenance. Existing uncertainty helpers were used; no training, fine-tuning, model inference, or split modification was performed.

- Accuracy: **0.6109** (628 correct, 400 incorrect).
- Ten-bin equal-width top-label ECE: **0.0431**.
- Multiclass Brier score: **0.5177**.
- Probability negative log-likelihood: **1.1513 nats**.
- Mean confidence: **0.5824**; mean predictive entropy: **1.2414 nats** (normalized: **0.5650**).
- Error-detection AUROC was **0.787** for 1-confidence, **0.798** for normalized entropy, and **0.771** for 1-top-two-margin. These scores rank errors better than chance on this split, but do not establish safe abstention.
- The classifier predicted NV for **1,012/1,028** images. Aggregate calibration is therefore dominated by one predicted class and must not be interpreted as reliable class-wide calibration.

## Calibration and thresholding limits

The existing split has 1,023 calibration-partition records, but they are `NOT_APPROVED` and have no saved prediction probabilities or logits. No temperature or other calibration fit was performed. The validation partition was used only for exploratory evaluation, not for fitting or selecting a threshold. Fixed confidence-threshold and risk-coverage results are descriptive and not deployed or validated operating points.

The saved artifact contains probabilities, not logits. Probability-based confidence, entropy, ECE, Brier score, and NLL are available; a logits-based evaluation is not. MC dropout was not run because project audits and the existing helper document that the model has no supported dropout layers.

## What ran / did not run

**Ran:** artifact and image provenance audit; probability validation; confidence, entropy, margin, calibration, class-wise reliability, error ranking, and risk-coverage analyses; cluster bootstrap intervals; plots; independent package and source-hash validation.

**Did not run:** training, fine-tuning, inference, calibration fitting, MC dropout, threshold optimization, external validation, cohort approval, or clinical assessment.

See `UNCERTAINTY_STATISTICAL_ANALYSIS.md`, `UNCERTAINTY_METHODOLOGY.md`, `UNCERTAINTY_LIMITATIONS.md`, `UNCERTAINTY_REPRODUCIBILITY.md`, and `UNCERTAINTY_VALIDATION.md` for definitions, caveats, and verification details.
