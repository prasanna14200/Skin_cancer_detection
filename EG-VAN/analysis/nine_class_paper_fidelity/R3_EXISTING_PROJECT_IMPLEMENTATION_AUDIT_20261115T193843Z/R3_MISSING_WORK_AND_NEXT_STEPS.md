# R3 Remaining Work and Recommended Next Step

This list preserves completed operational preparation and existing experiments. It does not recommend restarting them or running another model before resolving the dataset gates.

## Blocking validation work

1. **Close the source-record review queue.** Complete independent human adjudication for the 19 primary candidate pairs and resolve or explicitly exclude the 101 additional unresolved relations. Record reasons, reviewers, and versioned decisions; do not infer identity or equivalence from automated candidate scores.
2. **Establish record eligibility before creating a research split.** Resolve source/version and permitted-use evidence for every source; retain provenance and original labels; document patient/lesion identity limits and the SIIM quarantine/no-candidate decisions. The current 79 SIIM records are preliminary source-negative records, not an approved BENIGN cohort.
3. **Approve a leakage-safe research split.** Only after steps 1-2, produce and freeze an independently reviewed group-separated train/validation/calibration/test split. Do not promote the existing EXPLORATORY_ONLY split or its test partition.
4. **Clarify paper-fidelity decisions.** Obtain source/author clarification for Eq. (15)'s 20 undefined transformations, data selection/retention, unresolved count reconciliation, exact fusion/tap details, non-local configuration and training hyperparameters. If proceeding without clarification, document every choice as an experimental deviation, not reproduction.

## Existing implementation/evidence gaps after approval

- Attach an epoch-complete history, exact completed epoch, device model, software versions and initialization/checkpoint provenance to the existing training run. The current run records `CUDA`, not the specific GPU, and its lone `history.csv` is in another run folder.
- The saved nine-class validation result is real and checkpoint-hash-linked, but **exploratory only**: 0.61089494 accuracy and 0.09753237 macro-F1 on 1,028 validation records, with low balanced accuracy and near-collapse to the majority class. Do not tune against the test partition. Once a cohort is approved, diagnose training on training/validation data, then evaluate once on the frozen test partition.
- After approval, execute the already-implemented IQA-performance join and report quality-versus-error/confidence associations; the current IQA results are descriptive pixel proxies only.
- After approval, fit calibration only on a frozen independent calibration partition and produce the already-supported reliability, ECE, Brier, NLL and risk-coverage outputs. Do not use the unapproved exploratory calibration partition as evidence.
- The Stage 9 external workflow needs a genuinely independent, source-compatible, rights-cleared cohort with all required class support and overlap review. PH2's legacy two-label subset is not a nine-class external validation set.
- Reconcile older Stage 7 `nine_class_iqa_v1` results with current source `nine_class_iqa_v2` before presenting them as reproducible current-code outputs.
- Preserve the Stage 23 seven-class registry numbers as historical, unverified references unless the referenced checkpoint, metrics, predictions and evaluation inputs are recovered and integrity-checked.

## Single best next task

Complete the independent Stage 12 record-eligibility and overlap adjudication, including source rights/provenance and the SIIM quarantine decisions, without changing the existing data. This is the prerequisite to approving any research split or starting a defensible new training/validation cycle. It is a validation task, not a restart of dataset preparation.
