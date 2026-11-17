# Nine-Class Mapping Reassessment

## Status by claim

| Claim | Status | Evidence-based result |
|---|---|---|
| Seven HAM10000 diagnostic outputs | `VERIFIED` | Paper Section IV-A, printed p. 72862, describes seven HAM10000 diagnoses; Table 2 names the seven rows and their codes on printed p. 72863. |
| Separate `BENIGN` output | `VERIFIED` as a printed output; `PARTIALLY_VERIFIED` as a source-defined target | Table 2 has a `Benign` row with source `ISIC 2017`; Section IV-A describes a two-class benign/malignant collection. Exact source version and label derivation are not established. |
| Separate `MALIGNANT` output | `VERIFIED` as a printed output; `PARTIALLY_VERIFIED` as a source-defined target | Table 2 has a `Malignant` row with source `ISIC 2017`; Section IV-A describes a two-class benign/malignant collection. Exact source version and label derivation are not established. |
| Exact origin of the final two outputs | `PARTIALLY_VERIFIED` | The table's literal source label is `ISIC 2017`, but the complete official Task 3 release does not match the table's 3,297 images and generic two-class schema. The actual source package, derivative, version, and image list are unknown. |
| Exact meaning of the final two outputs | `PARTIALLY_VERIFIED` | The paper names the outputs benign and malignant but does not document the per-image label derivation or a mapping from official ISIC Task 3 targets. |
| All nine outputs are semantically comparable, mutually exclusive diagnoses | `UNVERIFIED` | The paper combines seven diagnosis-specific labels with two broad labels but does not define an exclusivity or cross-source reconciliation rule. No medical equivalence is inferred. |
| Project cohort/source provenance is approved | `NOT_APPLICABLE` | R2 is source verification only; it does not approve data, a cohort, a split, or training. |

## Interpretation

The paper directly supports nine separate output rows and the seven HAM10000 diagnostic names. It also directly supports two additional rows named Malignant and Benign and labels their dataset source `ISIC 2017`. The official ISIC Task 3 documentation does not support treating those rows as the complete official 2017 Task 3 dataset or as its two task-specific binary targets.

The table therefore verifies the printed label/source claim, not the underlying provenance or scientific meaning of the binary labels. Seven specific diagnostic categories and two broader source labels are not demonstrated to be mutually exclusive clinical concepts. A classifier can have nine one-hot output categories while the underlying clinical semantics overlap.

The existing project's `FANCONIC_LOCAL_UNVERIFIED_VERSION` marker and local folder-label mapping are not validated by Table 2. No cohort or dataset approval follows from this reassessment.
