# Stage 3F — reproducible duplicate-verification evidence

Decision date: 2026-10-19. The research objective remains **nine-class EG-VAN**. This method adds reproducible image-pair measurements to the Stage 3E review. It does not change clinical labels, human choices, source images, proposed exclusions, or dataset splits.

## Existing audit: what each measurement establishes

The original [fingerprint script](../src/nine_class_similarity_audit.py) decodes each image as grayscale. Its 64-bit pHash uses a 32×32 resize, 8×8 DCT and median threshold. Its implementation excludes the **first DCT row** from the median, rather than only the DC coefficient; it is therefore a locally defined hash, not necessarily identical to another library's pHash. dHash compares neighbors in a 9×8 grayscale resize. Hamming distances retrieve candidates when **either** hash distance is ≤6. The [first overlap review](../src/nine_class_overlap_review.py) prioritizes pairs when **both** distances are ≤6. Retrieval and priority thresholds were workflow rules, never validated identity probabilities. Rotation, cropping, lesions with common color/texture, and compression can alter hashes; low hash distance does not prove a shared photo and larger distance does not prove independence.

SHA-256 compares source file bytes exactly. The audit found no byte-identical HAM–binary pair, although many pairs are photographically related after different resizing/recompression. `train/malignant/768.jpg` and `769.jpg` are a verified byte-identical local binary control. The two binary trees are mirrors and must not be counted as extra observations.

The original full-pixel MAE and Pearson correlation decode RGB images. The binary image is the reference, normally 224×224; the other image is **resized directly to its width and height** if dimensions differ. The comparison is then pixel-for-pixel with no registration, orientation correction, crop search, or homography. In particular, a 600×450 HAM image may be nonuniformly squeezed to 224×224. This makes the metrics meaningful for closely aligned, similarly processed photos, but less interpretable for translated, rotated, differently cropped, or perspective-changed views. The earlier automated direct-pixel rule, MAE ≤2/255 **and** correlation ≥0.999, was a conservative audit rule, not a clinically validated error bound. The completion pass additionally used 64×64 grayscale correlation and edge correlation for screening, with broad full-pixel scoring when `min(pHash,dHash)≤2`, or `max≤8`, or coarse MAE ≤10/255, or grayscale correlation ≥0.96, or edge correlation ≥0.85. Those screens did not produce independent ground truth.

## New geometric verification

