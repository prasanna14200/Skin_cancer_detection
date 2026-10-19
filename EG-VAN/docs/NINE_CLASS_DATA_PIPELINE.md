# Nine-class data pipeline: current input audit

Audit date: 2026-10-19. Project root: `E:/Cancerdetection/EG-VAN`.

## Decision

**STOP: a defensible nine-class split cannot be generated from the present sources.** The 2026-10-19 perceptual audit found extensive content overlap between the canonical binary collection and HAM10000, including the binary source test partition. The same photograph would carry different nine-class targets (for example, HAM `nv` versus binary `BENIGN`). This is a target conflict and a direct leakage risk, not merely uncertainty about provenance. No combined manifest, preprocessing, or split was created. The earlier structural-match assessment below remains valid for source identification, but its conclusion that this combination was feasible is superseded by the overlap evidence.

## Current sources and counts

| Source | Local structure | Verified result |
| --- | --- | --- |
| HAM10000 | `data/raw/HAM10000_metadata.csv`; `HAM10000_images_part_1/` and `_part_2/` | 10,015 metadata rows and matching original JPGs (5,000 + 5,015); 10,015 unique image IDs, 7,470 nonblank unique lesion IDs. No patient ID column. |
| Current binary collection | `data/isic/data/{train,test}/{benign,malignant}/` | 3,297 labeled JPG entries: 1,800 benign and 1,497 malignant by directory. |
| Byte-identical mirror | `data/isic/{train,test}/{benign,malignant}/` | Another 3,297 JPG files, byte-for-byte copies of the corresponding `data/isic/data/` entries. Never count as additional cases. |

HAM metadata columns: `lesion_id,image_id,dx,dx_type,age,sex,localization`. Verified diagnosis counts: AKIEC 327, BCC 514, BKL 1,099, DF 115, MEL 1,113, NV 6,705, VASC 142. The metadata stores lower-case `dx` values. All metadata image paths exist. The existing `data/raw/images/` and `data/processed/images/` are additional HAM copies or derivatives, not new cases. The processed directory has 10,015 JPGs, and its log records 10,015 successes, though logged `D:` paths are stale here.

| Binary branch | Benign | Malignant | Total |
| --- | ---: | ---: | ---: |
| Canonical train | 1,440 | 1,197 | 2,637 |
| Canonical test | 360 | 300 | 660 |
| **Canonical total** | **1,800** | **1,497** | **3,297** |

All 3,297 canonical files decode as 224 × 224 RGB JPEGs. Their uniform dimensions suggest earlier resizing, but the preprocessing history and originals cannot be verified. There is no metadata CSV or other label file, no patient or lesion identifiers, and no source/version record. Numeric filenames repeat across classes, so a future manifest would need folder-qualified row keys.

## Version and provenance

The current folder is **not the previously audited ISIC 2017 Task 3 directory** of 2,750 images labeled melanoma, seborrheic keratosis, and other. Its former Task 3 paths and CSVs are absent. The current 3,297-entry layout is a **strong structural match** to the [Fanconi Kaggle dataset](https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign/metadata). The publisher calls it processed ISIC Archive pictures. A [published study explicitly linking that collection](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0269826) reports 3,297 images, 1,800 benign and 1,497 malignant, RGB, 224 × 224, in train and test folders. These are structural comparisons, **not a version-locked byte match**. No local package manifest, download receipt, Kaggle version number, official per-file checksums, original ISIC IDs, or image-level label table establishes exact identity or label derivation. No dataset was downloaded for this audit.

## Duplicate and overlap audit

SHA-256 of all 6,594 binary JPG files yields 3,296 unique byte contents. Each canonical entry has an identical mirror. Within the canonical copy, `data/isic/data/train/malignant/768.jpg` and `769.jpg` are byte-identical. Thus the 3,297 canonical entries contain 1,800 unique benign and 1,496 unique malignant byte contents. No hash carries conflicting folder labels. The duplicate pair is in the current train branch.

HAM's 10,015 original JPGs have 10,013 unique byte hashes. Cross-source SHA-256 comparison found **zero byte-identical HAM/binary images**; image ID stems also do not overlap. This does not rule out recompressed or visually similar images, shared lesions, or shared patients. Perceptual and clinical overlap remain unaudited.

## Label mapping and preprocessing

Proposed mapping only: `AKIEC=0, BCC=1, BKL=2, DF=3, MEL=4, NV=5, VASC=6, BENIGN=7, MALIGNANT=8`. It has **not been finalized against the EG-VAN paper**. HAM labels are diagnoses, whereas the two binary folder labels are broad outcomes. Do not infer either broad class from ISIC 2017 Task 3 `other`. A future nine-class model also risks learning source differences.

