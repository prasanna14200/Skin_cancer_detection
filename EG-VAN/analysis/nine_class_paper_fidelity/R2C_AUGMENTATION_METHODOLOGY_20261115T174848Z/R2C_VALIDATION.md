# R2C Validation

## Source and preservation checks

- Original PDF SHA-256 before source inspection: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`.
- R1, R2, R2A, R2A-SV1, and R2B manifests and exact file sets passed before R2C output creation.
- The source passages were extracted from PDF content streams and mapped through the page tree. The 13- and 20-reference pages were not visually rendered or inspected; no visual verification is claimed.
- No patient images, masks, datasets, model weights, predictions, training, inference, evaluation, or Git commands were used.
- Existing audit packages were not modified.

## Deliverable validation

- Expected deliverables: eight named R2C files, including this validation record and the manifest.
- Both CSV files are independently parsed as quoted CSV; every row has the header's field count.
- The augmentation-method inventory has a source locator in every row.
- The hypothesis update contains each H1-H7 exactly once, with an allowed evidence status and no status change from R2B.
- Both 13- and 20-method quotations, their locators, the `POSSIBLY_RELATED` classification, and the nonvisual extraction limitation are recorded.
- The Table 2 NV value remains the literal `00`; the conditional augmentation total remains expressly conditional.
- Arithmetic recheck: `37,883 + 6,686 = 44,569`; `11,980 + 34,554 = 46,534` only if NV `00` is interpreted as zero; `46,534 - 44,569 = 1,965` under that same condition.
- The original PDF SHA-256 was rechecked after report creation and still matches the expected value.
- R1, R2, R2A, R2A-SV1, and R2B manifests and exact file sets were rechecked after report creation and still pass.
- The R2C manifest contains exactly the seven non-manifest deliverables and their matching SHA-256 values.
- R2C directory contains exactly the eight requested files, all nonempty.

No Git cleanliness claim is made. No Git command was run.
