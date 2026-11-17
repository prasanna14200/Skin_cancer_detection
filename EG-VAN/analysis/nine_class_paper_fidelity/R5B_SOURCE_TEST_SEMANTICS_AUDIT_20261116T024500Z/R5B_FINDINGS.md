# R5B Source-Test Conflict Semantics Audit

## Summary
The original source file `analysis/nine_class_overlap_review/source_test_boundary_conflicts.csv` is a group-level conflict ledger, not a row-unique image ledger. The `duplicate_group` field is therefore a grouping ID, and multiple rows can share the same group when a single underlying group has multiple conflict types across split boundaries.

## Why the repeated group exists
The group `DG-f8e32066a54f843c` appears twice:

1. `binary_test_HAM` with `binary_paths = data/isic/data/test/benign/335.jpg` and `ham_paths = data/raw/HAM10000_images_part_1/ISIC_0027698.jpg;data/raw/HAM10000_images_part_2/ISIC_0029666.jpg`
2. `binary_train_test` with `binary_paths = data/isic/data/test/benign/335.jpg;data/isic/data/train/benign/1593.jpg` and the same HAM paths

This is not an accidental duplicate row. It is the same underlying group observed in two conflict contexts: a single test-image conflict and a train/test boundary conflict that includes both the test and train binary image paths. The shared group ID is therefore a grouping label, not a unique row key.

## Is `duplicate_group` a group ID or unique row ID?
`duplicate_group` is a group ID. Evidence: 471 rows but only 470 unique group IDs, and the only duplicate group (`DG-f8e32066a54f843c`) represents two different conflict contexts for the same underlying image relationship.

## Missing `ham_paths` row
The row with `duplicate_group = DG-681c50d4c60d4313` has:

- `binary_paths = data/isic/data/test/malignant/507.jpg;data/isic/data/train/malignant/439.jpg`
- `ham_paths = ''`
- `recommended_action = keep_test_exclude_train`

This is best interpreted as a source-evidence gap in the HAM-side reference, not as a valid multi-path HAM record. The field is empty; there is no evidence that the source intended a hidden, alternate, or implicit HAM path. The safest classification is: incomplete source evidence in the original CSV, not a queue-copy error.

## Delimiter and field semantics
The actual delimiter in `binary_paths` and `ham_paths` is a semicolon (`;`). Each field can contain one path or multiple paths. This is not a comma-separated list.

Counts from the original source file:
- original conflict rows: 471
- unique group IDs: 470
- unique individual image paths: 533 (counting unique entries across `binary_paths` and `ham_paths` after splitting semicolon-delimited values)
- groups with multiple conflict types: 1
- rows with missing paths: 1 row with empty `ham_paths`
- rows with multiple paths: 2 rows with multiple binary entries and 2 rows with multiple HAM entries

## Queue comparison to original source
Every row in the R5 queue maps back to a single original source row by `source_row_number`. The queue copies the exact original `conflict_id`, `binary_paths`, `ham_paths`, `conflict_type`, and `recommended_action` values. The queue does not lose information from the source file.

## R5A reassessment
The R5A conclusion was too strict if it treated the duplicate `duplicate_group` value as automatically erroneous. The repeated group value is valid as a group-level identifier. The remaining caveat is the incomplete `ham_paths` entry in one row, which constitutes a documentation limitation rather than a queue-replication failure.

## Final interpretation
The source-test conflict queue is semantically valid as a group-level ledger with one incomplete HAM reference. It is not a row-unique image ledger and should not be treated as 471 independent images without further decomposition.
