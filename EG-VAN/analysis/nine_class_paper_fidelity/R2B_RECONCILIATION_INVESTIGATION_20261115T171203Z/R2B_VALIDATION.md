# R2B Validation

## Validation results

Status: `PASS` for package integrity and arithmetic checks. The numerical reconciliation itself remains `UNRESOLVED`.

- Original PDF SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3` — matches the required source hash.
- R2 `TABLE2_SOURCE_TRANSCRIPTION.csv` SHA-256: `b0ce85fa775095e15c07a834b09f81f33935a23230f73538b40cc1dc3b098777` — unchanged and matches the R2 manifest.
- Prior package manifests verified without failures; exact file sets match the pre-output inventory:
  - R1: 6 entries; 7 files including `R1_MANIFEST.sha256`.
  - R2: 8 entries; 9 files including `R2_MANIFEST.sha256`.
  - R2A: 7 entries; 8 files including `R2A_MANIFEST.sha256`.
  - R2A-SV1: 4 entries; 5 files including `ADDENDUM_MANIFEST.sha256`.
- Both R2B CSVs parse using a local Node.js CSV parser. `R2B_RECONCILIATION_CALCULATIONS.csv`: 18 data rows, 23 columns. `R2B_HYPOTHESIS_MATRIX.csv`: 7 data rows, 6 columns. All rows have the declared column count.
- All nine Table 2 cells in the R2B class rows match the R2 source transcription, including literal NV `00`. All nine `Original = Testing + Train` equations pass.
- Independent sums: original 13,312; testing 1,332; train 11,980. Augmented sum 34,554 and `Train + Augmented` 46,534 are conditional on interpreting `00` as zero; the literal-string total is not numeric.
- Section IV-C arithmetic: 37,883 + 6,686 = 44,569. All seven comparison differences in the calculations CSV were independently checked; conditional `44,569 - 46,534 = -1,965`.
- Hypothesis matrix contains H1-H7 exactly once, with a permitted explicit status for each.
- The seven non-manifest deliverables were present and nonempty before writing the manifest. Final validation confirms all eight expected files (seven deliverables plus `R2B_MANIFEST.sha256`) are nonempty, and that the directory contains no other files.
- The R2B manifest contains exactly the seven non-manifest deliverables and every listed SHA-256 matches.
- No writes were made outside this new R2B directory. Existing R1/R2/R2A/R2A-SV1 file sets and manifest entries remain unchanged. No Git command was run; Git cleanliness is not assessed.

## Validation limits

Successful arithmetic and integrity checks do not prove that the paper's Table 2 and Section IV-C totals describe the same cohort or processing stage. No reconciliation is claimed.
