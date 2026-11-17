# R5C Queue Information Preservation Audit

## Objective
Audit whether the R5 source-test conflict queue preserves the original source information required for human review. The audit is read-only.

## Verified checks
- The R5B manifest was validated against the package files it lists. All listed files were present and matched their recorded SHA-256 values.
- Every queue row maps uniquely to its exact original row via `source_row_number`.
- The queue row count matches the original source row count exactly: 471 rows in each file.
- The `duplicate_group` field preserved all original IDs exactly.
- The raw `binary_paths` field preserved exactly in `image_id` for all 471 rows.
- The raw `ham_paths` field preserved exactly in `source_reference` for all 471 rows.
- The raw `conflict_type` and `recommended_action` values preserved exactly.
- There are zero missing or extra individual paths across the queue versus the original source.
- The repeated group ID `DG-f8e32066a54f843c` is a valid repeated group label, not a loss event.
- The empty `ham_paths` value in `DG-681c50d4c60d4313` is preserved as an empty `source_reference` and is thus not falsely imputed.

## Conclusion
For the fields and path values represented in the R5 queue, the queue is information-loss free. The queue is a review-oriented projection of the original source rows with a reduced column set, but it preserves the essential raw values required for auditing.
