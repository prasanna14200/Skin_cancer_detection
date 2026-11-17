# R5E Queue Mapping Validation

## Source identity
- Original queue: `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5_COHORT_HUMAN_REVIEW_PREPARATION_20261115T214500Z\R5_DUPLICATE_ADJUDICATION_QUEUE.csv`
- Original queue SHA-256: `11a286b366ce7b07bc9f88fc69b9404ea47acba6b69a8c4f48a089a71514f7cc`
- Original queue size: 117551 bytes; records: 449
- Selected-pairs source: `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_FIRST_HUMAN_ADJUDICATION_BATCH_20261116T022438Z\R5E_SELECTED_PAIRS.csv`
- Selected-pairs SHA-256: `be906eef305bd252c6cce878280824a302c0a85a96f4368aadcf406b1825264f`
- Selected rows: 20; unique pair IDs: 20

## Mapping results
- Every selected `queue_row_number` is unique, in range, and resolves to the corresponding original queue row: PASS.
- Pair ID, `image_a_id`, `image_b_id`, AI assessment/method/confidence, relation category, conflict flags, and `source_row_number` were compared field-by-field: PASS.
- Both image paths also match the final visual-review summary and registration records: PASS.
- All 20 decision records preserve the selected-pair order and original `pair_id`/`queue_row_number`.
- Original queue human decisions for these 20 rows are blank and queue status is unresolved/unreviewed.
- Canonical benign-pair ledger: 1 genuine reviewed decision(s) under the rule `review_status == reviewed` and non-empty `reviewer_decision`; selected-pair matches: 0.

The full per-pair path mapping is recorded in `R5E_DECISION_SOURCE_RECONCILIATION.csv`. No queue, image, template, or ledger was modified.
