# R5E Human Review Workflow

This package is a local, human-operated interface for the 20 R5E pairs. It preserves the original CSV schema and does not change the R5 queue, images, original template, reviewer guide, or prior audit packages.

## Start
Open `R5E_REVIEW_INTERFACE.html` in a browser. It displays one pair at a time with the original images side by side. If the browser blocks local images, open the HTML from the EG-VAN project on this machine; image paths are relative references to the original files.

## Human decision entry
- Exact human decision labels from `R5E_REVIEWER_INSTRUCTIONS.md`: `SAME_PHOTO, DISTINCT_PHOTOS, UNCERTAIN`.
- The original template has no validation-list/enum metadata; the reviewer guide supplies the allowed values. No label mismatch was found.
- PAIR_0001 remains `SAME_PHOTO`, confirmed by the user, and read-only in the interface.
- PAIR_0002–PAIR_0020 begin blank and are not preselected from AI recommendations.
- `reviewer_id` remains blank unless the reviewer enters it.
- The browser creates a UTC timestamp only after a human selects an allowed decision and explicitly clicks “Save this human decision.”
- Saving stores that human-entered record only in the current browser tab. Click “Download decision CSV” to explicitly export. There is no server, network submission, local-storage autosave, or automatic AI-to-human transfer.
- The exported CSV uses the exact original template headers. AI recommendations/evidence are shown separately in the interface and are not CSV decision fields.

## Evidence checked
- Previous final-package manifest entries rehashed successfully: 7; mismatches/missing/unlisted files: 0.
- Previous DOCX reopened successfully with 20 pair sections in order and 40 images.
- Original R5E selected-pair CSV rows: 20; unique pair IDs: 20.
- Selected pair image paths match their corresponding R5 queue rows: 0 mismatches.
- Original images decoded: 40/40; SHA-256 values match the original R5E image-validation CSV: 40/40.
- Existing human-review ledger genuine decisions: 1 (reviewed status plus non-empty reviewer decision).
- Known reviewed PAIR_0001 ledger record: SAME_PHOTO at 2026-10-19T12:25:44+00:00; this is separate evidence from the user confirmation in the R5E working copy.

## Scope limitation
The previously reported original-image ZIP was not found. The workflow uses the original image files already present under their selected-pair paths in the project; no archive-entry validation is claimed. This package does not adjudicate pairs, update the source ledger, approve the dataset/cohort, or run model work.
