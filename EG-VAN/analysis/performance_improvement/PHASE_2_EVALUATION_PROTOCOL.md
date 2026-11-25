# Phase 2 — Evaluation Protocol

**Status: EXPLORATORY / NON-CLINICAL / NOT APPROVED**

## Dataset and split audit

The existing `exploratory_split.csv` contains 10,234 source-labeled rows with
an explicit train/validation/calibration/test partition. The frozen split is
preserved and may not be overwritten.

Observed partition counts:

| Partition | Rows |
|---|---:|
| Train | 7,080 |
| Validation | 1,028 |
| Calibration | 1,023 |
| Test | 1,103 |

All nine source-defined classes are present in the train, validation,
calibration and test partitions.

## Trustworthiness assessment

The existing split has no known crossing of recorded `overlap_group` values
between partitions. However:

- only 79 patient identifiers are recorded;
- Fanconic patient/lesion identities and rights are incomplete;
- some photographic duplicate relationships remain unresolved;
- no independent approval is recorded;
- the approval checklist status is `NOT_APPROVED`.

Therefore the existing partition is unsuitable for a claim of
leakage-safe or independent protected-test performance.

## Protocol for this sprint

This sprint will distinguish:

1. **Development baseline:** existing training partition only.
2. **Model-selection validation:** existing validation partition only.
3. **Independent test:** existing test partition only after model selection,
   if an untouched and valid test is considered possible.

The test partition is locked and cannot be used for checkpoint selection,
class weighting, loss selection or hyperparameter tuning.

For a resource-bounded experiment, the following remain prohibited:

- tuning against the test partition;
- relabeling calibration/test records;
- removing classes;
- merging source labels;
- changing source labels or class definitions;
- replacing missing patient IDs with invented values.

## Minimum threshold for training

No full training will begin until the run is separately resource-bounded:

- no default-global package modification;
- CPU-only or a verified compatible GPU;
- one tiny smoke batch and memory measurement;
- checkpoint loading strictness verified;
- class weights calculated only from training rows;
- frozen seed and exact configuration.

## Result interpretation

Any result in this sprint is exploratory/non-clinical validation evidence.
Validation accuracy is not test accuracy. Test metrics can only be reported
after checkpoint freeze and one-time test evaluation.
