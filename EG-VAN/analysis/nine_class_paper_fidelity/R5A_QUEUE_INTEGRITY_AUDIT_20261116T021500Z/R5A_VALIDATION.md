# R5A Validation

## Checks performed
- Verified each queue row maps to the original source CSV or reports an integrity failure.
- Verified pair IDs are unique and complete in the duplicate queue.
- Verified the source-test conflict queue preserves original group semantics and found a duplicate `conflict_id` plus missing `ham_paths` evidence.
- Verified that the only human-reviewed row in the benign review ledger is unchanged and separate from automated AI decisions.
- Verified the current SHA-256 values of all original-input files recorded in the R5 input register against the values currently on disk.
- Verified that the substantive R5A files exist, are nonempty, and the manifest matches their hashes.

## Overall result
`NOT_READY_INTEGRITY_FAILURE`
