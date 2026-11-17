# Reviewer and Adjudicator Workflow

This is a future workflow specification only. No review batch is created here. Do not write decisions into the enriched queue.

## Before review

1. The coordinator confirms the current queue snapshot and creates a new, read-only mapping from neutral `review_item_id` to the two original image files. Keep this mapping restricted.
2. Assign two distinct reviewers with accountable IDs. Give each the same pair inventory in randomized order and neutral Image A/Image B labels. Do not expose paths, filenames, source/split metadata, candidate IDs, `evidence_sources`, evidence row references, `evidence_occurrence_count`, `priority_reason`, `priority_categories`, `ai_assessments`, scores, overlays, or previous decisions.
3. Do not use the enriched queue as the reviewer display: it contains AI and automated-evidence fields. A separate blinded display would need explicit authorization and validation before use.
4. Orient reviewers to the rubric and confidence scale. Use a small calibration exercise separate from the 1,258 pairs and based on independently established examples, if available. Do not use AI assessments or the queue as ground truth. If no reliable examples are available, record that limitation and proceed only after the terminology has been explained.
5. Confirm that reviewers understand this is not diagnosis, label review, patient identification, or dataset approval. No source or split metadata may substitute for visible relationship evidence.

## Independent pass (Reviewer 1 and Reviewer 2 separately)

For each neutral pair ID:

1. Open both original files at a suitable scale while preserving aspect ratio. Inspect original files; do not rely on enhanced, registered, overlaid, or otherwise processed images.
2. Choose exactly one: `SAME_PHOTO`, `SAME_LESION_DIFFERENT_PHOTO`, `DISTINCT`, `UNCERTAIN`, or `NOT_COMPARABLE`.
3. Record confidence (`HIGH`, `MODERATE`, or `LOW`), a concise visual rationale, and limitations. For `NOT_COMPARABLE`, identify the unusable side and reason.
4. Record reviewer ID and an ISO-8601 UTC timestamp. Save and lock the decision before seeing the other reviewer's work or automated evidence.
5. If the rationale is weak or confidence is LOW, select `UNCERTAIN` unless the category is `NOT_COMPARABLE`. Do not guess.

Reviewers should describe visible, distinctive correspondences or differences, not diagnoses. Similarity scores, AI predictions, labels, path conventions, and unverified IDs must not form the rationale. Do not interpret image-processing artifacts as biological evidence.

## Lock, compare, and adjudicate

1. The coordinator validates required fields and freezes both initial submissions as separate records. Never overwrite an original decision or rationale; corrections are append-only, time-stamped superseding entries.
2. Only after both submissions are locked, the coordinator compares categories, confidence, rationales, and limitations. Any category disagreement is escalated, including a category versus `UNCERTAIN` or `NOT_COMPARABLE`. Same-category agreement with LOW confidence or inadequate rationale is also escalated or retained as uncertain.
3. A designated third reviewer/adjudicator examines both original images and both preserved reviews. The adjudicator records identity, UTC time, disagreement type, outcome, and rationale separately. The adjudicator must not erase the independent records.
4. If the evidence does not resolve the relationship, retain `UNCERTAIN` or `NOT_COMPARABLE`. Do not force consensus. If the adjudicator's outcome differs from both initial decisions, preserve all three entries.
5. Keep the enriched queue unchanged. A future, separately authorized workflow may produce a decision ledger linked by pair ID; it must retain source provenance and the full audit trail.

## Disagreement checklist

- `SAME_PHOTO` vs `DISTINCT`: inspect distinctive capture landmarks and whether differences are explainable by a transformation. If unresolved, `UNCERTAIN`.
- `SAME_LESION_DIFFERENT_PHOTO` vs `DISTINCT`: require lesion-specific correspondence across separate captures. General resemblance is not enough. If unresolved, `UNCERTAIN`.
- `SAME_PHOTO` vs `SAME_LESION_DIFFERENT_PHOTO`: resolve same capture versus new capture; if not possible, `UNCERTAIN`.
- Any categorical result vs `UNCERTAIN`: investigate the stated ambiguity; never let a majority vote substitute for evidence.
- Any result vs `NOT_COMPARABLE`: establish whether the image can be accessed. Preserve `NOT_COMPARABLE` if not; never default to `DISTINCT`.

## Quality control and closure

Predeclare a random, blinded repeat sample of at least 10% of completed pairs for a consistency check; also include every disagreement, LOW-confidence case, and incomplete rationale. Record the sampling method/seed, repeat results, and category-specific agreement/disagreement counts. Agreement is not ground truth. Do not use a task pair's AI assessment as the repeat-review answer key.

At closure, verify that every decision has two independent entries or a documented exception, every disagreement has adjudicator disposition or remains unresolved, all records have timestamps and rationale, and the original entries remain intact. Report unresolved cases as unresolved. Relationship review does not authorize label changes, patient identity inference, cohort approval, or train/validation/calibration/test split approval.
