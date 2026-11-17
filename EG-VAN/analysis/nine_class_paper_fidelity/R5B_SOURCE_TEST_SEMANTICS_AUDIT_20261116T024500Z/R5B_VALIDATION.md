# R5B Validation

## Checks performed
- Verified the full original source CSV schema and all group-level rows.
- Confirmed the repeated `duplicate_group` value is valid group semantics, not a queue-copy corruption.
- Confirmed the missing `ham_paths` value is an incomplete source evidence field, not a queue transformation error.
- Verified the semicolon delimiter and multi-path semantics in the original data.
- Verified each R5 queue row maps back to its exact source row by `source_row_number`.
- Confirmed the copied fields match the original values exactly.
- Verified the package files are nonempty and the manifest matches all substantive outputs.

## Final status
`SOURCE_TEST_QUEUE_VALID_WITH_DOCUMENTATION_LIMITATIONS`
