# Stage 8: uncertainty estimation and calibration

Date: 2026-10-22. This stage provides software for the fixed nine source-defined outputs `AKIEC, BCC, BKL, DF, MEL, NV, VASC, BENIGN, MALIGNANT`. It uses the Stage 6 prediction schema and Stage 7 source-qualified IQA schema. There is **no approved training cohort, trained nine-class checkpoint, calibration partition or clinical prediction artifact**. The generated figures are explicitly synthetic demonstrations, not EG-VAN results. [Stage 6](NINE_CLASS_STAGE6_TRAINING_READINESS.md) eligibility gates and [Stage 7](NINE_CLASS_STAGE7_IQA.md) preprocessing concerns remain in force.

## Mathematical definitions and direction

For nine logits `z`, `p_k = exp(z_k/T) / Σ_j exp(z_j/T)` with max-subtraction for numerical stability. `T=1` is uncalibrated. The [core module](../src/nine_class_uncertainty.py) checks finite inputs, fixed nine-column shape, valid label indices and probability normalization. A batch of one is supported.

| Measure | Definition | Interpretation and limit |
| --- | --- | --- |
| Maximum probability | `max_k p_k` | Higher is greater model confidence, **not** a guaranteed chance of correctness. |
| Predictive entropy | `−Σ_k p_k ln p_k` | Higher is more diffuse prediction; range 0 to `ln(9)`. |
| Normalized entropy | Predictive entropy divided by `ln(9)` | Higher is more diffuse; range 0 to 1. |
| Top-two margin | Largest minus second-largest class probability | Smaller margin indicates closer top choices. |
| Labeled negative log-likelihood | `−ln p_true` | Lower is better for labeled cases. Computed by stable log-sum-exp from logits; exported probability calculations clip true-class probability at `1e−15` solely for finite reporting. |

These are predictive-distribution summaries, not a separation of model uncertainty from data uncertainty. In particular, softmax can be confidently wrong under distribution shift or source cues.

## Calibration metrics

The implementation reports top-label **Expected Calibration Error (ECE)** with 10 equal-width confidence bins by default. A confidence exactly 1 enters the last bin; other bins are `[b/B,(b+1)/B)`. For each occupied bin, it compares mean confidence with observed accuracy and weights the absolute gap by `n_bin/N`. Empty bins have null accuracy/confidence and zero contribution. The reliability diagram plots occupied bins against the diagonal. ECE depends on bin count, sample composition and finite-sample noise; it can obscure class-specific miscalibration and is not a proof of reliability.

The multiclass Brier score is the mean over images of `Σ_k (p_k − 1[y=k])²` (no division by nine). NLL is the mean true-class negative log probability. Accuracy, per-class support and missing-class warnings accompany these metrics. Missing classes do not fabricate support; a genuine final nine-class test must still satisfy the Stage 6 all-class gate. Accuracy-versus-confidence is available through the reliability bins and selective summaries.

## Temperature scaling protocol

The low-level fitter minimizes labeled NLL over `log(T)` using deterministic bounded golden-section search (`T` from 0.05 to 10, 120 iterations). It returns the fitted temperature, fit-data NLL before/after, bounds and iteration count. This is **fit-data optimization only**, never evidence of unseen-data improvement. A separate guarded API requires an approved, frozen `calibration` partition declared separate from model selection, a SHA-256 of the exact calibration logits/targets, the approval-file hash and checkpoint hash. Synthetic approvals are refused in production. The exact calibration manifest and reviewer evidence must substantiate the approval record; JSON declarations alone cannot prove independence.

The current Stage 6 manifest supports only train, validation and test, so **production temperature fitting is disabled until a separate calibration partition and logit artifact are approved and added to the protocol**. The Stage 6 CSV exports probabilities, not raw logits. An already fitted, approved temperature can be applied to positive exported probabilities by `softmax(log(p)/T)`; zero exported probabilities are rejected because the original logit magnitude was lost. The [future analysis runner](../src/nine_class_stage8_analysis.py) checks that a frozen calibration record matches the approved checkpoint and cohort, preserves the uncalibrated predictions, and reports calibrated metrics separately. It never fits on test or silently replaces the original probabilities.

## Selective prediction

At a predeclared confidence threshold `τ`, accept images with `max(p) ≥ τ`. Coverage is accepted count divided by total count; selective accuracy is correctness among accepted images; selective error risk is `1 − selective accuracy`. When no image is accepted, accuracy and risk are null, not zero. The risk–coverage curve orders predictions by decreasing confidence with stable tie order and includes an explicit zero-coverage point. The threshold selector searches observed confidence cutoffs for the lowest observed selective risk subject to a minimum coverage, **only** when the partition role is validation or calibration. It rejects a test role. This is exploratory selection and can overfit validation; a frozen threshold record stores the chosen value and cohort/checkpoint hashes before application to test. The present selector and curve always use **uncalibrated Stage 6 probabilities**, even when calibrated metrics are also reported. Abstention has no demonstrated clinical safety benefit here.

