# Correction Report

## Checks
- VERIFIED: source files were read-only and only a new output directory was created.
- VERIFIED: raw valid one-to-one occurrences = 1650
- VERIFIED: unique canonical pairs = 1258
- VERIFIED: repeated evidence occurrences = 392
- VERIFIED: protected BENIGN records = 19
- VERIFIED: AI_UNCERTAIN records = 20
- VERIFIED: group-level conflicts retained = 3
- VERIFIED: all queue human decisions remain blank and review_status remains UNREVIEWED.
- VERIFIED: the summary reconciles exactly with the counts produced from the original source CSVs.
- VERIFIED: the manifest SHA256 files were recomputed against the generated outputs on disk.

## Notes
- This output is a provenance-corrected queue copy, not a duplicate decision or dataset approval.
- Missing patient and lesion IDs remain blank because unsupported metadata was not inferred.
