# R5E Reviewer Instructions

## Goal
Review the first 20 unresolved duplicate pairs in the package without modifying any original source, queue, or split data.

## Decision options
- `SAME_PHOTO`: same underlying photograph, including resized, compressed, or color-adjusted versions of the same capture.
- `DISTINCT_PHOTOS`: different photographs, even when the same lesion or subject is visible.
- `UNCERTAIN`: the evidence is suggestive but not decisive enough for an authoritative conclusion.

## Evidence reviewers may use
- Original image paths and split labels from the queue.
- Available source metadata and review evidence already recorded in the research package.
- Image files themselves, using the visual review pages created for this batch.
- Existing AI assessment and confidence fields, but not as ground truth.

## What reviewers must not do
- Do not fabricate a decision.
- Do not treat AI output as authoritative.
- Do not merge, delete, relabel, or rewrite the original source records.
- Do not infer patient identity from visual appearance.
- Do not reorder the batch or silently skip a selected pair.

## Recording rationale
Use brief evidence-based rationale notes. Keep them factual and non-identifying. If the same photograph and same lesion distinction is unclear, select `UNCERTAIN`.
