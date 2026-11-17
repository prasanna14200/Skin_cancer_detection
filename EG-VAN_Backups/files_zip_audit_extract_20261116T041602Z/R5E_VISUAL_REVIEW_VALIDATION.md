# R5E Visual Review - Validation Report

Generated (UTC): 20261116T033949Z
Status: **PRELIMINARY.** AI-assisted advisory recommendations only. Not a completed human duplicate audit. Does not approve the nine-class research cohort or claim leakage resolution.

## Counts

| Item | Result |
|---|---|
| Selected pairs | 20 |
| Unique pair IDs | 20 |
| Original images | 40 (20 A, 20 B) |
| Images successfully decoded (full pixel decode) | 40 |
| Missing or unreadable images | 0 |
| Images whose SHA-256 and dimensions match R5E_IMAGE_VALIDATION.csv | 40 / 40 |
| Completed AI-assisted visual assessments | 20 |
| SAME_PHOTO recommendations | 20 |
| DISTINCT recommendations | 0 |
| UNCERTAIN recommendations | 0 |
| Confirmed human decisions | 1 (PAIR_0001, supplied by the user) |
| Pending human decisions | 19 |

## PAIR_0001 preservation
- Human decision `SAME_PHOTO` with status `CONFIRMED_BY_USER` is recorded in the summary CSV: **PRESERVED CORRECTLY**.
- The AI recommendation for PAIR_0001 (SAME_PHOTO, HIGH) is stored separately in `ai_recommendation` and was not used to fill the human decision.
- reviewer_id and review_timestamp_utc were not supplied and are not invented. The PAIR_0001 working-copy CSV and the original decision template were not provided, so the decision was taken from the user's written statement.
- PAIR_0002 to PAIR_0020: human_decision blank, status PENDING_HUMAN_REVIEW: **CORRECT**.

## DOCX structural validation
| Check | Result |
|---|---|
| ZIP container integrity | OK |
| Reopened with python-docx | OK |
| OOXML schema validation (skill validator) | PASSED |
| Converted to PDF by LibreOffice | OK, 25 pages |
| 20 pair sections, PAIR_0001 to PAIR_0020, in original order, each once | YES |
| Embedded images | 40 (expected 40) |
| Every pair section has exactly 2 images | YES |
| Every pair section has recommendation, confidence, evidence, evidence against, limitations, human decision status | YES |
| Methodology, summary table, pending-review list present | YES |
| Overall | **PASSED** |

## Method summary
1. ZIP extracted to a temporary directory; originals untouched. CSV headers read from the file; image_a_id and image_b_id hold the original relative paths; each matched to exactly one archive entry.
2. All 40 images decoded; dimensions: every A is 224x224, every B is 600x450 (JPEG).
3. Each pair was viewed side by side and compared on lesion shape, pigment, landmarks, specks, vessels, hairs, bubbles, tick marks and background texture.
4. Supplementary computational cross-check (not a substitute for the visual review): B resized to 224x224 over its full frame was compared with A (NCC and SSIM), with a negative control against every other pair's B.

## Supplementary cross-check results
All 20 pairs: A equals B resized full-frame to a square (aspect ratio not preserved); no crop needed.

| Pair | NCC | SSIM | Mean abs diff | Best NCC vs other pairs' B |
|---|---|---|---|---|
| PAIR_0001 | 0.9998 | 0.9983 | 0.64 | 0.43 |
| PAIR_0002 | 0.9998 | 0.9983 | 0.58 | 0.57 |
| PAIR_0003 | 0.9997 | 0.9982 | 0.55 | 0.65 |
| PAIR_0004 | 0.9998 | 0.9983 | 0.51 | 0.49 |
| PAIR_0005 | 0.9996 | 0.9984 | 0.42 | 0.29 |
| PAIR_0006 | 0.9997 | 0.9983 | 0.62 | 0.32 |
| PAIR_0007 | 0.9997 | 0.9983 | 0.65 | 0.52 |
| PAIR_0008 | 0.9998 | 0.9981 | 0.54 | 0.54 |
| PAIR_0009 | 0.9996 | 0.9982 | 0.5 | 0.32 |
| PAIR_0010 | 0.9996 | 0.9983 | 0.49 | 0.52 |
| PAIR_0011 | 0.9998 | 0.9983 | 0.72 | 0.57 |
| PAIR_0012 | 0.9997 | 0.9980 | 0.48 | 0.59 |
| PAIR_0013 | 0.9998 | 0.9981 | 0.53 | 0.72 |
| PAIR_0014 | 0.9999 | 0.9984 | 1.03 | 0.40 |
| PAIR_0015 | 0.9998 | 0.9981 | 0.5 | 0.65 |
| PAIR_0016 | 0.9997 | 0.9983 | 1.13 | 0.49 |
| PAIR_0017 | 0.9998 | 0.9982 | 0.61 | 0.74 |
| PAIR_0018 | 0.9997 | 0.9980 | 0.56 | 0.74 |
| PAIR_0019 | 0.9997 | 0.9981 | 0.99 | 0.34 |
| PAIR_0020 | 0.9997 | 0.9982 | 0.51 | 0.55 |

## Terminology
Reviewer instructions use `DISTINCT_PHOTOS`; this task uses `DISTINCT`. Mapping: SAME_PHOTO = SAME_PHOTO, DISTINCT = DISTINCT_PHOTOS, UNCERTAIN = UNCERTAIN. The original decision template was not supplied, so its allowed values were not inspected or changed. No DISTINCT recommendation was issued.

## Unresolved issues and caveats
- The review is AI visual inspection of rendered comparisons; the human reviewer must confirm every pair.
- PAIR_0001 agreement is one consistency check (its landmarks were supplied in advance) and does not validate the method.
- A being a resized copy of B shows a shared photograph, not which file is the source; implications for splits and leakage are not assessed.
- R5E_SELECTED_PAIRS.csv has blank or apparently misaligned columns (source_b, source_split_b, conflict_flags, selection_priority); they were not used and should be checked against the original on the E: drive.
- The Windows paths (E: drive, Desktop) were not accessible; this run used the uploaded ZIP and CSV. Output directory is in the sandbox outputs folder.
- The SHA-256 manifest is generated after this file is final, so its verification result is reported separately (separate sha256sum -c command), not inside this file.
- No original image, CSV, queue, template or earlier audit package was modified. No model was trained and no inference was run.
