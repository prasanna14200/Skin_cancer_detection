# R5E Final Validation

Generated UTC: 2026-11-16T04:04:47.965144+00:00

## Status and source ZIP
- Expected archive: `E:\Cancerdetection\EG-VAN_Backups\R5E_original_images_bundle.zip`
- Expected original-image ZIP found: **FALSE**
- ZIP inventory: 2 archives discovered recursively; none contains the expected R5E image entries or `BUNDLE_VALIDATION.txt`.
- `files.zip` contents: R5E_ALL_20_PAIRS_VISUAL_REVIEW_REPORT.docx, R5E_VISUAL_REVIEW_SUMMARY.csv, R5E_VISUAL_REVIEW_VALIDATION.md, R5E_VISUAL_REVIEW_MANIFEST.sha256
- `files.zip` is a prior-review package, not the original image bundle.
- The separate checkpoint backup ZIP was integrity-tested but contains no R5E source-image entries.
- No archive extraction was performed; ZIPs were not modified.

## CSV and mapping
- Selected-pair rows: 20
- Unique pair IDs: 20
- Original R5 queue rows: 449
- Selected CSV actual columns: 19
- Selected CSV row-width consistency: PASS
- Selected pair ↔ queue path/evidence mapping mismatches: 0
- Differences: none in checked source fields
- `source_b` and `source_split_b` are genuinely empty in both selected CSV and queue. `conflict_flags` matches. `selection_priority` is a selection-side generated field not available in the queue; no delimiter/quote or column-shift error was detected.
- Bundled-vs-original CSV comparison: **NOT POSSIBLE**; no image bundle containing the CSV was found. The existing project R5E CSV was compared to the original R5 queue.

## Image validation
- Original source images fully decoded: 40/40
- Images missing or unreadable: 0
- SHA-256 matches against R5E_IMAGE_VALIDATION.csv: 40/40
- Dimensions/formats: A images 224x224 JPEG; B images 600x450 JPEG (verified per-file in `R5E_IMAGE_VALIDATION_INDEPENDENT.csv`).
- Source path files were used; no ZIP archive-to-image mapping can be asserted.

## Independent image analysis
- Transformation: full-frame B resize 600x450 → 224x224 using Pillow LANCZOS; aspect ratio not preserved.
- Interpolation methods tested: nearest, bilinear, bicubic, Lanczos.
- Translation registration: dense grayscale Pearson search over integer dx,dy in [-3,+3] with valid overlap.
- Similarity measures: grayscale Pearson, Gaussian-window SSIM, global SSIM, MAE and MSE. Exact procedure and limitations are in the registration CSV and DOCX methodology.
- Correlation claim (>=0.9996) under this fixed implementation: 9/20.
- SSIM values: locally windowed values are implementation-specific and are reported in the CSV; global SSIM values are also recorded. The prior approximate SSIM claim is not treated as exact without matching the earlier implementation.
- Independent image-level recommendations: SAME_PHOTO=20, DISTINCT=0, UNCERTAIN=0.
- These are technical recommendations, not human adjudications.

## Human review
- Confirmed user decisions: 1 (PAIR_0001, SAME_PHOTO).
- Pending decisions: 19 (PAIR_0002–PAIR_0020).
- PAIR_0001 evidence is preserved from the user's working-copy CSV; reviewer ID remains blank and the timestamp is corrected to UTC in the new copy.
- The prior working-copy timestamp had a UTC-labeling error: `2026-11-16T08:17:26Z` reflects the displayed +05:30 wall-clock time, not UTC. The source file's actual filesystem write time is `2026-11-16T02:47:28.6227219Z`; that timestamp is used in this new copy. The prior copy is unchanged.
- Reviewer guide options: SAME_PHOTO, DISTINCT_PHOTOS, UNCERTAIN. `DISTINCT` in the summary is mapped to `DISTINCT_PHOTOS` if ever used in the original human template. No human `DISTINCT` decision was entered.
- Human-ledger schema inspected: binary_image_path, candidate_path, candidate_pair_id, source_split, review_batch, candidate_source, candidate_image_identifier, phash_distance, dhash_distance, pixel_mae, pixel_correlation, coarse_correlation, reviewer_decision, reviewer_notes, review_status, review_timestamp_utc, evidence_reference. Genuine ledger rows with `review_status == reviewed` and nonempty `reviewer_decision`: 1; observed decision values: SAME_PHOTO.
- Final working copy uses the original template headers unchanged.

## DOCX structural validation
- Reopened with python-docx: PASS
- ZIP container integrity: PASS
- Pair sections in original order: 20/20; unique: 20/20
- Embedded original images: 40/40
- Pair section count and image count checks: PASS
- Source pixels are embedded from fully decoded originals using in-memory PNG streams; no source image bytes were changed.

## Differences from prior review
- The direct project images were independently decoded and measured. All pairings visually show highly matching image content after the stated full-frame resize.
- Numerical results depend on interpolation and SSIM implementation. This report states its own method rather than copying the previous report's metrics.
- The expected original image ZIP was absent; the existing `files.zip` contains only prior output artifacts.

## Unresolved issues
- The original image bundle ZIP and `BUNDLE_VALIDATION.txt` are absent from the backup directory, so bundled CSV comparison and archive-entry mapping could not be completed.
- The report is based on the 40 original image files at the paths in the selected-pairs CSV, whose hashes match the prior validation ledger.
- Human review is complete only for PAIR_0001; the remaining 19 decisions are pending.
- This package does not approve the research cohort, resolve all provenance/leakage issues, or authorize clinical use.
