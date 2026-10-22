# Stage 3E — BENIGN image-pair human review

The nine-class EG-VAN dataset decision is still pending. This local interface records **image-relation judgments only**. It does not change source labels, apply exclusions, construct a manifest, or generate splits.

## Launch and review order

From the project root, run:

```powershell
python src/nine_class_benign_review.py
```

Open `http://127.0.0.1:8765/` in a local browser. Use `--port 8766` if that port is occupied. The server binds to `127.0.0.1` and stops with Ctrl+C. Reopening the server reloads the saved ledger. `python src/nine_class_benign_review.py --init` creates or verifies the ledger and exits without launching the page.

The interface follows [the 83-record plan](../analysis/nine_class_recovery/benign_review_plan.csv): T1 contains the 19 publisher source-test BENIGN images, followed by T2–T5 with 16 source-train images each. The existing [T1 contact sheet 1](../analysis/nine_class_recovery/review_sheet_01.jpg) and [sheet 2](../analysis/nine_class_recovery/review_sheet_02.jpg) are linked in the page. Each displayed image opens at its original resolution in a new tab. The paths, candidate image identifier, source partition, pHash/dHash distances, pixel MAE/correlation, coarse correlation, and source evidence row appear beside the pair.

The [focused source queue](../analysis/nine_class_overlap_completion/human_review_queue.csv) has **429 unique unresolved pairs touching the 83 records**: 355 BENIGN–HAM and 74 binary–binary. A pair involving two retained BENIGN records is visible from both record pages but has **one stable pair ID and one ledger decision**. Batch pair totals can overlap for this reason. The reviewer should inspect every relevant pair; a top candidate alone does not settle the other relations.

For each pair, choose exactly one decision and press **Save this pair**:

- `SAME_PHOTO`: the same photograph, possibly resized, cropped, recompressed, or color adjusted.
- `SAME_LESION`: a different photograph appears to show the same lesion. Use only when the visual evidence supports this relation; do not infer a diagnosis.
- `DISTINCT`: enough visual evidence shows different photographs and lesions.
- `UNCERTAIN`: available images do not support a reliable relation decision.

No option is preselected for an unreviewed pair. Notes are optional but should capture the distinguishing visual evidence or reason for uncertainty. A saved choice can be corrected by selecting another option and saving again; the latest decision and UTC timestamp are retained. Do not call an automated match human-reviewed. The interface provides no bulk decision action.

## Ledger and summary

[The review ledger](../analysis/nine_class_recovery/benign_pair_review_ledger.csv) begins with 429 rows marked `unreviewed`, empty decisions and timestamps. Each row includes the binary path, candidate path, SHA-256-derived pair ID, source partition, candidate source and identifier, similarity metrics, choice, notes, status, UTC time, and exact focused-queue row reference. It is written atomically on each save. [The summary](../analysis/nine_class_recovery/benign_pair_review_summary.json) reports reviewed and unreviewed pairs, counts for all four choices, fully resolved BENIGN records, source-test blockers, and per-batch progress. `UNCERTAIN` counts as a reviewed pair but **does not** resolve that relationship or its BENIGN record. An image is fully resolved only when all its related pairs have `SAME_PHOTO`, `SAME_LESION`, or `DISTINCT` decisions.

The source images, plan, similarity fingerprints, focused queue, completion evidence, and proposed exclusion ledger remain separate and unchanged. Review decisions do **not** automatically recalculate exclusions. A later, separately approved dataset decision must inspect the ledger and preserve the publisher source-test boundary.

## Stage 3F evidence panel

The page now shows [geometric verification](NINE_CLASS_DUPLICATE_VERIFICATION_METHOD.md) beside each pair: ORB/SIFT method, aspect-normalization view, keypoint and mutual-match counts, RANSAC inliers and ratio, reprojection error, automated evidence category, and the method's limits. A **matched landmarks** link appears only when the geometric consensus is coherent. The original-resolution image links remain the primary review view. Automated categories do not select a radio choice or change eligibility.

Use the independent **I disagree with the automated evidence category** checkbox and explain why if the geometric evidence seems misleading. This writes only to [the evidence-feedback ledger](../analysis/nine_class_recovery/benign_pair_evidence_feedback.csv), with one row per pair; it does not edit the human choice or the source audit. A reason is required for disagreement. The reviewer can still choose any of the four human decisions, including `UNCERTAIN`.

## Initial state and checks

At preparation: **0 reviewed**, **429 unreviewed** pairs; all decision counts **0**; **0/83** BENIGN records fully resolved; **19** source-test blockers. The ledger records no human adjudication yet.

Run `python -m pytest tests/test_nine_class_benign_review.py tests/test_nine_class_geometric_verification.py -q` for path resolution, pair coverage, decision/feedback persistence, reopening, invalid-decision rejection, uncertainty handling, geometric controls, and original audit preservation checks. These tests write only to temporary ledgers, never to the working review ledger.
