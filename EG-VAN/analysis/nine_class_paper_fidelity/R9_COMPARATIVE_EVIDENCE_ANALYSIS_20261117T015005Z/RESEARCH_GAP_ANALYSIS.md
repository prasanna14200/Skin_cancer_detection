# Research gap analysis

**Current state: exploratory evidence exists; defensible research validation remains blocked.**

## Implemented and evidenced

- Core EG-VAN-style dual-branch architecture, attention/fusion blocks, nine-class head, Stage 6 training gate, exploratory runner, best/last checkpoints, and a saved 1,028-row validation result exist. Synthetic architecture tests are not image-performance evidence.
- The checkpoint is linked to the validation metrics by SHA-256; source image and prediction linkage is recorded in the later IQA and uncertainty packages.
- A later real-model IQA association package and uncertainty/calibration package reuse saved probabilities and labels; they perform no new inference.
- External manifest/overlap/evaluation software exists, but R8 is feasibility/candidate-screen evidence, not external evaluation.

## Unresolved research gaps

1. **Cohort approval and independence:** all exploratory rows remain `NOT_APPROVED`; no production approval or protected nine-class test is established. The split's reported `known_group_crossings=0` does not prove photographic or patient independence because identities are missing and source semantics are not equivalent.
2. **Duplicate/source-test boundaries:** R6 records 9 `SAME_PHOTO`, 10 `DISTINCT`, 2 `UNCERTAIN`, 428 unreviewed queue pairs, and 471 remaining source-test conflicts. The 2 uncertain plus 428 unreviewed relationships remain unresolved. R7 is a second-review batch template, not adjudicated evidence.
3. **Class performance:** the current validation predicts NV for 1,012/1,028 rows. Accuracy 0.610895 masks macro-F1 0.097532 and balanced accuracy 0.118353; six classes have zero recall.
4. **IQA inference:** 9/14 overall features pass q<0.05 after the saved global correction, but overall differences are unadjusted for class/source confounding. Only BCC and NV permit within-class tests, with tiny groups for key errors (NV has five errors; BCC has three correct).
5. **Calibration/generalization:** probabilities show exploratory error-ranking ability and split-specific reliability, but there is no approved independent calibration set, no saved calibration predictions, no temperature fit, and no prospective or external threshold validation.
6. **External cohort:** PH2 has only candidate two-class mapping and unresolved identity/source version limits; the bounded SIIM pilot has only 18 detailed-diagnosis candidates across NV/BKL and 82 unknown labels; local ISIC-2017 images are unavailable by metadata ID. None can support full nine-class external validation.
7. **Paper fidelity:** R2F/R3 identify unresolved source versions, label construction, exact split/augmentation ledger, model details, and reported-count bridges. Random initialization and other implementation choices differ from or cannot be verified against the paper. The 98.20% accuracy and 96.68% F1 are paper claims only.
8. **Training provenance:** the saved run config states 25 planned epochs, but the history file in a different run folder is not linked to the validation checkpoint. No epoch-level curve is attributed to the checkpoint in this synthesis.

## Minimum future evidence

- Versioned and rights-cleared original image set with image/patient/lesion identifiers and a defensible nine-label policy.
- Human-reviewed photo/group resolution and independent reconciliation of the 471 source-test conflicts.
- Signed/recorded approval, frozen group-disjoint partitions including a separately approved calibration set, and hash-bound provenance.
- Author/source-maintainer resolution of paper ambiguities before any exact-reproduction claim.
- New gated evaluation and genuinely independent external cohort after the above blockers close.

No action in this analysis changes a gate or makes a cohort/split approval.
