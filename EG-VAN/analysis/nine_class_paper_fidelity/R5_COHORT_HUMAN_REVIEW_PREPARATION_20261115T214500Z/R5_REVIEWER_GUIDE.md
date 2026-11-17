# Reviewer Guide for Human Cohort Adjudication

## Purpose
This package prepares the project for human review of unresolved duplicate and source-test conflict records. It does not approve any cohort, split, or training run.

## Review categories
- SAME_PHOTO: the two records are the same image or a near-identical pixel-equivalent capture.
- DISTINCT_PHOTO: the records are different photographs.
- SAME_LESION_DIFFERENT_PHOTO: the images are different photos of the same lesion or lesion region.
- UNCERTAIN: the evidence is suggestive but not decisive enough for an authoritative conclusion.
- INSUFFICIENT_EVIDENCE: the record does not contain enough metadata, source evidence, or image framing to judge confidently.

## Evidence reviewers may use
- Original source paths and source split labels.
- File hashes and image dimensions.
- Duplicate-pair metrics already recorded in the review files.
- Existing AI assessment fields and decision methods.
- The original source metadata kept in the evidence package; do not infer patient identity from appearance.

## What reviewers must not do
- Do not treat AI scores as ground truth.
- Do not merge or delete records automatically.
- Do not infer patient or lesion identity from visual appearance.
- Do not change the original data, manifests, splits or frozen source records.
- Do not manufacture a decision when evidence is absent.

## When to choose UNCERTAIN or INSUFFICIENT_EVIDENCE
Select UNCERTAIN when the records are probably related but not proved. Select INSUFFICIENT_EVIDENCE when there is not enough metadata or direct evidence to support a confident decision. These options are allowed and should be used when the evidence cannot support certainty.

## Recording rationale
Each reviewer should provide a short rationale using evidence already present in the queue: source labels, image hashes, metrics, source split membership, and the reason the evidence is or is not sufficient. Do not include patient-identifying details or unneeded image content in the notes.

## Escalation
If a record remains ambiguous after the review queue, escalate it to the provenance-review lane or to a second reviewer rather than forcing a decision. Do not silently discard unresolved rows.
