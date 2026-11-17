# Exploratory IQA experiment report

**EXPLORATORY / NON-CLINICAL - cohort not approved; not an exact EG-VAN paper reproduction.**

## Result

Completed a retrospective association analysis on the already-saved validation predictions. Linked all **1028** predictions to the unchanged validation split by `(source_dataset, image_path)` and measured the existing `nine_class_iqa_v2` 14 raw-image proxies. All 1028 images decoded, all source-image SHA-256 values matched the frozen split before and after measurement, and all metric records completed successfully.

- Correct / incorrect: **628 / 400**; accuracy recomputed from saved predictions: **0.610895** (prior saved accuracy: 0.610895; macro-F1: 0.097532). These model metrics predate this IQA experiment.
- Missing IQA values: **0 / 14392**.
- Overall tests with global Benjamini-Hochberg q < 0.05: **9 / 14**. These unadjusted-for-class tests are strongly subject to class/source-composition confounding and are not confirmatory.
- Within-class tests were possible only for BCC (3 correct, 46 incorrect) and NV (624 correct, 5 incorrect). Four NV feature comparisons crossed q < 0.05 after global adjustment across all eligible tests; the five-case error group makes these estimates unstable. The other seven classes had no eligible two-group test.
- The model predicted NV for 1012 of 1,028 predictions.
- All 1028 rows carry image path, source-defined label, prediction, prediction probabilities, split/source metadata, source image hash, and frozen checkpoint/artifact hashes.

## What ran / did not run

**Ran:** read-only provenance and prediction/split audit; image decoding and source-hash validation; raw-image IQA extraction for 1,028 images; correctness-group and per-class descriptive statistics; Mann-Whitney U tests, rank-biserial effect sizes, global BH correction; three plots.

**Did not run:** training, inference, split/dataset preparation or changes, cohort approval, uncertainty/calibration, external validation, causal or clinical assessment.

## Key limitations

- All cohort rows remain `NOT_APPROVED`; no leakage-safe validation or research readiness is claimed. The split contains **192 repeated overlap-group IDs covering 429 rows**; patient independence is unverified. No exact-byte duplicate was found among the 1,028 validation images, which does not establish photographic independence.
- 84 Fanconic records lack recorded source image, lesion, and patient IDs. They were joined using the source-qualified path and verified file hash; no IDs were invented.
- Correctness is strongly class-dependent, with severe class imbalance and near-collapse to NV. The global differences may reflect class and source composition rather than image quality. Within-class analyses are sparse.
- The metrics are unvalidated engineering proxies on full-resolution raw images, not clinical quality scores or the model's resized/normalized tensor. Association is not causation.
- Source labels were kept unchanged; no label-equivalence assumptions were added.

## Artifacts

See `IQA_METHODOLOGY.md`, `IQA_STATISTICAL_ANALYSIS.md`, `IQA_LIMITATIONS.md`, `IQA_REPRODUCIBILITY.md`, linked-row and summary CSVs, plots, source evidence, linkage audit, and `IQA_VALIDATION.md`. `IQA_MANIFEST.sha256` hashes every other deliverable in this directory.
