# R2A Validation

## Structural validation

Status: `PASS`.

- The directory contains exactly the seven non-manifest files named in the R2A deliverables list and `R2A_MANIFEST.sha256` (eight files total).
- All eight files are non-empty.
- `TABLE2_ARITHMETIC_AUDIT.csv` parses as 10 records: nine classes plus one total row.
- `R2A_RECONCILIATION.csv` parses as 7 records; every record has a permitted classification and a verified `B - A` difference.
- `R2A_MANIFEST.sha256` lists exactly the seven non-manifest files, once each, and every digest matches.
- The original PDF hash is `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`; the existing transcription hash is `0bfac8b73d01e7c0abab31272f18b0e9dffe7793444bbc70f65fe639a2dba705`. Both match the recorded input hashes.
- All listed R1 and R2 manifest entries match their files; their exact file lists were checked.

## Arithmetic validation

Status: `PASS`.

- Table 2 totals: original 13,312; testing 1,332; train 11,980.
- Each of the nine class rows satisfies `Original = Testing + Train`.
- Augmented numeric subtotal excluding the literal `00` is 34,554. Conditional arithmetic assuming `00` equals zero is also 34,554.
- Conditional Table 2 `Train + Augmented` total is 46,534.
- Section IV-C: training 37,883; validation 6,686; combined 44,569.
- All nine class rows and four count columns were cross-checked against the R2 source transcription; NV `00` remains text in the source-value column.

## Scientific/source verification

Status: `PARTIALLY_VERIFIED`.

The R2 visual transcription identifies the Table 2 source cells, and the original PDF text content stream supports the Section IV-C values. The `00` interpretation and the stage relationship between Table 2 and Section IV-C remain unresolved. A passed arithmetic check does not resolve those scientific/provenance questions.

## Preservation

The source PDF, existing project transcription, R1 files, and R2 files are read-only inputs. Their hashes and prior manifests are rechecked during final validation. No dataset, patient image, source code, notebook, label, split, model file, or Git state is modified.
