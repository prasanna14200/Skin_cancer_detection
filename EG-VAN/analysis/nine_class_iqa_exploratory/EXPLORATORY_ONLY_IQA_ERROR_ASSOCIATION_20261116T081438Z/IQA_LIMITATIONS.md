# Limitations

- **EXPLORATORY / NON-CLINICAL.** The cohort and validation split are not approved; no research readiness or clinical validity is established. This is not an exact paper reproduction.
- The analysis reuses prior saved predictions; it does not rerun inference. Existing saved validation metrics are 1,028 samples, accuracy 0.610895, macro-F1 0.097532; these are prior exploratory values, not newly generated model results.
- The model predicted NV for 1012/1,028 rows. Per-class correctness groups are sparse; only classes with at least two correct and two incorrect examples receive within-class tests.
- Source labels remain as recorded in the exploratory split; HAM diagnoses, SIIM BENIGN, and Fanconic MALIGNANT were not reconciled into new equivalences.
- 84 Fanconic records have no recorded source `image_id`, `lesion_id`, or `patient_id`; they are linked only by their source-qualified file paths and verified SHA-256. No identity was invented.
- There are 192 overlap-group values repeated within validation, covering 429 records. Patient-level independence and leakage-safe partitioning are not established; nominal Mann-Whitney p/q values are not confirmatory.
- No exact-byte duplicate hashes occurred among the 1,028 validation images, but this does not establish photographic independence or resolve near-duplicate/source-test conflicts.
- IQA values are raw-image proxies measured before model resizing/normalization; quality association is not causal and no clinical usability threshold is implied.
- The prior Stage 7 v1 IQA sample (18 rows for 9 images) had no overlap with these prediction paths and was not mixed into this v2 analysis.
- No uncertainty, calibration, external validation, or new model training/inference was performed.
