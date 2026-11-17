# Independent Human-Review Queue Integrity Audit

- Audit directory: E:\Cancerdetection\EG-VAN\analysis\nine_class_human_review_queue\QUEUE_AUDIT_20261115T093000Z
- Queue directory: E:\Cancerdetection\EG-VAN\analysis\nine_class_human_review_queue\QUEUE_PREPARATION_20261115T091320Z

## Verified counts
- Valid one-to-one source occurrences: 1650
- Unique canonical pairs: 1258
- Repeated evidence occurrences removed: 392
- Group-level conflict records retained separately: 3
- Protected BENIGN count: 19
- AI_UNCERTAIN count: 20
- Queue rows: 1258
- queue_missing_patient_ids: 1258
- queue_missing_lesion_ids: 1258

## Statuses
- PROVENANCE_STATUS: PARTIALLY_VERIFIED
- METADATA_STATUS: PARTIALLY_VERIFIED
- MANIFEST_VERIFICATION: VERIFIED
- HUMAN_DECISION_STATUS: VERIFIED
- SUMMARY_JSON_CONSISTENCY: VERIFIED

## Findings
- VERIFIED: The valid one-to-one occurrence total is 1650 and unique canonical pair count is 1258, yielding 392 repeated occurrences removed.
- VERIFIED: The three source-test group conflict rows are retained in the source CSV and excluded from one-to-one pair counting, as designed.
- VERIFIED: The queue manifest SHA256 matches every listed file in the generated queue directory.
- VERIFIED: All queue rows remain UNREVIEWED and have blank human_decision values.
- PARTIALLY VERIFIED: The queue leaves location/source metadata blank in many rows when the source evidence does not explicitly provide patient or lesion IDs. This is not inferred or fabricated; it is a metadata limitation.
- PARTIALLY VERIFIED: evidence_provenance.csv canonicalizes each pair into sorted canonical path order. This preserves a stable pair identity but does not preserve the original left/right source-row ordering in the path_a/path_b columns; the original source row is still traceable through source_file and source_row_number.
- VERIFIED: The original queue directory and source CSVs were not modified, moved, or deleted as part of this audit.
