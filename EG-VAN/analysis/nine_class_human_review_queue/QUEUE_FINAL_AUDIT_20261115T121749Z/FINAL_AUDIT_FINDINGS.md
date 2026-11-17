# Final Set-Equality and Evidence-Preservation Audit

- Audit directory: E:\Cancerdetection\EG-VAN\analysis\nine_class_human_review_queue\QUEUE_FINAL_AUDIT_20261115T121749Z
- Corrected queue: E:\Cancerdetection\EG-VAN\analysis\nine_class_human_review_queue\QUEUE_CORRECTED_20261115T152000Z
- Overall status: **PARTIALLY_VERIFIED**

## Reconciled counts
- Source rows: 1653
- Valid one-to-one occurrences: 1650
- Group-level conflicts: 3
- Malformed/missing-path exceptions: 0
- Unique source canonical pairs: 1258
- Queue rows / unique keys: 1258 / 1258
- Provenance rows: 1650
- Archive records (valid + group conflicts): 1653 (1650 + 3)

## Check results
- **VERIFIED**: source_canonical_pair_set
- **VERIFIED**: queue_set_equality
- **VERIFIED**: queue_id_recomputation
- **VERIFIED**: protected_benign_reconciliation
- **VERIFIED**: ai_uncertain_reconciliation
- **PARTIALLY_VERIFIED**: metadata_field_inventory
- **VERIFIED**: group_conflict_preservation
- **VERIFIED**: occurrence_provenance_archive
- **VERIFIED**: manifest_hashes
- **FAILED**: manifest_file_set
- **VERIFIED**: human_decision_status

## Findings
- Queue/source set equality: complete; no missing, unexpected, or duplicate keys.
- Stable IDs: all 1258 queue rows match the SHA-1/NUL algorithm.
- Protected BENIGN: 19/19 source records map to queue rows with the source automated_category in priority_categories.
- AI_UNCERTAIN: 20/20 source records map to queue rows retaining AI_UNCERTAIN in ai_assessments.
- Group conflicts: 3/3 original rows match the conflict CSV and archive payloads; all are retained as group-level records.
- Occurrence provenance/archive: 1650/1650 valid occurrences fully match orientation, row/file, normalized and canonical paths, IDs, and raw payload (object key order ignored).
- Manifest: 7/7 listed hashes match. Missing listed files: none. Unlisted actual files: CORRECTION_REPORT.md.
- Metadata note: source evidence has populated split fields in unresolved_priority_pairs.csv (source_split_a: 449; source_split_b: 147), benign_review_plan.csv (source_split: 83; top_candidate_source: 83; top_candidate_lesion_id: 83), and ai_pair_review.csv (source_split: 429; candidate_source: 429). The corresponding queue source/source-split/lesion-ID fields are blank across 1,258 rows; no metadata was mapped or inferred in this audit. Patient/image identifiers were not inferred from paths.
- Human review fields: 0 nonblank decisions; 0 statuses other than UNREVIEWED.

## Limits
No problems were repaired. This audit reads path and tabular metadata only; it does not inspect image pixels, adjudicate duplicates, approve a dataset, or modify existing files.