## MC dropout status

The current nine-class EG-VAN assembly has **zero `nn.Dropout*` modules** and 167 BatchNorm modules in the local construction probe. Its EfficientNet feature extractor omits the classifier dropout; stochastic-depth behavior is a different mechanism and remains in evaluation mode. Accordingly, MC dropout is **unsupported for the present EG-VAN architecture**. No arbitrary dropout was added. A generic [helper](../src/nine_class_uncertainty.py) is tested on a small synthetic model that *does* contain dropout: it activates dropout only, keeps BatchNorm in evaluation mode, restores all original module states, and returns mean probabilities, predictive entropy, expected entropy and their nonnegative difference (mutual information). Those quantities are only interpretable for a suitable stochastic predictive model and do not establish epistemic uncertainty for this EG-VAN build.

## Approved-artifact analysis and Stage 7 IQA join

The [Stage 8 analysis runner](../src/nine_class_stage8_analysis.py) reuses Stage 7's Stage 6 artifact gate. It requires a real approved split and approval, matching manifest/approval/checkpoint hashes, complete and label-consistent predictions, and `--final-test` for an approved frozen nine-class test. It joins Stage 7 IQA by `(source_dataset, image_path)` and verifies original image SHA-256. It writes the original nine probabilities alongside per-image uncertainty, optional separate calibrated probabilities, calibration summaries, plots and provenance to a new output directory. With a complete IQA table it can later study quality versus entropy, confidence and error; it writes calibration metrics by equal-count quality rank for five primary proxies. Groups under 20 cases are flagged because their ECE estimates are particularly unstable. The Stage 7 performance module provides additional quality quantiles and class distributions. Associations remain observational and may be confounded by class/source composition.

Future validation command, **only after Stage 6 approval, training and evaluation**:

```powershell
python src/nine_class_stage8_analysis.py --approved-split PATH_TO_APPROVED_SPLIT.csv --approval PATH_TO_REAL_APPROVAL.json --inventory PATH_TO_APPROVED_INVENTORY.csv --evaluation-dir PATH_TO_STAGE6_VALIDATION_EVALUATION --output-dir PATH_TO_NEW_STAGE8_VALIDATION_OUTPUT
```

Optional `--iqa-csv PATH_TO_COMPLETE_IQA_FEATURES.csv --iqa-view raw` enables the hash-checked join. `--choose-minimum-coverage 0.8` may select a validation-only abstention threshold and emits `selected_threshold.json`. A later protected-test run must use its frozen record with `--threshold-record PATH_TO_SELECTED_THRESHOLD.json --final-test`; it cannot select a threshold on test. A future approved temperature file may be supplied with `--temperature-record`, after a separate calibration partition exists. No such files exist now.

## Synthetic visualizations and tests

The [synthetic demo directory](../analysis/nine_class_stage8/synthetic_demo) contains a confidence histogram, normalized-entropy distribution, reliability diagram, risk–coverage curve, per-class uncertainty plot and a JSON marker `SYNTHETIC_DEMONSTRATION_ONLY`. Its 27 constructed probability vectors have no relation to EG-VAN or skin images. Reproduce in a new directory:

```powershell
python src/nine_class_stage8_analysis.py --synthetic-demo --output-dir analysis/nine_class_stage8/NEW_SYNTHETIC_DEMO
```

`tests/test_nine_class_stage8.py` checks uniform and dominant logits, maximum entropy, extreme-logit stability, batch-one shape, ECE/Brier/NLL formulas, missing classes, bounded temperature fitting and test-partition rejection, selective coverage and zero-accepted handling, dropout/BatchNorm state restoration, unsupported no-dropout models and no-overwrite synthetic plotting. The Stage 7 artifact tests separately verify source-qualified IQA joining and rejection of missing/incompatible evaluation evidence. No checkpoint, original photograph or clinical prediction is used in Stage 8 tests.

## Stage 9 handoff

**Software readiness:** deterministic uncertainty, calibration metrics, selective analysis and approved-artifact gates are prepared. **Experimental reliability:** unmeasured. Stage 9 external validation should require a frozen trained checkpoint, a clinically and legally documented external cohort, nonoverlap checks, compatible nine-label mapping, and predeclared calibration/abstention settings. Report unsupported classes and shifts explicitly. Resolve the Stage 7 Retinex tonal-change concern before drawing conclusions from the current processed-image path. Do not treat synthetic figures or validation-only tuning as external clinical evidence.
