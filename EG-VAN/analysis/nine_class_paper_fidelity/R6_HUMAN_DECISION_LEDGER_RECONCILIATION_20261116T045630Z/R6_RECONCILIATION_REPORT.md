# R6 Human Decision Ledger Reconciliation

Generated: `2026-11-16T04:56:30Z`  
Scope: read-only reconciliation; outputs are a separate candidate package. No source ledger, queue, image, dataset, prior package, training run, inference, or cohort approval was modified or performed.

## Result

- Audited R5E export: **20/20** unique IDs (`PAIR_0001`–`PAIR_0020`): **8 SAME_PHOTO**, **10 DISTINCT_PHOTOS**, **2 UNCERTAIN**. All reviewer IDs are blank; all timestamps are present.
- Canonical mappings: `SAME_PHOTO → SAME_PHOTO`, `DISTINCT_PHOTOS → DISTINCT`, `UNCERTAIN → UNCERTAIN`. Raw labels remain separately recorded.
- Existing benign-pair ledger contributes **1** additional explicit human decision: `PAIR_0124`, queue row **124**, `SAME_PHOTO`, timestamp `2026-10-19T12:25:44+00:00`. Both image paths map exactly to that queue record.
- Combined queue reconciliation: **21 human-reviewed** pairs (**9 SAME_PHOTO**, **10 DISTINCT**, **2 UNCERTAIN**) and **428 unreviewed**. The two uncertain pairs remain unresolved. **430 duplicate-candidate relationships remain unresolved** (428 unreviewed + 2 uncertain). The 9 confirmed same-photo pairs are known duplicate relationships that still require separate data handling; this package changes no data.
- Original benign ledger: **429** rows; **88** exact unordered path-pair matches to the 449-row queue (1 reviewed and 87 unreviewed); **341** ledger rows do not map to that queue. No duplicate unordered path pairs, duplicate nonblank candidate IDs, or conflicting reviewed ledger records were found. None of the 20 exported pairs existed in the ledger. Candidate: **429 preserved + 20 appended = 449** rows.
- Source-test inventory: **471** conflict rows (**469 `binary_test_HAM`**, **2 `binary_train_test`**). **0** exact reviewed pair matches and **0** reviewed endpoints appear in this inventory. All **471** remain outstanding; no decisions were propagated via shared endpoints.
- Stage 11A `decision_ledger.csv` contains 19 placeholder rows with blank decision, reviewer, notes, and date fields; it is not human-review evidence and is not the benign-pair master ledger.

## PAIR_0001 provenance

PAIR_0001 remains `SAME_PHOTO`, reviewer ID blank. The audited export/current timestamp is preserved exactly as `2026-11-16T02:47:28.6227219Z`. The older one-row working copy records `2026-11-16T08:17:26Z`. Both originals are preserved; the discrepancy is documented, not harmonized. The candidate uses the audited export timestamp.

## Files

- `R6_SOURCE_EVIDENCE_REGISTER.csv` — 21 explicit decision records with source paths, row references, hashes, and queue mappings.
- `R6_DECISION_NORMALIZATION_AUDIT.csv` — raw-to-canonical label trace.
- `R6_RECONCILED_HUMAN_DECISIONS.csv` — 20 audited exports plus the prior ledger decision.
- `R6_MASTER_LEDGER_CANDIDATE.csv` — 429 legacy rows preserved plus 20 new rows; provenance columns are additive.
- `R6_DUPLICATE_QUEUE_STATUS.csv` — all 449 rows with original fields retained and effective reconciliation columns added.
- `R6_REMAINING_SOURCE_TEST_CONFLICTS.csv` — all 471 conflict rows retained; none cleared by unrelated pair decisions.
- `R6_VALIDATION.md` — checks and manifest-verification status.
- `R6_MANIFEST.sha256` — hashes the eight payload files (cannot include its own hash).

## Input evidence and SHA-256

- `D:\Downloads\R5E_HUMAN_DECISIONS_WORKING_COPY.csv` — SHA-256 `5acdb20abec924b6ba50dbb12f9139066c4687e11f7bd9df76b81311b00746e1`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_FIRST_HUMAN_ADJUDICATION_BATCH_20261116T022438Z\R5E_SELECTED_PAIRS.csv` — SHA-256 `be906eef305bd252c6cce878280824a302c0a85a96f4368aadcf406b1825264f`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5_COHORT_HUMAN_REVIEW_PREPARATION_20261115T214500Z\R5_DUPLICATE_ADJUDICATION_QUEUE.csv` — SHA-256 `11a286b366ce7b07bc9f88fc69b9404ea47acba6b69a8c4f48a089a71514f7cc`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_recovery\benign_pair_review_ledger.csv` — SHA-256 `ba89c8f9c54a96c08f58c2ac55db801a05d4018b470332eaa5dc6c0f0dd51999`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_overlap_review\source_test_boundary_conflicts.csv` — SHA-256 `0f48a8709c7cd80fa1ad2b6fb991932bbd6e21f0996c6c88c81269e2c0867c72`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_EXPORTED_HUMAN_DECISION_AUDIT_20261116T044508Z\R5E_DECISION_RECONCILIATION.csv` — SHA-256 `759752fd81e58509cb45bc21c8a717aaff6f8458e383d7c71abe467691b80a2d`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_EXPORTED_HUMAN_DECISION_AUDIT_20261116T044508Z\R5E_AUDIT_MANIFEST.sha256` — SHA-256 `960cce035d67e03f69f57dd4e925a956f4b9e2c521e303fb64fd6acfa14ccb64`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_FIRST_HUMAN_ADJUDICATION_BATCH_20261116T022438Z\R5E_HUMAN_DECISION_TEMPLATE_PAIR_0001_WORKING_COPY.csv` — SHA-256 `87642e5da19e736dd98cc0677dcaec7273903f5b9161ffa7fa73d40f6dbd4b95`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_FINAL_VISUAL_REVIEW_AND_ADJUDICATION_20261116T040429Z\R5E_FINAL_HUMAN_ADJUDICATION_WORKING_COPY.csv` — SHA-256 `71081977d7a60fc912247e1b3804e9bb7b16e56dd85ece0f00a41d7ab00d0d02`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_stage11a\decision_ledger.csv` — SHA-256 `dac216e5c68281f9bc07502233b2ffb5c59cb415ab778d8b72c327e6967239ce`

## Scope limits

This is not the master ledger and does not approve the cohort, a leakage-safe split, or research readiness. No training or inference was performed. The source-test conflict inventory remains a separate blocker: its path identities do not intersect the 21 reconciled decisions and require independent investigation.
