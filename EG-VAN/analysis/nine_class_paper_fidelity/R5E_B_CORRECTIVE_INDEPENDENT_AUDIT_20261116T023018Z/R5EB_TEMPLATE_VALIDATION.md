# R5EB Template Validation

## Actual human-decision fields in the template
The actual template headers are:
- pair_id
- queue_row_number
- human_decision
- reviewer_id
- review_timestamp_utc
- visual_evidence_notes
- decision_rationale

These are the fields that are logically reserved for human adjudication. The AI-generated assessment values are not copied into those fields.

## Validation results
- Template rows: 20
- Expected selected rows: 20
- Pair IDs match selected batch: TRUE
- Queue row numbers match selected batch: TRUE
- All human-decision fields blank: TRUE
- Reviewer IDs blank: 20/20
- Review timestamps blank: 20/20
- AI-generated fields copied into human decision fields: 0
