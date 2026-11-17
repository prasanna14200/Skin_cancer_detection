# Human Image-Relationship Review Protocol

## Purpose and scope

This protocol defines how two reviewers independently assess whether a pair depicts the same photograph, the same lesion in different photographs, distinct lesions, or a relation that cannot be resolved. It is an image-relationship and dataset-leakage review only. It is not a clinical diagnosis, source-label review, dataset approval, patient-identity determination, or split-approval procedure.

The read-only input is the 1,258-row enriched queue. Its `review_item_id` and `canonical_pair_id` identify queue records; `canonical_path_a` and `canonical_path_b` locate the two files. Queue paths are sorted for stable identity and do not record which path was first in the original evidence. Source/split metadata is partial. `image_id_*` and `patient_id_*` are blank throughout; `lesion_id_b` is populated for 83 rows, and other metadata fields are populated only for some rows. Missing identifiers are not evidence of independence.

No human decisions are present in the queue: `human_decision` is blank and `review_status` is `UNREVIEWED` for all rows. Automated and AI fields (`ai_assessments`, `priority_categories`, `priority_reason`, similarity/evidence references) are analyst evidence, not ground truth. They must be withheld during each initial independent review.

## Decision categories

Use exactly one category per reviewer per pair. Do not add a diagnosis or change either image's label.

### SAME_PHOTO

The files show the same original photographic capture, including versions altered by resizing, compression, rotation, color processing, or cropping.

Minimum evidence: distinctive visual correspondence that is specific to the capture, such as a matching combination of lesion-internal structures and spatially consistent surrounding skin, hair, ruler, artifact, or other landmarks. A crop may remove context, but the remaining visible features must still support the same capture. The reviewer must explain which landmarks correspond and why the differences are consistent with image transformation rather than a new capture.

Misleading evidence includes similar lesion shape, color, diagnosis, broad texture, or a matching filename/hash/similarity score without visual correspondence. If a separate capture cannot be ruled out, use UNCERTAIN.

Record the decision, confidence, a concise visual rationale, limitations, and any visible crop/quality issue. Two independent reviews are mandatory. If they disagree, an adjudicator is mandatory. If either initial reviewer has LOW confidence or the evidence is not distinctive, do not finalize SAME_PHOTO; retain UNCERTAIN or escalate for adjudication.

### SAME_LESION_DIFFERENT_PHOTO

The files show the same physical lesion in separate photographic captures. They are not merely resized, recompressed, rotated, recolored, or cropped versions of one capture.

Minimum evidence: convincing lesion-specific correspondence across separate captures, including distinctive internal structures, border details, or stable lesion-specific features, with enough visual evidence to distinguish a new capture from a transformed copy. Metadata may be considered only after independent decisions are locked, and only as explicitly recorded source evidence. It cannot replace visual support or establish cross-source identity by itself.

Misleading evidence includes matching diagnosis or lesion-type labels, color, general morphology, body region, a source lesion ID without a verified identity bridge, or a different crop that could still be the same photograph. If same-photo versus separate-capture is unresolved, use UNCERTAIN.

Record the decision, confidence, lesion-specific visual rationale, evidence that the captures differ, and limitations. Two independent reviews are mandatory. Any disagreement or LOW-confidence positive decision requires adjudicator review; do not force a same-lesion conclusion.

### DISTINCT

The images are sufficiently supported as different photographs of different lesions. This is stronger than observing that the files differ or show different views.

Minimum evidence: visible, lesion-specific differences that cannot reasonably be explained by crop, orientation, lighting, scale, compression, or image quality, with enough context to support that the lesions are different. The rationale must identify the relevant visual evidence and explain why same-lesion identity is not supported.

Misleading evidence includes different framing, lighting, orientation, scale, color, image quality, or photographic processing; absent matching metadata; different filenames; or a failed automated match. These do not alone establish different lesions.

Record the decision, confidence, the distinguishing visual evidence, and limitations. Two independent reviews are mandatory. Any disagreement, weak rationale, or LOW confidence requires UNCERTAIN or adjudicator review.

### UNCERTAIN

The available evidence does not support a reliable relationship decision. Use this when landmarks are ambiguous, cropping or quality removes necessary evidence, evidence conflicts, or same-photo and same-lesion alternatives cannot be distinguished.

Minimum evidence: identify what is ambiguous or missing and which plausible alternatives remain. Do not use UNCERTAIN as a substitute for an unrecorded review.

Misleading evidence includes choosing the most likely category because an AI result, similarity score, source label, or majority preference suggests it.

