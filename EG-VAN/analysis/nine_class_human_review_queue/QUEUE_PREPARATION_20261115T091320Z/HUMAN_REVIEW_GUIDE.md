# Human duplicate-review guide

This file is a review-preparation artifact only. It does not approve the dataset, split, or cohort. It is not a medical diagnosis or clinical decision aid.

## Decision categories
- SAME_PHOTO
- SAME_LESION_DIFFERENT_PHOTO
- DISTINCT
- UNCERTAIN
- CANNOT_ASSESS

## Review expectations
- Use available metadata only when explicitly present in the evidence tables.
- Do not infer same-lesion relationships from filenames alone.
- Do not turn AI labels into human decisions.
- Record uncertainty separately from the AI assessment.
- Patient and lesion IDs are review metadata, not proof of independence when missing.

## Why AI results are not human decisions
AI outputs are evidence artifacts. They can suggest likely overlap or uncertainty, but they are not human adjudications and must remain separate from the human-review record.

## Why patient-level separation matters
Pair records may appear harmless by file name alone, but patient-level or lesion-level duplication can leak across train, validation, calibration, and test sets. Missing patient or lesion IDs cannot be treated as proof of independence.

## What to record
- A human decision only after actual review.
- Review notes describing the evidence used.
- Uncertainty or inability to assess when metadata is incomplete.
