# R3 Uncertainty Estimation Audit

## Implemented methods

`src/nine_class_uncertainty.py` supports nine-class softmax probabilities/logits, confidence, predictive and normalized entropy, top-two margin, labeled NLL, equal-width top-label ECE, multiclass Brier score, bounded temperature scaling, selective prediction, risk-coverage curves, and a guarded calibration fit. `src/nine_class_stage8_analysis.py` consumes approved evaluation artifacts and can write per-image uncertainty, reliability and risk-coverage outputs, optional temperature-scaled metrics, and IQA-calibration quantiles.

The current EG-VAN has no supported `nn.Dropout*` layers; the generic MC-dropout helper therefore raises `NotImplementedError` for this model. Adding stochastic dropout was not attempted.

## What has actually run

`analysis/nine_class_stage8/synthetic_demo/` contains plots and a JSON marker `SYNTHETIC_DEMONSTRATION_ONLY` for 27 constructed probability vectors. Each of the nine labels has support 3 and mean normalized entropy `0.4170218836`; equal values are a construction artifact, not model uncertainty.

The exploratory validation export contains 1,028 per-image nine-class probability vectors. However, no Stage 8 report calculated ECE, Brier score, NLL, temperature, selective risk or reliability from those model predictions. The four-way exploratory split has a 1,023-record calibration partition, but it is explicitly unapproved and has no calibration logits/probability report or frozen calibration approval. It is not an independent research-grade calibration cohort.

## Status

- **Code:** implemented with approval/provenance gates.
- **Demonstration:** synthetic-only plotting output exists.
- **Real-model uncertainty/calibration:** not executed or scientifically validated.
- **Temperature scaling / threshold selection:** no saved model fit/record.
- **Reliability diagram, ECE, Brier, NLL and risk-coverage for EG-VAN:** unavailable.

Do not treat the synthetic outputs or the existence of probability columns as evidence that the model is calibrated or that abstention is safe.
