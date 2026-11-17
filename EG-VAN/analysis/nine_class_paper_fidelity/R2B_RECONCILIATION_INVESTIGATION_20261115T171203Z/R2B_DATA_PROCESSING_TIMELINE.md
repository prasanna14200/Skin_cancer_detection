# R2B Data-Processing Timeline

This timeline separates the paper's stated sequence from arithmetic derived from the reported counts. It does not infer a missing operation or establish that two counts refer to the same cohort.

| Order as stated or located | Paper evidence | What it establishes | What remains undefined |
|---|---|---|---|
| Dataset composition | Section IV-A, printed p. 72862: seven HAM10000 diagnoses are described; a second two-class skin-cancer source is described as malignant/benign with over 3,200 images. The paper says their combination created a nine-class dataset and points to Table 2 for class counts. | High-level nine-class composition and a link to Table 2. | Versioned source identity, per-image lineage, exact initial cohort list, and whether Section IV-C uses the same combined cohort. |
| Image preprocessing | Printed p. 72856: the text refers to hair removal on HAM10000, followed by illumination/color preprocessing. | An image-level preprocessing step is described. | No number of records removed, excluded, or retained is reported in this passage. |
| General augmentation rationale | Printed p. 72857, subsection B: augmentation is defined as creating new data from existing data through random transformations; class imbalance in HAM10000 is cited as motivation. The mathematical discussion refers to 20 transformations. | Augmentation can create derived examples; imbalance motivated augmentation. | It does not define Table 2's `Augmented Images` cells, actual per-class output counts, or partition placement. |
| Original/testing/train counts | Table 2, printed p. 72863: nine rows list original, testing, train, and augmented counts. In every row, Original = Testing + Train. | The first three columns are arithmetically consistent as an original/test/train partition. Totals are 13,312 original, 1,332 testing, and 11,980 train. | Table 2 does not state when these values were measured or whether the augmented column is an increment, target total, or another measure. |
| Section IV-C split/augmentation sequence | Printed p. 72863: first divide “the HAM-10000 dataset” into training/testing; testing contains 1,332 original images; apply augmentation on the training dataset to improve all nine classes; “After that” further divide the training dataset into training/validation. | A textual sequence of test split, augmentation, then train/validation split; reported test/training/validation counts. | It does not map Table 2 columns to these stages, define the exact cohort, provide class-level train/validation counts, or state the augmentation allocation/unique-file policy. |
| Section G augmentation count | Printed p. 72869: 13 techniques on the nine-class dataset. | A separate statement of augmentation technique count. | No connection to Table 2's numeric augmentation cells or Section IV-C totals. |
| Later augmentation count | Printed p. 72872: 20 alternative augmentation methods. | A second reported technique count. | The paper does not reconcile 13 vs. 20 or identify which count applies to the reported data totals. |

## Independently derived arithmetic (not printed split percentages)

- Table 2 testing is 1,332 / 13,312 = approximately 10.006% of its original total; train is approximately 89.994%. No percentage is stated in the cited Table 2 cells.
- Section IV-C validation is 6,686 / 44,569 = approximately 15.001%; training is approximately 84.999%. These are ratios calculated from the reported totals, not a paper-stated split ratio.
- Conditional on interpreting the NV literal `00` as numeric zero, Table 2 `Train + Augmented` totals 46,534. Section IV-C training plus validation totals 44,569. Their arithmetic difference is 1,965.
- A partitioning step by itself does not change the sum of records being partitioned. The paper does not state that 1,965 records were filtered, removed, or excluded between these counts.

## Scope cautions

Section IV-C calls the initial cohort “the HAM-10000 dataset” while referring to a nine-class task after augmentation. Section IV-A says the nine-class dataset combines HAM10000 and a second source. The text does not clarify whether “HAM-10000” is shorthand for the combined cohort in Section IV-C. The matching testing totals (1,332) do not establish image identity or resolve that wording.

The text's sequence places augmentation before the later train/validation division. It does not describe the parent-child allocation of augmented examples. Therefore this audit neither claims nor rules out related examples appearing across partitions.

No explicit dataset-record filtering, duplicate removal, overlap check, or patient/lesion-group split rule was located in the inspected passages. The hair-removal passage concerns image content and does not report record exclusion.