`src/preprocessing.py` implements deterministic hair removal (17-pixel elliptical blackhat kernel, threshold 10, Telea radius 1), Gray World, then multiscale Retinex (sigmas 15/80/250, equal weights, 1st/99th-percentile scaling). These numerical values are local choices, not verified paper parameters. `src/dataset.py` converts HAM images to RGB. Existing training code uses 384 × 384 resizing, pretrained-weight normalization, random flips and rotation for training, and deterministic evaluation transforms. Paper-exact numerical settings and model size were not verified. Applying these operations again to the current 224 × 224 files requires source history and a frozen policy.

No combined preprocessing was run. In a later adapted pipeline, keep raw images unchanged, report decode failures, apply identical deterministic per-image transforms to both sources, avoid unnecessary output copies, fit any shared statistics on train only, and augment training images only after splitting.

## Split and validation status

No combined train/validation/test manifests exist. The proposed 80/10/10 ratio with seed 42 is an adaptation, not a verified paper protocol. The binary `train` and `test` directories have unknown assignment methods and no validation directory. Patient/lesion independence cannot be established without identifiers. A future split must group verified related images and duplicates, stratify where feasible, examine perceptual cross-source matches, and reserve the test set for final evaluation. Existing HAM-only split files were not changed.

Completed checks: HAM metadata and source image counts; binary folder counts; decoding of all 3,297 canonical files; complete byte equality of the mirror; exact duplicate and cross-source hash audit. Combined nine-class class, path, group, split, transform, and leakage checks remain inapplicable. Combined train, validation, and test counts are unavailable.

## Focused verification: names, label conflicts, and the internal duplicate

There are 1,800 distinct numeric basenames in the canonical tree. Exactly 1,497 basenames occur in both classes; 474 occur in both existing partitions. A basename is **not** an image identifier. Use a source-qualified, project-relative path as an entry key, retain the original numeric stem as an unverified source filename, and never invent an ISIC ID. SHA-256 shows zero cross-class content conflicts and zero exact content groups crossing the current train/test directories.

`data/isic/data/train/malignant/768.jpg` and `769.jpg` are each 49,584 bytes with SHA-256 `19a74bc9c33324990897b3195d50de40b276e100a31c5262660725c106db664a`. They decode as the same 224 × 224 RGB picture, and direct visual inspection also shows the same image. The files contain identical camera EXIF data; this does not reveal a patient ID or establish diagnosis. Both raw files remain in place.

**Canonical tree:** use `data/isic/data/` for all future binary records because it is one complete train/test hierarchy. Treat `data/isic/{train,test}/` as a verified byte-identical mirror and exclude it from entry enumeration; retain it untouched. This is a logical choice, not a provenance claim.

**Deterministic exact-duplicate policy:** compute SHA-256 from each canonical file before splitting. Group equal hashes across all sources and partitions. For the known malignant pair, assign both entries the same content-based duplicate group. Prefer one representative per exact-content group for model sampling, chosen by lexicographically smallest normalized project-relative path; retain excluded entry paths and hashes in an audit table. For `768.jpg`/`769.jpg`, this selects `768.jpg` and excludes `769.jpg` from sampling. Preserve both raw files. If an experiment intentionally retains both entries, the whole group must remain in one split and be counted as one independent content unit. Any cross-label group is quarantined for review rather than assigned a target. Recompute the audit after any source change. This avoids counting mirror paths or identical content as independent observations.

**Near-duplicate search run:** `src/nine_class_similarity_audit.py` decodes all 10,015 HAM originals and 3,297 canonical binary entries, computes 64-bit pHash and dHash, and emits pairs where either Hamming distance is at most 6. The threshold creates candidates, not automatic match decisions. Further image-embedding/local-feature search could find more cropped or altered matches; it is unnecessary to establish the current blocker. A zero exact SHA-256 overlap did **not** imply no visual overlap.

## Provenance, licensing, and decision

The Fanconi source description and linked research make the binary folder labels **reasonably attributable to a published processed collection at collection level**, but there is no local image-level clinical validation or version proof. The current tree has no README, archive, metadata CSV, license text, source receipt, original ISIC IDs, patient IDs, or lesion IDs. The [published study](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0269826) says image rights remain with the underlying ISIC Archive; this does not identify the license of each local file. Verify source-specific terms before redistribution. The 224 × 224 files appear processed, but their processing history cannot be reconstructed from local evidence.

