# R2D Validation

## Source identity

- Original PDF SHA-256 recalculated before inspection: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3` — PASS.
- Requested printed pages 72856, 72857, 72863, 72869, and 72872 were visually inspected — PASS with limitation: the exact p. 72869 13-technique sentence was not legible enough for independent visual transcription and is marked text-stream-only.
- NV augmented entry is preserved literally as `00` — PASS.

## Deliverable validation

The package contains the eight substantive deliverables plus this validation file and `R2D_MANIFEST.sha256`. All nine expected files are nonempty. The manifest hashes the eight substantive deliverables.

- `R2D_VISUAL_EVIDENCE_INVENTORY.csv` parses; required source-locator and evidence columns are present — PASS.
- `R2D_STATUS_CHANGE_MATRIX.csv` parses; all six R2C conclusions have old/new statuses, evidence, and reasons — PASS.
- All quoted passages and inventory rows identify section/page and stream/form locators where recoverable — PASS; symbolic Section B description is explicitly labeled as a summary rather than a verbatim quotation.
- All reported visual limitations are disclosed — PASS.

## Preservation checks

Before creating this package, all listed substantive-file hashes and file counts matched the manifests for:

- R1: 6 files — PASS
- R2: 8 files — PASS
- R2A: 7 files — PASS
- R2A-SV1: 4 files — PASS
- R2B: 7 files — PASS
- R2C: 7 files — PASS

The original PDF matched its expected hash before inspection. No prior audit package or source PDF was intentionally modified. These checks cover files listed by the existing manifests; no Git cleanliness claim is made.

## Scope controls

No patient images, masks, datasets, model weights, predictions, or unrelated project artifacts were accessed. No training, inference, evaluation, or Git operation was run. Table 2's `00` was not numerically repaired, and no undocumented reconciliation or augmentation step is asserted.
