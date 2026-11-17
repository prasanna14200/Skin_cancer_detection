# IQA methodology

**EXPLORATORY / NON-CLINICAL; cohort not approved; not an exact EG-VAN paper reproduction.**

## Scope and source artifacts

This analysis links the already-saved 1,028-row validation prediction artifact to the unchanged exploratory validation split by the exact key `(source_dataset, image_path)`. Each target class is taken directly from the split's `class_name` and original source label field; no diagnosis equivalence or label conversion was introduced. The frozen run's checkpoint, config, split, preprocessing, source-preview, and run-provenance hashes were checked by the existing validation diagnostic's input verifier. The checkpoint hash is recorded on each linked row.

No training, checkpoint loading for inference, inference, split modification, or dataset preparation was performed.

## Image-quality proxies

The experiment reused the `measure_rgb` function and feature names in `src/nine_class_iqa.py` (`nine_class_iqa_v2`). It measured all 14 proxies on each full-resolution decoded source image in RGB order: Laplacian variance, grayscale brightness and contrast, under-/overexposed fractions, RGB means and standard deviations, color-cast range, dark-line fraction, and dark-border fraction. Existing `PreprocessConfig` hair-kernel and line-threshold values were used. This is the `raw` measurement view, before the model's 384-pixel resize and ImageNet normalization; it is not a measurement of the exact model tensor. These are engineering proxies, not validated clinical image-quality scores.

## Outcome and analysis

`correct` is an exact equality comparison between the saved predicted class and the split's source-defined target class. For each feature, the analysis reports group counts, means, medians, quartiles, median differences, two-sided asymptotic Mann-Whitney U tests, and rank-biserial effect sizes. Per-class comparisons are performed only where both correctness groups have at least two records; otherwise the row is explicitly marked not run. Benjamini-Hochberg q-values are adjusted globally across all eligible overall and per-class tests.

Statistical outputs are descriptive screening results. Repeated overlap groups, source/patient independence limitations, severe class imbalance, and the unapproved exploratory split prevent confirmatory interpretation. No causal claim is made.
