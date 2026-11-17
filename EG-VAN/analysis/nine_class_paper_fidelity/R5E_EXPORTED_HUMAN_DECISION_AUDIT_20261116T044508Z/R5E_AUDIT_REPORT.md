# R5E Exported Human Decision Audit

## Export identification
- Selected export: `D:\Downloads\R5E_HUMAN_DECISIONS_WORKING_COPY.csv`
- Downloads candidates: 1 CSV; this was the sole CSV candidate.
- Size: 1787 bytes
- Last modified: 2026-11-16T10:08:56.277471+05:30 local / 2026-11-16T04:38:56.277471+00:00 UTC
- SHA-256: `5acdb20abec924b6ba50dbb12f9139066c4687e11f7bd9df76b81311b00746e1`
- Parsed data rows: 20; header: `pair_id, queue_row_number, human_decision, reviewer_id, review_timestamp_utc, visual_evidence_notes, decision_rationale`; fields in every row: 7.
- The file was read twice with identical size, modification time, and SHA-256. A direct PowerShell hash attempt encountered a sharing lock, but read-only Python access succeeded.

## Decisions and counts
- Explicit nonblank human decision entries: 20/20.
- Pending/blank decisions: 0.
- Raw value counts: {"SAME_PHOTO": 8, "DISTINCT_PHOTOS": 10, "DISTINCT": 0, "UNCERTAIN": 2, "BLANK": 0}.
- Invalid labels under the original R5E reviewer guide and interface: 0.
- Decision tokens that conflict with this audit request's exact allowlist: 10 (`DISTINCT_PHOTOS` is used where the task list says `DISTINCT`).
- Duplicate pair IDs: 0; missing IDs: 0; unexpected IDs: 0.
- Conflicting decisions for the same pair: 0.
- The supplied 20-item decision list matches the raw CSV decision labels: YES.

## Label-schema finding
The original reviewer guide explicitly permits `SAME_PHOTO`, `DISTINCT_PHOTOS`, and `UNCERTAIN`; the interface code's `allowedDecisions` array uses the same values. The current audit request instead lists `DISTINCT`. Therefore `DISTINCT_PHOTOS` is valid under the original R5E workflow schema but conflicts with the exact current-task token set. The CSV retains all ten raw `DISTINCT_PHOTOS` strings unchanged; none were converted to `DISTINCT`. The source documents do not establish `DISTINCT` as the original workflow's canonical value.

## Column-order and timestamp finding
The raw export header order is `pair_id, queue_row_number, human_decision, reviewer_id, review_timestamp_utc, visual_evidence_notes, decision_rationale`. All 20 `reviewer_id` cells are genuinely blank; all 20 timestamps are in `review_timestamp_utc`, and all row widths are seven fields. In the export code, `headers` is read in the exact template order, the save handler assigns `reviewer_id` and `review_timestamp_utc` as separate properties, and the download serializes `headers.map(h => records[p.pair_id][h])`. This is not a column-order or CSV-serialization bug. The supplied representation's apparent shift is consistent with omitted blank cells in a display; it is not present in the raw CSV.

Timestamp strings were retained verbatim. PAIR_0001 remains `SAME_PHOTO`, reviewer ID blank, timestamp `2026-11-16T02:47:28.6227219Z`, and its saved visual notes/rationale match the latest confirmed copy. The older first-batch copy uses `2026-11-16T08:17:26Z`; that historical discrepancy is recorded, not silently changed.

## Mapping
- Original selected pairs: 20 rows.
- Original duplicate queue: 449 rows.
- Queue-row references unique and sequential 1–20: PASS.
- Pair ID and image-path mappings against selected pairs and queue: 20/20 match; failures: 0.

## Browser-saved versus exported state
The HTML workflow stores saves only in the current tab's in-memory `records` object and creates a CSV Blob from that same object on download. It does not write browser storage or submit to a server. Consequently, the downloaded CSV is a snapshot; the original on-disk starter CSV is not updated by in-tab saves. The accessible separate browser page currently shows PAIR_0020 blank, so it cannot establish the state of the user's export tab. No persistent user-tab state was available for independent comparison. The raw downloaded export is the audited record.

## Decision validity summary
- Valid under the original R5E guide/interface schema: 20/20.
- Exact-token matches to the current audit allowlist: 10/20.
- Human decisions with the `DISTINCT_PHOTOS` versus `DISTINCT` conflict: 10.
- Reviewer IDs blank: 20; timestamps blank: 0.
- Queue mapping failures: 0; conflicting decisions: 0.

## Source hashes captured
- export: `5acdb20abec924b6ba50dbb12f9139066c4687e11f7bd9df76b81311b00746e1`
- selected_pairs: `be906eef305bd252c6cce878280824a302c0a85a96f4368aadcf406b1825264f`
- template: `ee965c47e2db597b711adecbf1e72411cc7628fd510eca8fc1bbba27816e64a6`
- reviewer_instructions: `e659720250d53e5626850c5d993d1c720c29e722490cf9a7a322c31070ea940e`
- original_queue: `11a286b366ce7b07bc9f88fc69b9404ea47acba6b69a8c4f48a089a71514f7cc`
- workflow_copy: `71081977d7a60fc912247e1b3804e9bb7b16e56dd85ece0f00a41d7ab00d0d02`
- interface: `9bfa36822d911546c83572b1a68c8f13889d4c9fb2c013c10a60c47756b181ca`
- prior_zip_recovery: `a9df2c6fde59e673ae092e1f2764840c8c5ac95e07dbd38a4164109dc5b2156c`
- final_working_copy: `71081977d7a60fc912247e1b3804e9bb7b16e56dd85ece0f00a41d7ab00d0d02`

This audit is read-only. It does not update the master ledger, source CSV, queue, images, browser storage, or prior packages, and makes no cohort or split approval.
