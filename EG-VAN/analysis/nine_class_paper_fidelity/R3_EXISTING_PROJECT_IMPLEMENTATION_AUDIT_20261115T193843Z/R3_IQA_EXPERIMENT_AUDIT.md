# R3 Image-Quality Assessment Audit

## Implemented code

`src/nine_class_iqa.py` implements deterministic raw/processed image-quality proxies: Laplacian sharpness, grayscale brightness/contrast, under/overexposure fractions, RGB means/standard deviations, color-cast range, dark-line and dark-border fractions, and image geometry. It separates `raw` from `stage4_processed`; the metrics are proxies, not clinical usability labels. `src/nine_class_iqa_performance.py` implements a gated join with approved predictions, source hashes, equal-count quality ranks, per-class summaries, confidence/entropy and error association. Its gate requires an approved cohort and complete matching evaluation artifacts.

## Executed descriptive results

`analysis/nine_class_stage7/descriptive_sample_1_per_class/` contains one source image per class (9 total), 18 raw/processed metric rows, all with `processing_status=OK`, and eight plots/examples listed in `iqa_summary.json`. This is a descriptive sample from the unapproved source inventory, not an approved training/validation cohort. No model checkpoint or classification predictions were joined.

The saved rows identify themselves as `nine_class_iqa_v1`, while the current source module declares `IQA_VERSION = nine_class_iqa_v2` and now enforces approval gates. The output has no source-code hash; it should be treated as an older versioned result, not a byte-for-byte execution of the current module.

For orientation only, the nine-image sample's raw versus Stage4-processed means were:

| Proxy | Raw mean | Stage4 processed mean |
|---|---:|---:|
| Brightness | 161.2876 | 60.8171 |
| Underexposed fraction | 0.000340 | 0.309619 |
| Sharpness (Laplacian variance) | 74.3317 | 243.0788 |
| Dark-line fraction | 0.138225 | 0.433204 |
| Dark-border fraction | 0.000133 | 0.293912 |

These are unweighted descriptive means over one image per class. They show strong pixel-statistic changes, not that processing improves diagnostic quality. Individual saved values for all 14 features and both views are included in `R3_EXISTING_RESULTS_INVENTORY.csv`.

`analysis/nine_class_stage10/preprocessing_summary.json` records a separate non-source-test sample of 26 images, 104 measurement rows, and four variants: raw, hair+Gray World, full Stage4, and mild luminance Retinex. Its values are medians across the sample. For example, full Stage4 had median brightness 67.7812, underexposed fraction 0.191315, sharpness 226.8526, and luminance-pixel correlation -0.9228299 versus raw; the mild variant had median brightness 160.6287 and correlation 0.9798070. The comparison is descriptive and has no classification-performance arm.

## Execution and scientific validity

Implemented: deterministic feature extraction, figures, preprocessing comparison, and a gated future quality-vs-error/confidence/uncertainty analysis.

Executed: Stage 7 one-image-per-class descriptive sample and Stage 10 26-image preprocessing comparison.

Not executed: approved nine-class IQA-performance association, quality-versus-error analysis, class-conditioned model-performance comparison, or any clinical quality assessment. No run joins the 9-image IQA table to the 1,028 validation predictions; the current performance module would reject a missing/incomplete approved evaluation cohort. No test threshold or image-quality cutoff was fit.

No images were opened by this audit; saved numerical tables, metadata and source code were inspected only.
