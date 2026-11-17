# R2B Unresolved Evidence

## Unresolved numerical relationship

If and only if Table 2's NV augmented literal `00` is treated as numeric zero, and if the separate `Train images` and `Augmented Images` cells are added, the Table 2 arithmetic is:

- Original: 13,312
- Testing: 1,332
- Train: 11,980
- Augmented: 34,554 (conditional)
- Train + Augmented: 46,534 (conditional)

Section IV-C reports 37,883 training and 6,686 validation images, totaling 44,569. Conditional `46,534 - 44,569 = 1,965`. This is a numerical difference between derived/reported quantities, not proof that the paper's method is inconsistent: the paper does not define the relevant Table 2 stages or state that the totals are comparable.

## Missing definitions and evidence

1. **Table 2 count semantics:** The paper does not define whether `Augmented Images` means newly generated items, a final class target, a count including originals, or another measure. Required evidence: an author/source definition for each Table 2 column.
2. **NV `00`:** It is printed literally as `00`, with no clarifying note located. Required evidence: author/source clarification of whether this is zero, a formatting error, or another value. No numeric interpretation is adopted here.
3. **Stage bridge:** Section IV-C describes augmentation and then a train/validation division, but there is no per-class table relating Table 2 to its 37,883/6,686 totals. Required evidence: a count ledger at each processing stage, by source and class.
4. **Cohort identity:** Section IV-A describes a combined nine-class dataset; Section IV-C says it first divided “the HAM-10000 dataset” while then referring to all nine classes. The text does not clarify whether the term denotes the combined cohort. Required evidence: source/versioned cohort manifest with stable image IDs.
5. **Partition and augmentation allocation:** The text does not give membership, seed, patient/lesion grouping, duplicate/overlap control, or a method for allocating augmented descendants between training and validation. Required evidence: partition manifests, augmentation lineage, and grouping policy.
6. **Filtering/removal:** Hair removal is an image preprocessing method, but no record-level filtering, exclusion, or removal count is stated in the relevant passages. A train/validation partition alone cannot change a combined total. Required evidence: a documented record-level exclusion or filter operation and its counts, if one occurred.
7. **Augmentation method count:** Section G says 13 techniques on the nine-class dataset; printed p. 72872 says 20 alternative methods. The paper does not explain whether these refer to different stages or subsets. This does not account for the 1,965 image-count difference. Required evidence: a method inventory and clarification of where each technique was used.

## Directly supported conclusions

- All nine Table 2 rows satisfy `Original = Testing + Train`.
- Table 2 testing totals 1,332, matching Section IV-C's stated count of 1,332 original testing images. Numeric equality does not prove sample-level identity.
- The source supports the Section IV-C training and validation values. It does not provide a sufficient explanation of how those totals relate to Table 2's augmentation values.
- Under conditional zero arithmetic, the NV cell does not remove the 1,965 gap; it makes the augmented sum calculable only under that assumption.

THE PAPER DOES NOT PROVIDE A SUFFICIENT EXPLANATION IN THE INSPECTED SECTIONS.

No reconciliation, filtering step, split ratio, or image-level partition was invented. The paper's own count relationship remains unresolved.
