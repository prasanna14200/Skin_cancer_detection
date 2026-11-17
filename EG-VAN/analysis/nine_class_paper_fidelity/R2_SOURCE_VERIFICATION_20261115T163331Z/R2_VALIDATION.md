# R2 Validation

## Structural validation

Status: `VERIFIED` after the final checks.

- Expected output set: 9 files total, comprising the 8 named reports/CSVs plus `R2_MANIFEST.sha256`.
- All expected files are present and non-empty.
- `TABLE2_SOURCE_TRANSCRIPTION.csv` contains 54 cell records: 9 rows x 6 printed columns. Every record carries Table 2, printed p. 72863, viewer page 12, zero-based PDF page index 11, row label, column heading, exact visible value, qualification, status, and evidence method.
- The source transcription records all nine table rows; no illegible or missing source cells were found.
- `TABLE2_COMPARISON.csv` contains 64 comparison entries, each with a permitted classification.
- Manifest lists exactly the 8 non-manifest outputs, once each; all SHA-256 values match.
- Input hashes were rechecked: the source PDF, existing Table 2 CSV, and R1 manifest entries match their recorded values.
- Temporary isolated table-preview PDFs were removed after visual inspection.

## Scientific/source verification

Status: `PARTIALLY_VERIFIED`.

- Table 2's printed vector content is visually verified. Its NV augmented cell literally reads `00`; the intended numerical meaning is not stated.
- The existing CSV has one cell mismatch (`00` versus `0`) and a different row order; no row or column is missing.
- Official ISIC sources verify the 2017 Task 3 schema and release counts. Treating the paper's 3,297-image binary table as the complete official Task 3 release with official labels is contradicted; the actual EG-VAN source package remains unverified.
- The semantics and mutual exclusivity of the seven diagnoses plus two broad labels are not fully established.

## Preservation and scope

- R1 files and the existing Table 2 transcription were not modified; hashes and the R1 manifest were checked read-only.
- No patient/lesion image, contact sheet, queue, model output, or human decision was accessed.
- No source code, dataset, notebook, label, split, model file, or Git state was modified.
- No download, training, evaluation, or inference was performed.

Structural validation does not upgrade unresolved scientific provenance claims.
