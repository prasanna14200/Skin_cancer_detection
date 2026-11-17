# R2B Findings: Table 2 / Section IV-C Investigation

## Final status

`TABLE2_SOURCE_STATUS = VERIFIED`

`SECTION_IVC_SOURCE_STATUS = VERIFIED`

`TABLE2_SECTION_IVC_RECONCILIATION = UNRESOLVED`

`NV_AUGMENTED_ENTRY_STATUS = AMBIGUOUS`

`OVERALL_R2B_STATUS = UNRESOLVED`

## Executive summary

The original paper directly supports Table 2's visible counts (as previously isolated and visually verified in R2) and Section IV-C's 1,332 original testing, 37,883 training, and 6,686 validation statements. The paper describes augmentation before a further training/validation division. It does **not** define Table 2's `Augmented Images` column, say whether `00` is numeric zero, or provide a class/stage ledger relating Table 2 to Section IV-C.

With the explicit conditional assumption that NV `00` means numeric zero and Table 2 `Train images` and `Augmented Images` are additive, `Train + Augmented = 46,534`; Section IV-C training plus validation is 44,569; the difference is 1,965. The paper does not document a 1,965-record removal or any other operation that reconciles these figures. Because shared cohort and stage equivalence are unproven, this arithmetic alone does not establish an error.

## Verified facts and calculations

- Table 2 totals: 13,312 original; 1,332 testing; 11,980 train. Every class satisfies `Original = Testing + Train`.
- Table 2's nine augmentation cells preserve NV as literal `00`. Their sum is not numerically defined as printed. The sum is 34,554 only if `00` is assumed to be zero; conditional `Train + Augmented` is 46,534.
- Section IV-C reports 1,332 original testing images, 37,883 training images consisting of originals and augmentation images, and 6,686 validation images also consisting of originals and augmentation images; combined train plus validation is 44,569.
- Section IV-C's narrative order is: initial train/test division, augmentation on the training dataset, then further division into training and validation. The paper does not explicitly map these stages to Table 2.
- Section IV-A describes a nine-class dataset as a combination of HAM10000 and a two-class source. Section IV-C uses “HAM-10000 dataset” while describing a nine-class training set; whether this is shorthand for the combined cohort is not stated.
- The paper describes 13 augmentation techniques on printed p. 72869 and 20 alternative methods on printed p. 72872. No relation between those method counts and Table 2 counts is provided.
- Hair removal is described as image preprocessing on printed p. 72856; no record-removal count is stated. No dataset-level filtering/exclusion or duplicate/overlap operation explaining 1,965 was located in the inspected/searchable text.

## Hypothesis outcome

- H1 (augmentation cells are additional images): `PARTIALLY_SUPPORTED`; the definition and separate columns support, but do not define, that reading.
- H2 (augmentation cells include original training images): `NOT_SUPPORTED`; no direct evidence supports it, although the missing definition prevents definitive exclusion.
- H3 (Section IV-C is a later stage): `PARTIALLY_SUPPORTED`; later operations are narrated, but their relationship to Table 2 is not specified.
- H4 (split/filter explains the difference): `NOT_SUPPORTED`; a split alone preserves the combined total, and no count-changing filter is documented.
- H5 (paper arithmetic/reporting inconsistency): `UNRESOLVED`; the conditional difference exists but comparability is unproven.
- H6 (NV `00` changes reconciliation): `UNRESOLVED`; the literal's intended meaning is not specified.
- H7 (evidence is insufficient to distinguish explanations): `VERIFIED`.

The complete evidence, missing information, and statuses are in `R2B_HYPOTHESIS_MATRIX.csv` and `R2B_UNRESOLVED_EVIDENCE.md`.

## Project-document comparison

Earlier audit findings are consistent with these limits: R1 reports that per-image lineage and split/overlap membership are not established; R2 records the literal `00`; R2A and R2A-SV1 leave the count relationship unresolved. These are historical audit conclusions, not evidence that the local project reproduces the paper. No local dataset or project source was inspected for this R2B task.

## What this investigation does not establish

It does not establish the meaning of `00`, the final number of unique training images, a paper arithmetic error, dataset provenance, image-level split membership, duplicate/patient-level separation, model performance, clinical validity, training authorization, or exact reproduction. No dataset, patient image, mask, model weight, prediction, code, notebook, or Git state was accessed or changed. No training, evaluation, inference, or external research was performed.
