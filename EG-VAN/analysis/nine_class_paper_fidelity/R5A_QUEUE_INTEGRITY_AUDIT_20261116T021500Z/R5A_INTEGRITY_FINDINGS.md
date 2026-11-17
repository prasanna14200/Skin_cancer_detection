# R5A Integrity Findings

## Scope
This audit inspected the R5 package only. It did not modify any original data, queue files, frozen splits, or prior audit materials.

## Queue lineage findings

### Duplicate adjudication queue
- All 449 duplicate-queue rows resolve to existing rows in `analysis/nine_class_overlap_review/unresolved_priority_pairs.csv`.
- Every `source_row_number` resolves to a valid original row and the queued `image_a_id` and `image_b_id` match the original `path_a` and `path_b` values.
- The queued `ai_assessment` and `ai_assessment_method` values match the original `decision` and `decision_method` values for the mapped rows.
- The queue uses file paths as the image identifiers, not stable, source-independent IDs.
- The queue includes inferred summary fields (`source_a`, `source_b`, `source_split_a`, `source_split_b`) that are not direct source columns in the original CSV. These are derived for human review convenience and are not original source-provenance fields.
- Pair IDs are unique and complete: 449 unique `pair_id` values for 449 rows.

### Source-test conflict queue
- The source-test queue contains 471 rows but only 470 unique `conflict_id` values.
- One conflict group ID is duplicated: `DG-f8e32066a54f843c` appears twice with different `conflict_type` values and different `binary_paths` semantics.
- One row has an empty `ham_paths` value (`duplicate_group = DG-681c50d4c60d4313`).
- The queued `image_id` values are not independent image identities; they are path strings associated with a conflict group and may represent a group record rather than a single image.
- The queue should not be treated as 471 independent images or 471 independent conflict records until conflict-group semantics are corrected.

## Existing human decisions
- `analysis/nine_class_recovery/benign_pair_review_ledger.csv` contains exactly one row with `review_status == reviewed`.
- `reviewer_decision = SAME_PHOTO` for `binary_image_path = data/isic/data/test/benign/802.jpg` and `candidate_path = data/raw/HAM10000_images_part_1/ISIC_0028399.jpg`.
- The review timestamp is `2026-10-19T12:25:44+00:00` and the evidence reference is `analysis/nine_class_overlap_completion/human_review_queue.csv#row=11`.
- `analysis/nine_class_recovery/benign_pair_evidence_feedback.csv` contains no explicit human-review decision column; it is auxiliary evidence feedback, not a human adjudication record.
- `analysis/nine_class_overlap_review/review_decisions.csv` contains 2,797 rows with `human_review_status = not_human_reviewed`; all are automated or AI-generated decisions, not human-approved adjudications.

## Input hash verification
- All files listed in `R5_INPUT_EVIDENCE_REGISTER.csv` are present and match their recorded SHA-256 values.
- Therefore the current workspace state is consistent with the recorded R5 snapshot for those inputs.
- A matching hash confirms current consistency with the snapshot, not the indefinite historical accuracy of the files before the snapshot was recorded.

## Integrity conclusion
The duplicate-adjudication queue is lineage-consistent with the original unresolved-pair source, but the source-test conflict queue is not integrity-clean because the `conflict_id` is duplicated and one conflict row has incomplete `ham_paths` evidence. The package therefore fails the integrity threshold for human review readiness and cannot be certified as `READY_FOR_HUMAN_REVIEW`.
