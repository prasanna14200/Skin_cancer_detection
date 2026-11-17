# R2E Validation

## Source and locator checks

- Original PDF SHA-256 recalculated before inspection: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3` — PASS.
- Primary locator recorded in all equation-related deliverables: Section B, printed p. 72857, viewer page 6, zero-based index 5, page object 47, content stream 122 — PASS.
- Equation number `(15)` recovered from the source operators and visual crop — PASS.
- High-resolution full-page visual inspection was not achieved; a low-resolution page preview was available, while the formula region was reviewed separately as a text/math crop. The unrelated figure region was not inspected — LIMITATION RECORDED.
- Font mappings recorded: BLEX font 101 / Encoding 515 / ToUnicode 140; MTSYN font 9 / ToUnicode 34; italic font 102 / ToUnicode 156; RMTMI font 103 / ToUnicode 513; Roman font 10 / ToUnicode 37 — PASS.
- Equation transcription distinguishes visual, text-operator, ToUnicode, and Encoding-Differences evidence. BLEX summation glyphs lack direct Unicode entries and were identified through the font's glyph-name encoding plus visual confirmation — PASS.
- No transformation operation was inferred from general augmentation knowledge — PASS.

## Deliverable checks

All eight substantive deliverables and the manifest exist and are nonempty. The manifest contains hashes for exactly the eight substantive deliverables.

- `R2E_SYMBOL_DEFINITION_INVENTORY.csv` parses and has source locators for every row — PASS.
- `R2E_TRANSFORMATION_IDENTIFICATION.csv` parses; its single family row is not misrepresented as an individually identified operation — PASS.
- Formula preserves visible subscripts, superscripts, bounds, and equation number — PASS.
- The count of verified symbol roles is explained; \(N\) is explicitly left unresolved — PASS.

## Preservation

Before creating this R2E package, existing file counts and manifest-listed hashes passed for R1, R2, R2A, R2A-SV1, R2B, R2C, and R2D. No earlier package was intentionally modified. The source PDF was read-only. No Git operation or Git-cleanliness assertion was made.

## Scope

No patient images, masks, datasets, model weights, or predictions were inspected. No training, inference, evaluation, or augmentation implementation was performed. The unrelated figure region on p. 72857 was excluded from visual review. The 1,965-image discrepancy was not investigated.
