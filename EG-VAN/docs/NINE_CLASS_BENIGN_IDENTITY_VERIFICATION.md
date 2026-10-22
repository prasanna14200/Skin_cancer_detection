# Stage 3G — independent verification of retained BENIGN overlap

Date: 2026-10-19. The research objective remains **nine-class EG-VAN**. This is an evidence and review report, not an exclusion ledger, final manifest, split, preprocessing run, or model result. No raw image, earlier audit CSV, source label, or existing human decision was changed.

## What was investigated

The [83-row strong-pair report](../analysis/nine_class_recovery/stage3g/strong_pair_identity_evidence.csv) covers exactly one geometrically coherent HAM candidate for each of the 83 provisionally retained Fanconic BENIGN entries: 19 publisher source-test and 64 source-train. It preserves both original image paths, original pHash/dHash and pixel scores, the Stage 3F keypoint/RANSAC measurements, HAM `image_id`, `lesion_id`, `dx`, `dx_type`, the human-ledger decision as it stood at this audit, and the Stage 3G conclusion status. **All 83 HAM candidates have recorded `dx=nv`; this is metadata about the HAM images, not a clinical reassignment of any binary label.** HAM `dx_type` is 60 `histo`, 16 `consensus`, and 7 `follow_up`. Fanconic still provides no original ISIC image IDs or patient/lesion IDs for its numeric files.

For each pair, the [Stage 3G script](../src/nine_class_stage3g_verification.py) reproduces the frozen registration, checks the mapped image corners and valid overlap, then saves three review aids under [`analysis/nine_class_recovery/stage3g/`](../analysis/nine_class_recovery/stage3g/):

1. **Aligned overlay:** binary grayscale, registered HAM grayscale, and a 50/50 blend. The HAM image is first resized to the square binary view because this was the recorded Stage 3F registration hypothesis.
2. **Difference image:** absolute grayscale difference multiplied by four for visibility. Gray borders mark pixels outside the valid warp. The amplified colors are for review, not calibrated error magnitudes.
3. **Landmark view:** all inlier locations over the binary image and registered HAM image. The center box spans 20–80% of both axes. Green points lie in that box; red points lie outside it. **The box is not a lesion mask, and points on skin texture or artifacts can be misleading.**

The [static 83-pair gallery](../analysis/nine_class_recovery/stage3g/strong_pair_gallery.html) links each view and both original-resolution files. The CSV gives the exact per-pair image paths and uncertainty requirement. Images in these review aids are derived artifacts only; no model input or source image was replaced.

## Registration and lesion-structure checks

The geometric check records mapped-corner area relative to the binary canvas, transformed center displacement, projective component, valid aligned fraction, aligned grayscale MAE/correlation, central inlier fraction, and inlier convex-hull coverage. A mapping is flagged as *geometrically plausible* only if its corner area is 0.5–2.0 times the binary area, the local 2×2 determinant is positive, projective strength is ≤0.1, center shift is at most half the canvas diagonal, and valid aligned area is ≥70%. These are **sanity checks for a review image**, not calibrated identity thresholds. The original 83-pair pixel correlation ranges **0.99612777–0.99893552**; after registration the grayscale correlation ranges **0.92890714–0.99948936**. A color-to-grayscale change and warped borders make those two ranges different measures.

**82/83** transforms pass the mapping sanity check. The exception is `data/isic/data/train/benign/1169.jpg` versus HAM `ISIC_0028947.jpg`: projective strength is **0.203683**, above the 0.1 review gate, although corner area ratio is 0.981967 and valid aligned fraction is 0.936543. Its overlay visibly warrants a closer original-image and landmark check; the outlier is **not** evidence of a distinct photograph. The per-pair status is `INSUFFICIENT_EVIDENCE` pending that check.

The central inlier fraction ranges **0.361338–0.993333**. Six pairs have fewer than half of their inliers in the center box: source BENIGN basenames `61`, `670`, `1260`, `997`, `162`, and `1236`. Four pairs have aligned grayscale correlation below 0.98: basenames `89`, `1543`, `1169`, and `1181`. These are **review priorities**, not negative decisions. Landmark concentration within the center can still be generic skin texture, hair, or a ruler. There is no independently verified lesion segmentation for this binary collection. Thus the `lesion_structure_match_status` column is `not_independently_verified_no_lesion_mask` for **every** pair; an independent reviewer must inspect lesion-specific pigment, borders, vessels and nearby artifacts in the original-resolution views. Automated location proxies cannot complete that check.

## Identity conclusions and existing human judgment

| Stage 3G conclusion status | Pairs | Reason |
| --- | ---: | --- |
| `VERIFIED_SAME_PHOTO` | **0** | No pair has completed the stated independent lesion-structure/source confirmation. |
| `VERIFIED_DISTINCT` | **0** | Good or poor registration cannot establish independent lesions. |
| `REQUIRES_REVIEW` | **82** | Plausible mapping; identity still requires independent original-resolution judgment. |
| `INSUFFICIENT_EVIDENCE` | **1** | Pair `1169.jpg` has a projective-warp outlier requiring closer geometry review. |

