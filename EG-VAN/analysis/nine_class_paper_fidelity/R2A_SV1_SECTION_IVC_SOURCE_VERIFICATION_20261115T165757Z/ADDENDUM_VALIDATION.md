# Addendum Validation

## Structural checks

Status: `PASS`.

- The five expected files are present and non-empty.
- `SOURCE_LOCATOR_DETAILS.csv` parses as two records, one per quoted count.
- Both rows agree on the source PDF, SHA-256, section, printed page, viewer page, zero-based index, page object, text-stream object, filter, and page-tree position.
- The addendum manifest contains exactly the four non-manifest deliverables, once each; hashes match.

## Source checks

Status: `PASS`.

- Original PDF SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3` (matches required value).
- Page object 475 references text stream object 509 with `FlateDecode`.
- The page tree maps page object 475 to viewer page 12 / zero-based index 11, and the stream footer gives printed page 72863.
- The decompressed text stream contains both quoted count statements and the Section IV-C heading.
- No claim is made that the entire PDF page was visually inspected.

## Preservation checks

Status: `PASS`.

- The original R2A directory contains its expected eight files. Its seven non-manifest files match `R2A_MANIFEST.sha256`, and the manifest file list is unchanged.
- The original R2A manifest still passes.
- R1/R2 and all existing R2A artifacts were read-only. The only intentional project-tree addition is this new addendum directory.
- No Git command or Git metadata operation was performed. No existing project working-tree file was edited, renamed, moved, or deleted.
- No dataset, patient image, model weight, review queue, training, or evaluation was accessed or performed.

## Audit status retained

- `SECTION_IVC_SOURCE_STATUS = VERIFIED`
- `TABLE2_SECTION_IVC_RECONCILIATION = UNRESOLVED`
- `OVERALL_R2A_STATUS = PARTIALLY_VERIFIED`
