# R5E ZIP Human-Review Recovery Assessment

## Finding
`files.zip` contains four flat entries: a DOCX visual-review report, a visual-review summary CSV, a validation report, and a SHA-256 manifest. The DOCX contains 40 embedded image objects, but the ZIP contains no separate decision form, reviewer-submitted CSV, or screenshot record.

The ZIP records PAIR_0001 as `CONFIRMED_BY_USER (SAME_PHOTO)`. That record is corroborated by the prior explicit user confirmation and the latest final/workflow decision copies. PAIR_0002–PAIR_0020 are each marked `PENDING_HUMAN_REVIEW` in the archived report and have blank human-decision cells in the archived summary and current working copies. No decision for those pairs was recovered.

- Human decisions preserved: 1 (PAIR_0001; no new decision recovered from the ZIP for PAIR_0002–PAIR_0020).
- AI advisory recommendations: 20 total; 19 are the only recommendation evidence for their pair (PAIR_0002–PAIR_0020).
- Pending human decisions: 19.
- Ambiguous evidence classifications: 0.
- No usable evidence: 0.
- Explicit decision labels recovered: SAME_PHOTO.
- Label vocabulary note: the current recovery task lists `DISTINCT`, while the original R5E reviewer guide permits `DISTINCT_PHOTOS`. No distinct decision was recovered, so no label conversion was made; the recovered CSV contains only `SAME_PHOTO`.
- The registration/correlation/SSIM values are computational evidence, not human decisions.

## PAIR_0001 preservation and timestamp discrepancy
The recovered CSV preserves the user-specified existing values exactly, including timestamp `2026-11-16T02:47:28.6227219Z`, the existing notes and rationale, and blank reviewer ID. The older first-batch working copy contains a different timestamp `2026-11-16T08:17:26Z`. The later final visual-review and workflow copies contain the requested timestamp; this package retains that requested/latest value and records the older discrepancy without changing either source.

## Archive provenance and limits
- ZIP: `E:\Cancerdetection\EG-VAN_Backups\files.zip`
- Size: 1632525 bytes
- Last modified UTC: 2026-11-16T03:40:44.988186+00:00
- SHA-256: `9fa16fe1297cda246d8be3570118f11f24ee55395051c6eff805f92ffef7184a`
- DOCX core author: `python-docx`; stored created/modified values are `2013-12-23 23:15:00+00:00` / `2013-12-23 23:15:00+00:00`. These document metadata fields do not establish reviewer identity.
- The report and summary identify AI recommendations as advisory and the human status separately. The report's visual descriptions are retained as AI-advisory evidence, not copied into human fields.
- The archived internal manifest entries were independently checked against ZIP member bytes: 3 entries; errors: 0.

## Scope
This recovery covers only the selected 20-pair batch. It does not resolve all 449 duplicate relationships or all 471 source-test conflict records, approve a cohort, or update the master benign-pair ledger. PAIR_0002–PAIR_0020 still require human judgment.