The current binary collection cannot simply be appended to HAM10000 as two new mutually exclusive classes. A scientifically defensible alternative requires a revised target definition or a verified, nonoverlapping additional source. That change is outside this task and needs an explicit protocol decision. The scientific report must not claim exact EG-VAN reproduction, image independence, or patient independence. **Ready for EG-VAN construction: NO.**

## 2026-10-19 overlap audit and stop gate

The published [EG-VAN paper](https://www.researchgate.net/publication/390831641_EG-VAN_A_Global_and_Local_Attention_based_Dual-Branch_Ensemble_Network_with_Advanced_color_balancing_for_Multi-Class_Skin_Cancer_Recognition) describes seven HAM diagnoses plus a binary malignant/benign collection, and reports 1,332 original test images followed by augmented train and validation counts. It does not publish image assignments or a patient/lesion-aware split. Its table lists nine class names but does not establish numeric encoding. If a new protocol is approved later, use an explicitly adapted mapping `AKIEC=0, BCC=1, BKL=2, DF=3, MEL=4, NV=5, VASC=6, BENIGN=7, MALIGNANT=8`; do not call it a paper-specified index order. The binary source's published train/test organization is treated as protected here.

The read-only search emitted 41,381 candidate pairs at pHash **or** dHash Hamming distance ≤6: 37,015 binary–HAM and 4,366 binary–binary. This broad set contains false positives and is retained for review, not automatically grouped. More decisively, **1,926 binary–HAM pairs** have *both* 64-bit hashes identical (1,920 distinct binary files and 1,924 distinct HAM files). Resizing the corresponding HAM image to 224 × 224 with area interpolation gave mean absolute pixel difference <2/255 in 1,916 of those pairs and pixel correlation >0.99 in 1,925 pairs. Direct visual review of binary test `benign/1003.jpg` against HAM `ISIC_0028716.jpg`, and binary test `malignant/1003.jpg` against HAM `ISIC_0026847.jpg`, confirmed the same photographs; correlations after resizing exceeded 0.999. These results establish large cross-source re-encoded/resized overlap despite zero byte-identical cross-source hashes.

Among the strong binary–HAM pairs, HAM metadata labels are `nv` for 1,348 pairs and `mel` for 578 pairs. **401 distinct binary source-test images** have strong HAM matches. The same image would be labeled both `NV` and `BENIGN`, or both `MEL` and `MALIGNANT`, in the proposed nine-class target system. Those are different mutually exclusive targets, even though their broad clinical meanings may be compatible. Grouping them would prevent partition crossing, but would not resolve the target conflict or restore independent test cases.

There are also five binary–binary pairs with both hashes identical. Three are within train, including the byte-identical `malignant/768.jpg` and `769.jpg`. Two cross the published binary train/test directories: `test/benign/335.jpg` with `train/benign/1593.jpg`, and `test/malignant/507.jpg` with `train/malignant/439.jpg`. Visual inspection confirmed each pair depicts the same photograph; the second pair has pixel correlation >0.999. The source's own test boundary therefore contains near-duplicate leakage. Raw files were not changed.

### Preprocessing and split disposition

The existing deterministic operations in `src/preprocessing.py` are hair removal (17-pixel blackhat, threshold 10, Telea radius 1), Gray World, and Retinex (sigmas 15/80/250, equal weights, percentile scaling). Those numerical values are local adaptations rather than verified paper settings. HAM source dimensions vary; all binary images decode as 224 × 224 RGB JPEGs and may already have been resized. Existing `src/train.py` uses 384 × 384 resizing, pretrained-weight normalization, random flips/rotation on train only, and deterministic evaluation transforms. No new image preprocessing or split transforms were applied because of the stop gate.

The proposed 80/10/10, seed-42 group-aware allocation remains **unexecuted**. The source binary test allocation cannot be silently mixed into training. A combined split would need to account for at least the 401 strongly overlapping binary test images and the two binary train/test near-duplicate pairs, while resolving the nine-class target conflict. HAM lesion IDs are available, but binary patient and lesion IDs are absent. No patient-independent claim is possible.

### Outputs and validation

Generated audit artifacts only: `src/nine_class_similarity_audit.py`, `analysis/nine_class_similarity/fingerprints.csv` (13,312 entries), and `analysis/nine_class_similarity/candidates.csv` (41,381 candidate pairs). The audit covers only the canonical binary tree; the mirror was not enumerated. Original images, the existing HAM preprocessing cache, and HAM split files were untouched. No combined metadata, duplicate-exclusion manifest, processed-image copy, or nine-class train/validation/test manifest exists. Nine-class counts and split leakage validation are therefore blocked. The count 13,312 is the *pre-exclusion sum of source entries*, not a valid independent nine-class dataset size.


