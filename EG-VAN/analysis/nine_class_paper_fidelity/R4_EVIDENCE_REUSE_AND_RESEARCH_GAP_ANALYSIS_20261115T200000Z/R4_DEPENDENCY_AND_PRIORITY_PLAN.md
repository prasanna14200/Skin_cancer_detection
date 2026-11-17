# R4 Dependency and Priority Plan

## Highest-priority dependency chain
1. Resolve source provenance and rights for the nine-class cohort.
2. Resolve record-level patient/lesion identity and overlap review.
3. Establish a leakage-safe approved split and freeze the manifest hash.
4. Confirm the label mapping and class-order definitions before any further evaluation.
5. Resolve paper-fidelity gaps in augmentation, Table 2 logic and Section IV-C count reconciliation.
6. Re-run the existing model and evaluation pipeline only on the approved cohort.
7. Re-run IQA, uncertainty and external-validation flows only after the approved split is fixed.

## Priority ordering
- Priority A: cohort approval and split integrity
- Priority B: paper-fidelity and methodology closure
- Priority C: model validation and result logging
- Priority D: uncertainty calibration and IQA-to-error analysis
- Priority E: legitimate external validation

## Implementation constraints
- No new training or evaluation should be started before the approved cohort and split are in place.
- The exploratory split must remain isolated from research claims.
- Any experimental assumption must be documented as a deviation from the paper rather than as faithful reproduction.

## Recommended next action
Complete the missing source-rights and overlap-adjudication work before any attempted nine-class training run on a newly approved dataset. The current infrastructure is prepared to continue once the data-level blockers are removed.
