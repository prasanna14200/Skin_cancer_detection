# R2A Findings

## Final status

`PARTIALLY_VERIFIED`

The Table 2 values are available in the R2 primary-source visual transcription and the count statements in Section IV-C were extracted from the original PDF text content stream. Independent arithmetic checks are consistent, but the paper does not explain how Table 2's counts reconcile with Section IV-C's training and validation totals.

## Verified facts

- Original paper: *EG-VAN: A Global and Local Attention-Based Dual-Branch Ensemble Network With Advanced Color Balancing for Multi-Class Skin Cancer Recognition*, Adnan Saeed, Khurram Shehzad, Saim Ahmed, and Ahmad Taher Azar; IEEE Access 13 (2025), pp. 72852-72874; DOI `10.1109/ACCESS.2025.3561240`.
- The original PDF is 23 pages. Table 2 and Section IV-C are on printed p. 72863, viewer page 12, zero-based index 11.
- Table 2 row sums: 13,312 original, 1,332 testing, and 11,980 train images.
- Each of the nine Table 2 classes satisfies `Original Images = Testing Images + Train images`.
- Section IV-C reports 1,332 original testing images, 37,883 training images including original and augmentation images, and 6,686 validation images including original and augmentation images. Training plus validation is 44,569.
- The paper prints NV augmented images as literal `00`. The existing project transcription stores `0`; R2 previously recorded this cell mismatch. R2A has not normalized that literal.

## Arithmetic results

- Augmented values excluding literal `00` sum to 34,554. Treating `00` conditionally as numeric zero gives the same total, 34,554; without such an interpretation, the augmented total is not numerically defined.
- Per-class `Train images + Augmented Images` arithmetic, conditional on `00` meaning zero, sums to 46,534. This is not evidence that the final training set contained 46,534 unique images.
- Section IV-C training plus validation is 44,569, which is 1,965 below the conditional Table 2 `Train + Augmented` arithmetic. The paper does not establish that these quantities are comparable.
- Section IV-C training is 25,903 above the Table 2 `Train images` sum and 8,651 below the conditional Table 2 `Train + Augmented` sum. The paper does not define the stage relationship needed to interpret these differences.
- Table 2 testing total 1,332 matches Section IV-C's 1,332 original testing images. Table 2 testing 1,332 and Section IV-C validation 6,686 are different named partitions and are not interchangeable.

## Unresolved issues

The meaning of the `00` literal and the relationship among Table 2 original/train/augmented counts and Section IV-C training/validation counts remain unresolved. The paper does not identify whether augmentation totals are additional unique images, how they were allocated across partitions, or whether the reported totals use identical cohorts and filtering stages.

## Reproducibility impact

The count arithmetic is reproducible from the printed Table 2 cells, but the training/validation accounting is not reproducible from the inspected paper statements alone. No numerical difference is silently attributed to augmentation, filtering, or cohort merging.

## This audit does not establish

This audit does not establish dataset provenance, image-level split membership, duplicate or patient-level separation, clinical validity, model performance, cohort approval, training authorization, or exact reproduction of the paper. No dataset or image was inspected; no training, evaluation, or inference was performed.
