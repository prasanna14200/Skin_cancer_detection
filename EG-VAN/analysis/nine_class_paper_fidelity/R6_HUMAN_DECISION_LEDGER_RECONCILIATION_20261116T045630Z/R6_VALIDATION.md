# R6 Validation

Generated at `2026-11-16T04:56:30Z`. This is a separate candidate; source files were read-only.

## Reconciliation checks

- Export schema matched the actual seven columns; exactly 20 unique IDs cover `PAIR_0001`–`PAIR_0020`.
- All 20 source decisions are nonblank and allowlisted. Raw counts: 8 `SAME_PHOTO`, 10 `DISTINCT_PHOTOS`, 2 `UNCERTAIN`. Exactly 10 `DISTINCT_PHOTOS` labels map to canonical `DISTINCT`; raw labels are retained.
- All 20 export rows matched selected pairs and original queue by ID, queue row, and exact ordered image paths; the prior R5E audit mapping was `MATCH` for every row.
- PAIR_0001 remains `SAME_PHOTO`, reviewer ID blank, current/export timestamp `2026-11-16T02:47:28.6227219Z`. Older one-row copy timestamp `2026-11-16T08:17:26Z` retained as a discrepancy.
- Existing ledger: all 429 original rows and 17 original columns preserved exactly; 0 duplicate unordered path pairs; 0 duplicate nonblank `candidate_pair_id` values; one prior decision maps to `PAIR_0124` / queue row 124. Undecided legacy rows remain undecided.
- Candidate master ledger: 449 unique unordered path pairs (429 preserved + 20 appended); no exported pair overlapped the old ledger; no synthetic candidate IDs were generated.
- Queue status: 449 unique rows; 21 human-reviewed (including the two `UNCERTAIN`) and 428 unreviewed. Original queue columns are preserved; reconciled decisions are separate fields.
- Source-test conflicts: all 471 original records retained; zero exact reviewed pair matches and zero reviewed image endpoints; all 471 remain outstanding.
- Stage 11A ledger: 19 blank placeholders, not counted as decisions.
- Prior R5E audit manifest independently checked against all 6 listed payload hashes.
- All tracked source input hashes were identical before and after generation.

## Manifest

`R6_MANIFEST.sha256` covers the eight deliverable payloads, including this validation report and the reconciliation report. The manifest itself is excluded because self-hashing is recursive. A separate process independently verified all eight payload hashes and the exact package file set. After this validation report was finalized, the manifest was regenerated to include its final hash; a second separate-process verification was then run on the final manifest.
