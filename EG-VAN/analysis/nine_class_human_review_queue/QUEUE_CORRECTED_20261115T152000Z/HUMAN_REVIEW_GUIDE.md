# Human Review Guide

This queue is a traceability artifact only. It is not a clinical review, not an approved dataset, and not a human duplicate adjudication system.

## Decision categories
- SAME_PHOTO: the two images represent the same photographic frame or effectively the same image after cropping, resizing, or compression differences.
- SAME_LESION_DIFFERENT_PHOTO: different photos of the same lesion or an image pair with the same lesion captured at different times or viewpoints.
- DISTINCT: the images do not represent the same lesion or same photo.
- UNCERTAIN: image evidence and metadata do not conclusively resolve the question.
- CANNOT_ASSESS: there is insufficient metadata or evidence to make the judgment.

## Review workflow
- Consider both visual evidence and available metadata, but do not infer patient or lesion independence from filenames, image IDs, or path strings alone.
- Treat AI assessments as evidence, not as human decisions.
- If a patient or lesion ID is missing, record that fact; do not fill in guessed values.
- Keep split assignments separate from duplicate adjudication and do not conflate them.
- Do not diagnose a lesion from the image. This review is for duplicate/leakage review only.

## Why AI evidence is separate
AI assessments are supporting evidence. They are not a substitute for human review, and they are never recorded as a human decision.

## Why patient-level separation matters
If a patient or lesion appears across multiple proposed partitions, the pair may be leakage-relevant even when the images are not identical. Patient-level grouping matters for valid held-out evaluation.

## Missing identifiers
Blank patient or lesion IDs represent missing evidence, not proof of independence.
