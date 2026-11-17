# R2F Cross-Audit Consistency Report

## Validation basis

The R1-R2E package manifests were verified before synthesis. Their recorded substantive file sets and hash manifests passed. The original paper SHA-256 matched `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`. This report distinguishes direct evidence, extraction, project artifacts and conditional arithmetic.

## Required cross-audit checks

1. **Table 2 source transcription versus numerical reconciliation — CONSISTENT.** R2 preserves the visible NV augmented cell as literal `00`. R2A/R2B/R2D retain the same literal and present 34,554 and 46,534 only conditionally on treating it as zero and adding columns. No later report silently normalizes the source entry.
2. **Table 2 versus Section IV-C — UNRESOLVED, consistently.** Table 2 reports 11,980 train and 1,332 testing; Section IV-C reports 37,883 training, 6,686 validation and 1,332 original testing. The testing count matches numerically, not demonstrably by image identity. The Table 2 augmented definition, cohort/stage bridge and class ledger are absent. Conditional difference remains 1,965.
3. **R2C versus R2D on 13/20 references — QUALIFIED, NOT CONTRADICTORY.** R2C marks the two quotations verified from PDF text streams and classifies their relationship `POSSIBLY_RELATED`. R2D changes the 13-reference status from `VERIFIED` to `PARTIALLY_VERIFIED` specifically for the additional visual-legibility criterion; the words remain text-stream supported. R2D visually supports the conclusion's 20 reference. Relationship remains `POSSIBLY_RELATED`.
4. **R2D visual limits versus extracted text — CONSISTENT.** The exact Section G sentence was not legible enough for independent visual transcription, and every R2F citation preserves its text-stream-only qualification. The conclusion's 20-method sentence and Table 2 `00` have visual evidence. The R2D page inspection is not misrepresented as full-page transcription.
5. **R2E equation versus symbol/transformation inventories — CONSISTENT.** The recovered equation is `f(x_i) = sum(j=1 to 20) T_j(x_i)`. The symbol inventory reports seven verified symbol/index roles and leaves N partial; the transformation inventory identifies zero individual operations. R2F preserves all three statements and does not confuse role/index verification with operation identification.
6. **Project implementation claims versus R1 provenance/leakage — QUALIFIED.** Prior context reports an implemented nine-class architecture/training pipeline, while R1 records an unverified local binary source and no approved final cohort/split with unresolved IDs/overlap. R2F treats architecture/pipeline existence as an unverified project claim, not evidence that the data are eligible or that the implementation is paper-faithful.
7. **Later status upgrades — NONE WITHOUT EVIDENCE.** Table 2's printed values are `VERIFIED` because R2 added visual source verification; this does not upgrade the current project cohort. R2E verifies the equation transcription using PDF operators/font maps and a text/math crop but does not upgrade operational reproducibility. No R1-R2E package resolves rights, cohort identity, group separation, augmentation identities, Table 2 semantics, or the 1,965 difference.

## Cross-audit cautions

- `R2C OVERALL_R2C_STATUS = PARTIALLY_VERIFIED` is retained; R2D did not replace that overall assessment.
- The Section G count's status is evidence-mode dependent: text-stream verified, visually limited. R2F uses `PARTIALLY_VERIFIED` in the consolidated matrix to preserve that limitation.
- A paper-reported performance figure is not project-measured performance. No R1-R2E audit establishes a reproduction of 96.68% F1 or 98.20% accuracy.
- Count arithmetic, equality, or repeated mention across reports is not independent evidence of image membership, stage equivalence, source provenance, or leakage safety.

## Conclusion

No material contradiction among R1-R2E was identified in the required checks. Status distinctions and unresolved issues are carried forward rather than silently reconciled. The current evidence does not justify a positive paper-fidelity, dataset-readiness, or implementation-readiness conclusion.
