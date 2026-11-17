# R2A Unresolved Questions

## Numerical interpretation

1. What does the Table 2 NV `Augmented Images` literal `00` mean? It is retained exactly as printed. A total of 34,554 is only the conditional sum if `00` is numeric zero; the literal-string total is not numeric.
2. Are Table 2's `Train images` counts pre-augmentation counts, post-augmentation counts, or another stage? The paper does not define this.
3. Do Table 2's `Augmented Images` counts represent additional generated images, final per-class training counts, or a different augmentation accounting measure? The table provides no definition or footnote.
4. How do Table 2's per-class training and augmentation values relate to Section IV-C's later totals of 37,883 training and 6,686 validation images? No mapping is supplied.
5. Does Section IV-C's validation total contain augmented images, and if so, what process assigned them? The passage says the validation total includes original and augmentation images but does not state the allocation method or identify Table 2 cells used.
6. Are the Table 2 binary-source counts and the Section IV-C totals drawn from exactly the same nine-class cohort and filtering stage? This is not established by the inspected passages.

## Required evidence to resolve

- An author- or source-maintainer-provided definition of every Table 2 count column and the NV `00` literal.
- A class-by-class, stage-by-stage count ledger distinguishing original, generated/augmented, training, validation, and testing records.
- The split and augmentation procedure, including when augmentation occurred relative to the train/validation split and whether any image could enter more than one partition.
- A source cohort manifest with stable record identifiers and the filtering/merging rules connecting Table 2 to Section IV-C.

THE PAPER DOES NOT PROVIDE A SUFFICIENT EXPLANATION IN THE INSPECTED SECTIONS.

These are source-definition and provenance gaps. Arithmetic alone cannot resolve them, and no inferred reconciliation is offered.