Record the uncertainty reason, confidence, and any limits on the visible evidence. Two independent reviews are mandatory. If both reviewers agree on UNCERTAIN, preserve UNCERTAIN; it remains unresolved for split approval. If they disagree, an adjudicator reviews the disagreement but must not force a categorical decision.

### NOT_COMPARABLE

At least one image is missing, unreadable, corrupted, inaccessible, or otherwise unsuitable for a meaningful comparison.

Minimum evidence: state which image is unusable and the observable access or quality problem. Do not diagnose the image or infer why it is unavailable.

Misleading evidence includes treating a missing image, decode failure, or poor rendering as evidence that the pair is DISTINCT.

Record the affected side, the concrete reason, confidence that comparison is not possible, and any attempted non-destructive access check. Two independent reviewers are required where feasible. Disagreement requires adjudicator review. Preserve NOT_COMPARABLE if the limitation cannot be resolved; do not silently convert it to UNCERTAIN or DISTINCT.

## Confidence and rationale

Each reviewer records confidence in their selected decision:

- **HIGH**: distinctive, directly visible evidence strongly supports the selected category.
- **MODERATE**: evidence supports the category but has stated limitations.
- **LOW**: evidence is weak or ambiguous; ordinarily select UNCERTAIN instead of a categorical relation.

For NOT_COMPARABLE, confidence describes confidence that the comparison is unusable, and the reason is mandatory. The rationale must be concise and specific to visible evidence: for example, corresponding lesion-internal structures, border patterns, surrounding skin landmarks, or consistent spatial relationships. Record limitations separately when useful.

Rationales must not rely solely on diagnosis labels, broad color or morphology, filenames, directory names, hashes, automated similarity scores, AI conclusions, or unverified patient/lesion identifiers. Do not use a medical diagnosis as a review outcome.

## Independence and blinding

Two reviewers independently examine each assigned pair and submit their decision, confidence, rationale, limitations, and UTC timestamp before seeing the other reviewer's entry. The coordinator must keep the following hidden until both initial decisions are locked:

- AI assessments and prior AI opinions;
- automated duplicate/similarity categories, scores, overlays, and proposed decisions;
- other reviewers' decisions and rationales;
- source evidence references and analyst priority reasons.

The initial reviewer view should use neutral pair IDs and neutral Image A/Image B labels. It should not expose source/split fields, lesion identifiers, candidate IDs, or filenames. A coordinator-controlled mapping may be used only to retrieve the correct original files. Do not let path conventions or metadata function as identity evidence. After both reviews are locked, the coordinator may examine explicitly recorded source metadata as separate corroborating context and must preserve its provenance and missingness; metadata alone cannot decide a visual relationship.

Blinding reduces confirmation bias and prevents automated predictions from being copied into human labels. The enriched CSV is not a reviewer-facing form because it includes AI and priority fields. No reviewer export or review batch is created by this protocol task.

## Operational workflow

1. **Prepare reviewers.** Assign distinct, accountable reviewer identities. Explain the categories, confidence scale, rationale rules, and prohibition on diagnosis. Use a small calibration exercise separate from the 1,258 queue pairs, with independently established examples if such examples are available. Calibration aligns terminology only; it does not change this queue or establish performance. If no suitable examples exist, document that limitation rather than presenting AI-labeled queue items as practice ground truth.
2. **Assign neutral pair IDs.** A coordinator maintains a restricted mapping from pair ID to the two original files. Both reviewers receive the same pair inventory with randomized order and neutral side labels. Do not expose AI fields, scores, source paths, metadata, or one another's decisions.
3. **Compare original files independently.** Use the original available images at a suitable viewing scale, preserving aspect ratio. Inspect native files where needed. Do not use image enhancement, registration, overlays, or other processing as a substitute for originals. Do not interpret compression, resizing, color processing, or display artifacts as biological evidence.
4. **Record each independent decision.** For every pair, record exactly one category, confidence, a concise visual rationale, limitations, reviewer ID, and ISO-8601 UTC submission time. No decision is preselected. If an image cannot be compared, select NOT_COMPARABLE and state why.
5. **Lock both reviews.** The coordinator verifies required fields and freezes each submission as a separate append-only record before revealing either review or any automated evidence. Corrections are new versioned entries; never overwrite the first decision.
6. **Detect disagreements.** Compare the two locked decisions only after both are complete. Treat any category disagreement as a disagreement, including a categorical decision versus UNCERTAIN or NOT_COMPARABLE. Also flag same-category agreement if either confidence is LOW or a rationale is insufficient.
7. **Adjudicate separately.** A designated third reviewer/adjudicator sees both preserved reviews and may inspect the original files. The adjudicator records an outcome and reason in a separate log. The adjudicator does not erase or rewrite either original decision. If evidence remains insufficient, record UNCERTAIN or NOT_COMPARABLE.
8. **Record the audit trail.** Retain pair ID, reviewer identities, both initial decisions, confidences, rationales, limitations and timestamps; any disagreement type; adjudicator identity, decision, rationale and timestamp; and audit notes. Keep the queue unchanged. Use a new, controlled decision ledger if a later task explicitly authorizes one.
9. **Quality control.** Predeclare a random repeat sample of at least 10% of completed pairs for a blinded consistency check by a reviewer who cannot see the earlier decisions. Also review all disagreements, LOW-confidence cases, and cases with incomplete rationale. Record sample selection method/seed and report agreement and category-specific disagreement counts without treating agreement as ground truth. Correct terminology drift through a documented protocol update, not by rewriting past decisions.