The existing [Stage 3E human ledger](../analysis/nine_class_recovery/benign_pair_review_ledger.csv) contains **one** source-test `SAME_PHOTO` entry, for `data/isic/data/test/benign/802.jpg` versus HAM `ISIC_0028399.jpg`. It has no reviewer note or second independent confirmation. Stage 3G preserves this saved choice but does **not** convert it to `VERIFIED_SAME_PHOTO` or apply an exclusion. The human-ledger SHA-256 remained `ba89c8f9c54a96c08f58c2ac55db801a05d4018b470332eaa5dc6c0f0dd51999` through the evidence run. A reviewer may confirm, revise, or document disagreement through the existing [pair-review interface](NINE_CLASS_BENIGN_REVIEW_WORKFLOW.md); Stage 3G does not preselect an answer.

The remaining **346** focused Stage 3F pairs were not converted into Stage 3G identity conclusions. They include 272 other BENIGN–HAM and 74 binary–binary relations, retain `INSUFFICIENT_EVIDENCE` as automated Stage 3F triage, and still require human/source evaluation where relevant. Resolving only the strongest HAM candidate for each BENIGN image does not resolve every relation touching that record.

## Blind validation of difficult candidate nonmatches

The [40-case blind queue](../analysis/nine_class_recovery/stage3g/blinded_validation_queue.csv) maps random-looking case codes to the Stage 3F provisional hard-negative pairs. The source metadata records different HAM `lesion_id` values, but those values alone do **not** prove two photographs depict distinct lesions. All 40 cases are explicitly `unreviewed` and `pending`; **zero** independently verified hard negatives are available.

The [blind review server](../src/nine_class_blinded_validation_review.py) shows only paired images and a case code. Its API does not expose source paths, lesion IDs, partition, similarity scores, or the metadata relation. To conduct two independent passes, run from the project root:

```powershell
python src/nine_class_blinded_validation_review.py --reviewer R1 --port 8766
python src/nine_class_blinded_validation_review.py --reviewer R2 --port 8767
```

Each reviewer opens their local URL and saves `SAME_PHOTO`, `SAME_LESION`, `DISTINCT`, or `UNCERTAIN` with optional visual notes. The two reviewer codes create **separate ledgers only when those reviewers start**; none has been fabricated or filled here. Reviewers should not read the mapping queue or each other's ledger during their passes. After both complete all 40, reconcile disagreements using original images and metadata. Keep `UNCERTAIN` or conflicting cases out of verified-negative counts. For a negative to become independently verified, require concordant blinded `DISTINCT` judgments with written visual evidence and confirm that the source metadata identifies distinct images/lesions; document adjudication separately. Then freeze a rule using the development subset and evaluate it **once** on held-out verified cases. If the remaining verified test negatives are too few or not representative, report that limitation rather than a misleading rate.

The Stage 3F controlled positives remain 160 in-memory same-source transformations and one actual SHA-256-identical file pair. Held-out coherent geometry was 20/20 decoded copies, 19/20 resized/JPEG versions, 20/20 rotations, and 20/20 crops. These demonstrate stress behavior on known positives; they do **not** validate the false-positive rate on independent images. **Detector precision, recall, false-positive rate and false-negative rate remain unavailable** until independently confirmed positives and negatives support a frozen held-out evaluation. No confidence percentage is claimed.

## Conditional nine-class BENIGN impact

The current proposed retained BENIGN count stays **83** (64 source train, 19 source test); Stage 3G applied **zero** exclusions. If the one saved source-test `SAME_PHOTO` choice is independently confirmed and approved for exclusion, the upper bound would be **82** (64 train, 18 test). If all 83 strong HAM relations are eventually confirmed as duplicate photographs, **zero** BENIGN entries from this Fanconic tree would remain. More generally, if `k` unique BENIGN records are *independently confirmed and approved* as HAM copies, the upper bound is `83 − k`; source-test count is `19 − k_test`. The additional 346 focused relations and lower-priority audit candidates could reduce these counts further. None of these scenarios is a current manifest or split.

Even the present 19-record source-test BENIGN upper bound is very small, and all 19 have strong HAM overlap candidates. Thus the current Fanconic tree **does not yet support a meaningful leakage-audited nine-class evaluation**. The mandatory nine-class objective remains feasible only conditionally: obtain source/version and source-test evidence, finish independent pair review, and—if BENIGN cases are insufficient—assess a documented additional binary-labeled dermoscopic source. Such a source needs original clinical label definitions compatible with the source-conditioned nine-label task, image-level rights, original image IDs, patient/lesion identifiers, protected test policy, and verified nonoverlap with HAM10000/Fanconic. [SIIM–ISIC 2020](NINE_CLASS_DATASET_RECOVERY_PLAN.md) is a conditional provenance candidate, not an approved merged dataset; its malignant category has a narrower melanoma scope. Do not remap HAM diagnoses into BENIGN/MALIGNANT or assume the nine labels are mutually exclusive clinical diagnoses.

## Reproduction and remaining gate

From the project root, the following commands create Stage 3G evidence in a new directory and run focused tests:

```powershell
python src/nine_class_stage3g_verification.py
python src/nine_class_stage3g_gallery.py
python -m pytest tests/test_nine_class_stage3g_verification.py tests/test_nine_class_benign_review.py tests/test_nine_class_geometric_verification.py -q
```

The scripts refuse to overwrite existing Stage 3G files. The [Stage 3G summary](../analysis/nine_class_recovery/stage3g/stage3g_summary.json) freezes SHA-256 checksums of the input geometry CSV, validation manifest, HAM metadata, and human ledger. Original images, original audit evidence, labels, human decisions, and proposed exclusion counts are unchanged. Stage 4 dataset construction remains gated on independent identity and negative-control review, provenance, rights, and a defensible nine-class test protocol.
