# R2F Evidence and Source Index

## Scope and evidence rules

R2F consolidates the R1, R2, R2A, R2A-SV1, R2B, R2C, R2D and R2E audit packages. It is not a new paper inspection, implementation review, dataset approval, or reproduction. Prior package manifests were checked before this synthesis; the original PDF SHA-256 is `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`.

Evidence labels are kept distinct:

- **Direct PDF / visual**: source-page/table view, including R2's visual Table 2 transcription and R2D's specified page views.
- **Extracted text**: PDF text stream/operator evidence, not automatically a visual transcription.
- **Project artifact**: findings recorded from local project manifests, gates or code by R1; not newly inspected in R2F.
- **Inference**: arithmetic, comparison, or a conclusion from stated evidence. Conditional calculations are labeled conditional.

`VERIFIED` applies only to the claim actually supported. A verified printed count is not verification of local cohort membership; a recovered equation is not a reproducible algorithm. R2F does not treat repeated audit prose as independent evidence.

## Source identity

- Original paper: `EG-VAN_A_Global_and_Local_Attention-Based_Dual-Branch_Ensemble_Network_With_Advanced_Color_Balancing_for_Multi-Class_Skin_Cancer_Recognition.pdf`
- Expected and rechecked SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`
- R1-R2E evidence refers to the same paper PDF hash, as recorded in their validation/source identity sections.

## Audit package index

All paths below are relative to `analysis/nine_class_paper_fidelity/`.

| Package | Primary evidence used in R2F |
|---|---|
| `R1_AUDIT_20261115T142000Z` | `R1_FINDINGS.md`, `NINE_CLASS_MAPPING_EVIDENCE.csv`; dataset-source mapping, unverified local binary source, missing IDs, rights/split/overlap limitations and project gate status. |
| `R2_SOURCE_VERIFICATION_20261115T163331Z` | `TABLE2_SOURCE_TRANSCRIPTION.csv`, `TABLE2_COMPARISON.csv`; visually verified Table 2 rows and literal NV `00`. |
| `R2A_NUMERICAL_RECONCILIATION_20261115T164756Z` | `R2A_RECONCILIATION.csv` and findings; separates arithmetic equality from cohort/stage comparability. |
| `R2A_SV1_SECTION_IVC_SOURCE_VERIFICATION_20261115T165757Z` | `SECTION_IVC_VERIFICATION_ADDENDUM.md`; Section IV-C source wording/counts. |
| `R2B_RECONCILIATION_INVESTIGATION_20261115T171203Z` | `R2B_FINDINGS.md`, `R2B_HYPOTHESIS_MATRIX.csv`, `R2B_RECONCILIATION_CALCULATIONS.csv`, `R2B_UNRESOLVED_EVIDENCE.md`; processing sequence and unresolved count bridge. |
| `R2C_AUGMENTATION_METHODOLOGY_20261115T174848Z` | `R2C_FINDINGS.md`, `R2C_SOURCE_EVIDENCE_INVENTORY.md`, `R2C_13_VS_20_COMPARISON.md`, `R2C_AUGMENTED_COUNT_DEFINITION.md`. |
| `R2D_VISUAL_SOURCE_VERIFICATION_20261115T183952Z` | `R2D_VISUAL_SOURCE_VERIFICATION.md`, `R2D_VISUAL_EVIDENCE_INVENTORY.csv`, `R2D_STATUS_CHANGE_MATRIX.csv`, `R2D_TABLE2_AUGMENTED_COUNT_REVIEW.md`; visual qualification and status changes. |
| `R2E_AUGMENTATION_FORMULA_RECOVERY_20261115T190646Z` | `R2E_EQUATION_TRANSCRIPTION.md`, `R2E_SYMBOL_DEFINITION_INVENTORY.csv`, `R2E_TRANSFORMATION_IDENTIFICATION.csv`, `R2E_AUGMENTATION_SPECIFICATION_GAPS.md`, `R2E_RELATIONSHIP_CHECK.md`. |

R2F's complete domain-by-domain ledger and project status qualifications are in `R2F_MASTER_FIDELITY_MATRIX.csv`. Proposed decisions are in `R2F_IMPLEMENTATION_DECISION_REGISTER.csv`.

## Key source locators

| Claim | Locator and evidence |
|---|---|
| Seven HAM diagnoses plus a second binary source form a nine-class dataset | IV-A, printed p.72862; R2B source inventory records page object 719 and extracted text. Exact version/record lineage remains open. |
| Table 2 class counts and `NV / Augmented Images / 00` | Printed p.72863, viewer 12, page object 475, vector Form XObject 510; visually transcribed in `R2_SOURCE_VERIFICATION_20261115T163331Z/TABLE2_SOURCE_TRANSCRIPTION.csv`. |
| Section IV-C split narrative and totals | Printed p.72863, viewer 12, page object 475, content stream 509; wording verified in the R2A-SV1 addendum. |
| Generic augmentation definition and Eq. (15) | Section B, printed p.72857, viewer 6, index 5, page object 47, stream 122. Exact recovered equation: `f(x_i) = sum(j=1 to 20) T_j(x_i)`. |
| 13 techniques | Section G, printed p.72869, viewer 18, page object 181, stream 182. Text-stream wording is available; R2D could not independently visually transcribe the sentence at the available scale. |
| 20 alternative methods | Section VI, printed p.72872, viewer 21, page object 469, stream 534; text stream and conclusion crop support the sentence. |
| Model components named in conclusion | Section VI, printed p.72872, page object 469, stream 534. This is only a high-level claim; method-section component details were not audited in R1-R2E. |

## Count interpretation safeguards

The printed NV augmented value remains the literal `00`. Table 2 augmented sum `34,554`, Table 2 `Train + Augmented = 46,534`, and the `1,965` difference from `44,569` are conditional on treating `00` as zero and adding the two Table 2 columns. Section IV-C reports `37,883 + 6,686 = 44,569`. The paper does not establish that the Table 2 and Section IV-C totals refer to the same cohort, stage, or counting convention.

## Project evidence boundary

Project-status statements in R2F are inherited from R1's project-artifact audit and are explicitly labeled as such. R2F did not inspect patient images, masks, weights, predictions, source code, or data files. The prior project context's assertion that an architecture/training pipeline exists is not evidence of paper fidelity, dataset approval, split eligibility, or measured results.