## Disagreement and adjudication

The adjudicator must examine both original files and preserve each initial decision and rationale verbatim.

- **SAME_PHOTO vs DISTINCT:** determine whether distinctive capture-specific landmarks support the same photograph or whether sufficient lesion-specific evidence supports different lesions. If neither is compelling, retain UNCERTAIN.
- **SAME_LESION_DIFFERENT_PHOTO vs DISTINCT:** evaluate lesion-specific correspondences and evidence of separate captures. General resemblance is insufficient. If identity cannot be distinguished, retain UNCERTAIN.
- **SAME_PHOTO vs SAME_LESION_DIFFERENT_PHOTO:** decide whether differences are transformations of one capture or evidence of separate captures of the same lesion. If that distinction is unresolved, retain UNCERTAIN.
- **Any categorical decision vs UNCERTAIN:** review the stated ambiguity and the visible evidence. Do not treat the categorical vote as a tie-breaker. If evidence remains insufficient, retain UNCERTAIN.
- **Any decision vs NOT_COMPARABLE:** establish whether the image can actually be accessed and compared. If it cannot, preserve NOT_COMPARABLE; if it can but relationship evidence remains weak, use UNCERTAIN. Never use DISTINCT as a fallback for unavailable data.
- **Two categorical decisions agree:** agreement is not a substitute for the evidence requirement. LOW confidence, contradictory rationale, or unresolved limitations must be escalated or retained as UNCERTAIN.

The adjudication record includes the disagreement type, both independent decisions, reviewer rationales, adjudicator identity, date/time, final outcome, and reason. If adjudication cannot resolve the case, preserve the unresolved category. No forced consensus is allowed.

## Dataset and split implications

| Decision | Relationship implication for leakage control |
| --- | --- |
| SAME_PHOTO | Treat the records as one photographic identity and keep them linked for leakage prevention. This decision does not authorize relabeling or an exclusion. |
| SAME_LESION_DIFFERENT_PHOTO | Keep the records linked as the same lesion for split-grouping purposes. This does not establish patient identity. |
| DISTINCT | This review establishes no duplicate-photo or same-lesion link for this pair only. It does not prove patient independence or clear other candidate relations. |
| UNCERTAIN | Quarantine from final split approval until resolved. Do not separate across partitions while unresolved. |
| NOT_COMPARABLE | Quarantine from final split approval until resolved, or separately exclude only with documented and authorized justification. |

A relationship decision does not authorize label changes, merge source-defined labels, establish a clinical diagnosis, or establish patient identity. Patient-level separation requires reliable patient identifiers and an appropriate grouping source. This protocol cannot manufacture either. Source identity, licensing, cohort eligibility, label compatibility, and dataset approval remain separate blockers. Do not approve or construct train, validation, calibration, or test splits under this protocol.

## Schema and historical terminology

The current queue has `human_decision` and `review_status`; decisions are blank and statuses are `UNREVIEWED`. The queue does not contain reviewer identity, confidence, rationale, or adjudication columns. Record future reviews in a separate, controlled ledger if separately authorized; do not alter this queue.

Earlier project guides use terms such as `SAME_LESION`, `DISTINCT_PHOTO`, or `CANNOT_ASSESS`. This protocol uses the requested explicit `SAME_LESION_DIFFERENT_PHOTO`, `DISTINCT`, and `NOT_COMPARABLE` categories. Do not silently translate historical records. Preserve each prior value verbatim with its original schema and provenance.
