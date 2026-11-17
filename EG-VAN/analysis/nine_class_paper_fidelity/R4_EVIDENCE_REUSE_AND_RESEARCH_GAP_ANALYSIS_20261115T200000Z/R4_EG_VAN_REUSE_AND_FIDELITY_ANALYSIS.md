# R4 EG-VAN Reuse and Fidelity Analysis

## Scope
This review is a read-only reuse analysis of the existing project evidence. It does not re-run training or inference and it does not treat exploratory outputs as research-grade evidence.

## What is already reusable
The existing project contains concrete reusable artifacts for a controlled continuation after provenance and split approval become available:

- The nine-class EG-VAN architecture is implemented in the model source files under `EG-VAN/src/models/egvan`.
- The training gate, data loader and checkpoint logic are present in the Stage 6 and exploratory training stack.
- The real exploratory validation evidence exists in `analysis/nine_class_validation_diagnostics/.../validation_metrics.json` and is linked to the saved checkpoint provenance.
- The read-only project audit packages `R2F` and `R3` establish the formal status boundaries and the current blockers.
- The IQA and uncertainty experimental infrastructures exist and can be re-used only after they are rerun on an approved, leakage-safe cohort.

## What is not reusable as paper-grade evidence
The following items must not be promoted from exploratory or descriptive work into research-grade evidence:

- The exploratory split remains `EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION`.
- The model’s real validation result is weak and majority-class dominated.
- The IQA outputs are descriptive only and do not establish a valid classification-quality relationship.
- The uncertainty outputs are synthetic-only and not derived from a real held-out model.
- The external-validation pipeline is implemented but has no approved nine-class external cohort.
- The paper-level fidelity resolution remains blocked by source provenance, augmentation ambiguity and Table 2/Section IV-C count gaps.

## Where implementation fidelity is acceptable for local engineering reuse
The codebase demonstrates a substantial engineering implementation of the EG-VAN design: EfficientNetV2-S, modified ResNet50, SCGA, non-local attention and multi-scale feature fusion are all present. This is a sound basis for continuing to handle code and training maintenance, provided the implementation is consistently labeled as local engineering and not paper reproduction.

## Where fidelity is not paper-validated
The current repository architecture is not evidence-equivalent to the paper’s exact design because:

- paper augmentation is unresolved and not represented as a specified transformation set,
- the actual Table 2 and Section IV-C ledger remain unresolved,
- the data provenance and label derivation remain unresolved,
- no approved nine-class split and no approved source cohort exists,
- questions remain around patient/lesion-level separation and image overlap.

## Reuse decision
The strongest evidence-backed reuse path is to preserve the current implementation as a local engineering backbone while postponing any paper-equivalent claim and keeping exploratory outcomes isolated from clinical or paper claims.

`PAPER_FIDELITY_STATUS = INCOMPLETE_UNRESOLVED`

`DATASET_READINESS_STATUS = OPERATIONAL_PREPARATION_COMPLETE__RESEARCH_COHORT_NOT_APPROVED`

`IMPLEMENTATION_READINESS_STATUS = BLOCKED`
