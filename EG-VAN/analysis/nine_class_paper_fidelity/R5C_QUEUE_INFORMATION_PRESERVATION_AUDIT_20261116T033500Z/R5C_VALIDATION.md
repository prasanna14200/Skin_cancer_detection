# R5C Validation

## Checks performed
- Verified the R5B manifest against the files it lists.
- Verified the queue row count equals the original source row count (471 / 471).
- Verified every queue row maps uniquely to its original row by `source_row_number`.
- Verified raw field preservation for `duplicate_group`, `binary_paths`, `ham_paths`, `conflict_type`, and `recommended_action`.
- Verified the individual path sets and counts match exactly across all rows.
- Verified and recorded SHA-256 hashes for all input files.
- Verified the R5C manifest matches the generated output files.

## Final status
`QUEUE_LOSSLESS`
