# Task 6B: Task 6A Protocol Review Findings

## Scope

Read-only review of the five Task 6A text files listed below. No Task 6A file was changed. Findings and corrections below are recommendations for a future, explicitly authorized protocol revision; they are not edits or instructions to alter historical decisions.

## Findings and proposed corrections

1. **`UNCERTAIN` versus `NOT_COMPARABLE` needs a sharper operational boundary.** The protocol lists both ambiguous visual evidence and inaccessible/unreadable content, but “otherwise unsuitable” could blur them. Proposed clarification: use `NOT_COMPARABLE` only when a concrete access, integrity, or image-usability problem prevents comparison; if both images can be viewed but the relationship cannot be resolved, use `UNCERTAIN`. Do not infer a relationship from the technical failure.
2. **Confidence for unresolved outcomes is underspecified.** Confidence is described as confidence in the selected decision, but it does not explicitly explain `UNCERTAIN`. Proposed clarification: record confidence in the evidence assessment, not certainty about a hidden relationship; for `UNCERTAIN`, state confidence that the available evidence is insufficient. For `NOT_COMPARABLE`, state confidence that comparison is not possible and record the observable reason.
3. **Metadata exposure after initial review could bias adjudication.** The protocol permits a coordinator to examine source metadata after both initial reviews and says metadata may be considered for same-lesion review. Proposed clarification: keep source, split, identifier, AI, and automated evidence hidden from reviewers and adjudicators until their visual decision is locked. Prefer excluding metadata from the relationship decision entirely; if retained for separate audit context, label it as non-decisional and preserve provenance.
4. **The two-reviewer requirement has a small exception ambiguity.** Most sections require two independent reviews, while `NOT_COMPARABLE` says two reviewers “where feasible.” Proposed clarification: require two reviews for all pairs; where a documented operational exception prevents this, label the record preliminary and do not treat it as independently reviewed or adjudicated.
5. **`DISTINCT` has an appropriately high burden but could be mistaken for pairwise clearance.** Its definition requires support for different lesions, while the split table says only that no link is established for this pair. Proposed clarification: state prominently that `DISTINCT` is pair-specific and never proves patient independence, clears other candidate relations, or approves partitioning.
6. **Adjudication blinding is not as explicit as initial-review blinding.** The protocol explicitly blinds initial reviewers to AI and automated evidence but does not state as directly whether the adjudicator remains blinded. Proposed clarification: keep the adjudicator blinded to AI, similarity scores, automated classifications, and source metadata until a visual adjudication is recorded. Any later evidence review should be a separate, logged step and must not overwrite the visual outcome.
7. **The audit template omits some fields required by the workflow.** It has decisions, confidence, rationale, and timestamps, but no dedicated reviewer limitations columns; its pair identifiers include path fields that should not be exposed in a blinded reviewer form. Proposed clarification: maintain a restricted coordinator mapping separately, add limitations fields to the controlled decision ledger, and ensure the adjudication record preserves original entries verbatim with append-only corrections.
8. **The fixed 10% repeat sample lacks a stated rationale.** A repeat sample can support consistency monitoring, but the percentage is not justified in the protocol. Proposed clarification: select and justify a sampling rate before review based on workload and risk; document the sampling frame and method. Keep all disagreement, LOW-confidence, and incomplete-rationale cases in the quality-control review.
9. **`LOW` confidence and categorical decisions need consistent handling.** The protocol variously says “retain UNCERTAIN,” “escalate,” and “adjudicator review.” Proposed clarification: a LOW-confidence categorical decision is not final; the reviewer should choose `UNCERTAIN` unless the category is `NOT_COMPARABLE`, then escalate where a concrete comparison issue remains. Adjudication must not convert weak evidence into forced certainty.
10. **Correction and finalization states could be more explicit.** Append-only corrections are described, but a ledger schema and versioning rule are not supplied. Proposed clarification: define immutable submission IDs, UTC timestamps, correction reason, superseded-record pointer, and a distinct adjudication entry. Preserve every original decision and rationale.

## Rubric assessment

The five categories are distinct in principle. In particular, `SAME_PHOTO` concerns one photographic capture despite transformations, whereas `SAME_LESION_DIFFERENT_PHOTO` requires separate captures plus lesion-specific correspondence. The `DISTINCT` threshold is stronger than “not a duplicate.” All categories prohibit diagnosis-based, filename-based, hash-based, AI-based, or unverified-identity reasoning.

## Blinding and scope assessment

Initial independent blinding is described clearly: reviewers must not see AI assessments, automated classifications/scores, proposed decisions, other reviews, source evidence, or priority information before locking their own submissions. The recommended improvement is to extend that protection through the visual adjudication. The protocol correctly states that this is not clinical diagnosis, relabeling, patient identification, dataset approval, or split approval. The reviewer interface should continue to omit filenames, paths, labels, and presumed identifiers.

## Inputs inspected (read-only)

- `analysis/nine_class_human_review_queue/HUMAN_REVIEW_PROTOCOL_20261115T124345Z/HUMAN_REVIEW_PROTOCOL.md`
- `analysis/nine_class_human_review_queue/HUMAN_REVIEW_PROTOCOL_20261115T124345Z/DECISION_RUBRIC.csv`
- `analysis/nine_class_human_review_queue/HUMAN_REVIEW_PROTOCOL_20261115T124345Z/REVIEWER_WORKFLOW.md`
- `analysis/nine_class_human_review_queue/HUMAN_REVIEW_PROTOCOL_20261115T124345Z/ADJUDICATION_LOG_TEMPLATE.csv`
- `analysis/nine_class_human_review_queue/HUMAN_REVIEW_PROTOCOL_20261115T124345Z/PROTOCOL_VALIDATION.md`

No queue records, images, contact sheets, source data, or other project files were inspected for this review. No real pair was reviewed, no decision was made, and no reviewer readiness was assessed.
