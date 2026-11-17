# R3 Validation Record

## Scope and safeguards

- Read-only audit of existing source, configuration, metadata, saved reports, CSVs and checkpoint file metadata.
- No Git commands, training, inference, evaluation, tests, plot regeneration or dataset preparation were run.
- No patient image contents or model weights were opened/deserialized.
- Existing R1-R2F audit packages and project inputs were not intentionally modified.
- All result values are linked to saved artifacts or marked unavailable/unverified in `R3_EXISTING_RESULTS_INVENTORY.csv`.

## Validation results

- **Deliverables:** all 11 substantive deliverables are nonempty. The manifest is separate and hashes those 11 files.
- **CSV parsing:** .NET `TextFieldParser` parsed all four CSVs with consistent row widths and expected columns:
  - `R3_PROJECT_FILE_INVENTORY.csv`: 356 records, 7 columns.
  - `R3_EGVAN_ARCHITECTURE_AUDIT.csv`: 16 records, 7 columns.
  - `R3_EXISTING_RESULTS_INVENTORY.csv`: 546 records, 11 columns.
  - `R3_PAPER_VS_IMPLEMENTATION_MATRIX.csv`: 22 records, 8 columns.
- **Source paths:** all 33 architecture-source references, 38 explicit matrix evidence paths, and all 546 results-inventory source-artifact paths resolve. The 15 explicit paths in the Markdown reports also resolve.
- **Project inventory:** 346 file-level entries marked `PRESENT` exist. Nine directory-count summaries are not treated as file paths. One Stage23 checkpoint reference is explicitly marked `MISSING_REFERENCED_ARTIFACT`; that absence is also documented in the external-validation audit.
- **Historical package integrity:** all nine prior R1-R2F manifests parsed, and every listed file hash passed: 62 entries total, zero missing files or hash mismatches. No prior audit package files were written by this R3 operation.
- **Saved result linkage:** the existing validation report contains checkpoint SHA-256 `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`, matching the recorded `best.pt` hash. This establishes artifact linkage only; it does not validate the data split or scientific result.
- **R3 manifest:** generated and checked after this report; it contains the SHA-256 hashes for the 11 substantive deliverables and all entries verify.

The Python executable was unavailable on `PATH`; CSV parsing and file validation were performed with PowerShell/.NET. An initial validation expression failed due to a malformed PowerShell regular expression; the corrected checks above completed successfully. These were audit-tool invocation issues, not project failures.

## Interpretation limits

“Parsed,” “present,” “hash matches,” and “source contains implementation” do not mean the cohort is approved or a method is scientifically validated. The seven-class Stage23 registry's referenced checkpoint/evaluation files are absent and are explicitly marked as such. Exploratory and synthetic evidence remains labeled accordingly.
