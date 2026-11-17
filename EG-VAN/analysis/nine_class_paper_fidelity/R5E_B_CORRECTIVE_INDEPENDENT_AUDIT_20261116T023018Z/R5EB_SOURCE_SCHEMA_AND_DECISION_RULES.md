# R5EB Source Schema and Decision Rules

## Source schemas and actual status values

The audit inspected the real headers and values from the following source files:

- analysis/nine_class_recovery/benign_pair_review_ledger.csv
- analysis/nine_class_overlap_review/review_decisions.csv
- analysis/nine_class_overlap_completion/human_review_queue.csv

### 1) benign_pair_review_ledger.csv
Headers: binary_image_path, candidate_path, candidate_pair_id, source_split, review_batch, candidate_source, candidate_image_identifier, phash_distance, dhash_distance, pixel_mae, pixel_correlation, coarse_correlation, reviewer_decision, reviewer_notes, review_status, review_timestamp_utc, evidence_reference

Observed actual status/decision values:
- review_status values: reviewed, unreviewed
- reviewer_decision values: SAME_PHOTO, empty string
- The actual human decision field is `reviewer_decision` when `review_status == 'reviewed'` and the field is non-empty.

### 2) review_decisions.csv
Headers: path_a, path_b, scope, phash_distance, dhash_distance, label_a, label_b, source_split_a, source_split_b, sha256_a, sha256_b, size_a, size_b, pixel_mae, pixel_correlation, nine_class_target_conflict, decision, decision_method, human_review_status

Observed actual values:
- decision values: confirmed_direct_pixel_automated, confirmed_visual_assistant, confirmed_exact_sha256, unresolved_human_review
- decision_method values: strict_pixel_evidence, candidate_only, visual_inspection_and_pixel_evidence, byte_identity
- human_review_status values: not_human_reviewed

This file does not contain genuine human decisions for the selected batch. It stores automated or unresolved decisions, not human adjudications.

### 3) human_review_queue.csv
Headers: path_a, path_b, scope, phash_distance, dhash_distance, coarse_mae_8bit, coarse_correlation, gradient_correlation, pixel_mae, pixel_correlation, decision, human_review_status

Observed actual values:
- decision values: unresolved_human_review
- human_review_status values: not_human_reviewed

This queue is not a ledger of accepted human decisions; it remains unresolved and not human-reviewed.

## Decision rule used for audit

A genuine human decision was counted only when all of the following are true:

1. The source row comes from `benign_pair_review_ledger.csv`.
2. `review_status` equals `reviewed`.
3. `reviewer_decision` is non-empty.
4. The row has a valid evidence reference.

AI decisions, unresolved queue entries, and empty statuses were excluded even when they contained a prediction string or a queue state.

## Known prior decision

The exact known pair is:

- data/isic/data/test/benign/802.jpg
- data/raw/HAM10000_images_part_1/ISIC_0028399.jpg
- expected decision: SAME_PHOTO
- expected timestamp: 2026-10-19T12:25:44+00:00

This pair appears in the human ledger with review_status=reviewed and reviewer_decision=SAME_PHOTO. It is not in the selected R5E batch.
