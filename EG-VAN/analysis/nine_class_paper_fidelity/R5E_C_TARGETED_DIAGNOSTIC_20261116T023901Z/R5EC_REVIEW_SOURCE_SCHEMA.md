# R5EC Review Source Schema

## A. benign_pair_review_ledger.csv
Headers: binary_image_path, candidate_path, candidate_pair_id, source_split, review_batch, candidate_source, candidate_image_identifier, phash_distance, dhash_distance, pixel_mae, pixel_correlation, coarse_correlation, reviewer_decision, reviewer_notes, review_status, review_timestamp_utc, evidence_reference

This ledger is the canonical source of genuine human-reviewed duplicate pairs. The decisive columns are `review_status`, `reviewer_decision`, and `review_timestamp_utc`. Only rows with `review_status == "reviewed"` and a non-empty `reviewer_decision` are treated as genuine human evidence.

## B. R5_DUPLICATE_ADJUDICATION_QUEUE.csv
Headers: pair_id, image_a_id, image_b_id, source_a, source_b, source_split_a, source_split_b, ai_assessment, ai_assessment_method, ai_confidence, relation_category, conflict_flags, review_status, human_decision, human_rationale, reviewer_id, review_timestamp, source_record, source_row_number

This queue is a review projection, not a ledger of final adjudication decisions. It contains queue row metadata, unresolved states, and the selected pair paths; the `review_status` field in this queue is `NOT_HUMAN_REVIEWED` for the known pair, while the legitimate human decision sits in the separate ledger.

## C. R5E_SELECTED_PAIRS.csv
Headers: queue_row_number, pair_id, image_a_id, image_b_id, source_a, source_b, source_split_a, source_split_b, ai_assessment, ai_assessment_method, ai_confidence, relation_category, conflict_flags, selection_priority, selection_reason, image_a_exists, image_b_exists, image_a_readability, image_b_readability

This file records the 20 selected unresolved pairs for manual review. The selection deliberately excluded any queue row already recognized as having a genuine human decision in the canonical review ledger.
