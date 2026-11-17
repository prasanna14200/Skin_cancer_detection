# IQA package validation

Status: **EXPLORATORY / NON-CLINICAL**.

## Checks performed during generation

- Existing frozen-run verifier confirmed the expected run metadata, config SHA-256, split SHA-256, preprocessing fingerprint, source-preview SHA-256, and checkpoint SHA-256.
- All 1,028 saved prediction keys matched the 1,028 frozen validation records exactly; no duplicate key or unmatched row.
- Saved true labels matched split labels; all probability vectors were finite, nonnegative, summed to one within tolerance, and their argmax matched the recorded class. Recomputed accuracy matched the saved validation metrics.
- All source images existed, decoded successfully, and their SHA-256 matched split records before and after measuring; no source image was modified.
- 1,028 unique image-key rows and 14 finite features per row; 0 missing features; all processing statuses `OK`.
- 944 source image IDs were present and matched their filename stems; 84 Fanconic source IDs were absent in the source split and remain explicitly blank.
- No exact-byte duplicate image hashes appeared in the validation set. 192 overlap-group IDs repeat across 429 rows; this is reported as an independence/leakage limitation.
- No inference or training was run. No source, split, checkpoint, or prior package was modified.

## Independent revalidation

A separate CPython 3.13 process independently verified all 15 manifest entries against all 15 non-manifest output files and rehashed all 9 source-evidence files. It also checked the linked table against the saved predictions and frozen split, recalculated class counts and the 628/400 correctness totals, and independently recomputed SHA-256 for all 1,028 source images. All checks passed; no missing feature values were found, and the recomputed accuracy was 0.6108949416342413.

The manifest lists every package file except the manifest itself; the manifest is self-excluded to avoid a recursive hash.