The [geometric script](../src/nine_class_geometric_verification.py) processes the same 429 unique Stage 3E pairs in a new [read-only-derived evidence CSV](../analysis/nine_class_recovery/geometric_pair_evidence.csv). It tries ORB keypoints/descriptors and bidirectional nearest-neighbor ratio matching. OpenCV recommends Hamming distance for ORB; the ratio-match plus RANSAC homography sequence follows its [feature/homography tutorial](https://docs.opencv.org/4.x/d7/dff/tutorial_feature_homography.html) and [matcher reference](https://docs.opencv.org/4.12.0/d3/da1/classcv_1_1BFMatcher.html). If ORB lacks a coherent consensus, the script tries SIFT with L2 matching as a fallback. It records both image sizes, candidate view, keypoint counts, ratio matches, mutual matches, RANSAC inliers and ratio, median reprojection error, transformation matrix, failure reason, and a separate automated evidence category.

Images are decoded in grayscale and capped at 800 pixels on the longer side. For differing aspect ratios, the first view explicitly resizes the candidate to the binary image's width and height; the native-aspect view is also tried if needed. This hypothesis is recorded as `aspect_normalized_to_binary` and is **not** evidence that the original photography had that aspect ratio. The chosen homography maps candidate coordinates to binary coordinates. A landmark view is generated **on request** from the original images; it is a visualization aid, not a processed dataset image.

| Fixed implementation gate | Value | Purpose and status |
| --- | ---: | --- |
| ORB ratio / SIFT ratio | 0.75 / 0.70 | Remove ambiguous descriptor neighbors; heuristic. |
| Minimum keypoints per image / mutual matches | 8 / 8 | Minimum data to attempt a homography; heuristic. |
| RANSAC reprojection threshold | 3 pixels | Permit modest localization error at analyzed resolution; [OpenCV's tutorial](https://docs.opencv.org/4.x/d7/dff/tutorial_feature_homography.html) uses this scale. |
| Coherent consensus | ≥12 inliers, ≥0.50 inlier ratio, ≤2-pixel median reprojection error | Reject weak or inconsistent geometry for *display and review priority only*. |
| Mapped candidate area | ≥2% of binary image area | Reject degenerate homographies; heuristic. |
| Review-priority pixel fallback when geometry is unreliable | correlation ≥0.995 and MAE ≤5/255 | Keep an already aligned, highly similar pair in `NEEDS_HUMAN_REVIEW`; never confirms identity. |

These gates were fixed before the controlled validation run and **were not fitted to the 429 pair decisions**. They are not calibrated confidence thresholds. A coherent homography supports common local visual structure; repeated dermoscopic texture, rulers, frames, and artifacts may still yield false matches. An unreliable match can arise from low texture, blur, reflection, crop size, feature-detector limits, or nonlinear preprocessing. A failed match never means `DISTINCT`. Area-based ECC registration is an alternative for nearly aligned low-feature pairs, but it requires a good initialization and can optimize a background artifact; it was **not** added as automatic evidence here. Manual original-resolution comparison remains necessary for scientific adjudication.

## Validation set and measured stress behavior

The [validation manifest](../analysis/nine_class_recovery/geometric_validation_manifest.csv) deterministically selects 40 HAM images with distinct recorded lesion IDs using a fixed SHA-256 ranking. Twenty source images form a development partition and twenty a held-out partition; their source paths do not overlap. No examples from either partition were used to choose the geometric gates. Each source supplies four **in-memory controlled positive** views: an exact decoded-pixel copy, 224×224 JPEG-quality-75 version, 90° rotation, and central 80% crop. These are known same-source-photograph transformations and never become dataset images. The manifest also includes the real SHA-256-identical `malignant/768.jpg`/`769.jpg` file pair.

For each HAM source, a visually difficult *candidate negative* is selected by the smallest pHash distance among same-diagnosis HAM images with a **different recorded lesion ID**. This gives 40 metadata-distinct candidate pairs, but different metadata IDs alone do not independently establish photographic or lesion distinctness. They are marked `provisional_distinct_requires_independent_verification`, **not negative ground truth**. They need source-ID verification and blinded human confirmation before calculating a false-positive rate. Using the same pair set to choose a threshold and score it would invalidate the held-out test; any future calibrated rule must be frozen on development data, then evaluated once on separate, independently adjudicated test pairs.

The [validation summary](../analysis/nine_class_recovery/geometric_validation_summary.json) reports coherent geometry on held-out controlled positives: **20/20** decoded-pixel copies, **19/20** resized/JPEG views, **20/20** 90° rotations, and **20/20** central crops. The one controlled JPEG failure illustrates that a failed geometric match cannot be a distinctness rule. The byte-identical source-file control is included separately in the manifest. These fractions describe **synthetic stress behavior only**, not real-world duplicate-detector recall.

**Detector precision, recall, false-positive rate, and false-negative rate are unavailable.** There are zero independently verified hard negatives, and the current geometric category is a review aid rather than a validated binary identity detector. No confidence percentage is assigned. The validation summary stores these four metrics as `null` rather than inventing values.

## Triage of the 429 review pairs

The [pair summary](../analysis/nine_class_recovery/geometric_verification_summary.json) reports:

| Automated evidence category | Pairs | Interpretation |
| --- | ---: | --- |
| `HIGH_CONFIDENCE_SAME_PHOTO` | **0** | With no independent hard-negative calibration, this label is withheld. |
| `HIGH_CONFIDENCE_DISTINCT` | **0** | Neither weak geometry nor low similarity can establish distinctness. |
| `NEEDS_HUMAN_REVIEW` | **83** | Coherent geometry or strong aligned-pixel evidence warrants focused original-image review. |
| `INSUFFICIENT_EVIDENCE` | **346** | Existing and new automated measurements cannot settle identity. Human/source evidence is still needed. |

Exactly one HAM candidate for **each of the 83 retained BENIGN records** yielded coherent geometry; all 83 were in the aspect-normalized view, with 14–2,329 inliers and ≥0.971 inlier ratio. The other 272 BENIGN–HAM pairs and 74 binary–binary pairs lacked sufficient mutual matches. This is strong **triage** information but does not adjudicate any pair. In particular, the 83 coherent pairs are not promoted to automatic exclusions.

## Automated evidence and human decisions remain separate

The updated [review interface](../src/nine_class_benign_review.html) displays original metrics, geometric results, limitation text, and a matched-landmark view only for coherent geometry. Its radio choices remain `SAME_PHOTO`, `SAME_LESION`, `DISTINCT`, and `UNCERTAIN`; no choice is preselected for an unreviewed pair. A reviewer may disagree with the automated category and save a required explanation to [the separate feedback ledger](../analysis/nine_class_recovery/benign_pair_evidence_feedback.csv). That action does not alter the [human-decision ledger](../analysis/nine_class_recovery/benign_pair_review_ledger.csv). `SAME_LESION` is never assigned automatically. Reviewers should check whether landmarks lie on the lesion rather than a common frame, ruler, or background.

At this audit's start, the human ledger already contained **one** source-test `SAME_PHOTO` decision and 428 unreviewed pairs. Its SHA-256 was `ba89c8f9c54a96c08f58c2ac55db801a05d4018b470332eaa5dc6c0f0dd51999` before and after Stage 3F initialization. Stage 3F did not change that decision or compute new exclusions. Eighteen source-test records still lacked a complete set of non-`UNCERTAIN` decisions at the time of this report; the live interface summary may change as the researcher reviews more pairs.

## Reproduce and continue

From the project root, with the existing OpenCV, NumPy and pytest environment:

```powershell
python src/nine_class_geometric_verification.py --verify
python src/nine_class_benign_review.py
python -m pytest tests/test_nine_class_benign_review.py tests/test_nine_class_geometric_verification.py -q
```

The first run was made without `--verify`; it wrote only new Stage 3F evidence files and refuses to overwrite an existing pair audit. `--verify` recomputes both the controlled validation and all 429 pair measurements, comparing them to the saved files without writing. It ignores only the historical *human-ledger byte hash* in pair evidence, because later legitimate reviews may change that ledger without changing pair paths. For a changed method, use separately named output files. The runtime used here was OpenCV **5.0.0**. No dataset was downloaded. Original Stage 3 similarity/overlap evidence, raw images, labels, and reviewer choices remain unchanged. Final nine-class eligibility and splitting remain blocked until human/source adjudication and independently validated error estimates are available.
