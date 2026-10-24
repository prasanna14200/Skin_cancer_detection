# Stage 7: nine-class image-quality assessment

Date: 2026-10-22. Stage 7 implements deterministic image-quality **proxies** and a gated future quality-versus-prediction analysis. It does not decide whether an image is clinically usable, whether a label is correct, or whether a disputed image is eligible for training. The nine source-defined class order remains `AKIEC, BCC, BKL, DF, MEL, NV, VASC, BENIGN, MALIGNANT`. [Stage 6](NINE_CLASS_STAGE6_DATASET_RESOLUTION.md) still has no approved cohort or final test.

## Existing code and implementation boundary

The existing [`image_quality.py`](../src/image_quality.py) offers deterministic blur, luminance, exposure and related proxies for the older seven-class work. Its companion `run_quality_analysis.py` assumes historical seven-class processed files and frozen splits, so it is preserved but not used for this nine-class extension. [The Stage 7 IQA module](../src/nine_class_iqa.py) reads the Stage 4 **source inventory**, checks each original SHA-256, and uses the same `remove_hair`, `gray_world`, and `retinex` implementations and settings as the [Stage 4 loader](../src/nine_class_dataset.py). It measures raw decoded RGB separately from deterministic Stage 4 processed RGB after 384×384 resizing, before model normalization. It never applies train-only flips or rotations. It does not create a processed-image cache.

## Fixed proxy definitions, version `nine_class_iqa_v1`

Let `Y` be OpenCV's uint8 RGB-to-grayscale luminance approximation; `N` is pixel count, `μ` the mean, and `L` the discrete Laplacian. Values are measured on the **particular pixel view** identified in each row.

| Feature | Definition | Main limitation |
| --- | --- | --- |
| Sharpness | `variance(L(Y))` | Texture, JPEG noise, lesion borders and hair can raise it; blur does not have a universal threshold. |
| Brightness | `mean(Y)` | Camera/skin tone and preprocessing affect it; neither high nor low implies diagnostic usability. |
| Contrast | `std(Y)` | Global spread misses local contrast and can rise with artifacts. |
| Under/overexposure | Fractions of `Y < 30` and `Y > 225` | Fixed descriptive 8-bit cutoffs, not clinically calibrated exposure limits. |
| RGB characteristics | Per-channel mean and standard deviation; `(max(channel means)−min(channel means))/255` color-cast range | Lesion/skin colors and illumination are confounded; a neutral cast is not intrinsically best. |
| Dark-line indicator | Fraction of blackhat response `> 10`, with 17-pixel elliptical kernel | Detects dark thin structures including lesion texture, rulers, markings and compression; it is not a validated hair detector. |
| Dark-border indicator | Fraction of dark pixels in the outer 5% image border | Vignetting, framing and naturally dark skin can trigger it; it is not an occlusion label. |
| Image geometry | Original and measured width/height, aspect ratio `width/height`, megapixels `width×height/10⁶` | Resolution alone does not measure focus or clinical information. |

Uniform luminance is explicitly flagged; its finite zero contrast/sharpness values remain well-defined. Decode or processing failures produce `processing_status` and missing-metric flags rather than invented numbers. No thresholds are fit from protected test data. The sample selector sorts source-qualified paths deterministically, selects a fixed count per nine classes, and excludes every publisher `source_split=test` entry. The source inventory contains disputed and unapproved entries, so this is **descriptive source imagery only**, not a training or validation cohort.

Stage 4's Telea inpainting can replace pixels under its dark-structure mask; Gray World rescales color channels; Retinex changes local and global tonal relations; resizing changes edges and spatial frequency. Thus a higher postprocessing Laplacian variance or contrast may reflect algorithms rather than recovered lesion information. Raw and processed feature values must be analyzed as separate views, never pooled without the `measurement_view` field.

**Visual preprocessing finding:** the two bounded examples show conspicuous tonal changes: dark lesion areas appear much lighter and surrounding skin darker after Stage 4 processing. The local Retinex implementation computes `log(GaussianBlur(image)) − log(image)` before per-channel percentile scaling. That sign and scaling can reverse local brightness relationships. This is an observed software/output concern, not a clinical judgment from two images. Review the paper equation and intended display range with the researcher or authors, then conduct a broader blinded visual/quantitative check before using these processed views for full training or claiming improved image quality. Stage 7 preserves the Stage 4 implementation so the discrepancy remains auditable.

## Feature schema and generated sample

Each CSV row contains `source_image_key = source_dataset:image_path`, `image_path`, `source_dataset`, `class_name`, `class_index`, `source_split`, `source_image_sha256`, `iqa_config_version`, `preprocess_config_sha256`, `measurement_view`, original and measured geometry, all named features, `invalid_metric_flags`, and `processing_status`. The preprocessing settings and inventory SHA-256 appear in [`iqa_summary.json`](../analysis/nine_class_stage7/descriptive_sample_1_per_class/iqa_summary.json). Image identifiers are source qualified; patient identifiers are neither displayed nor invented.

I ran a **bounded, non-source-test descriptive sample** of one image per class from the Stage 4 inventory. The [feature table](../analysis/nine_class_stage7/descriptive_sample_1_per_class/iqa_features.csv) has 9 source images and 18 view records; all 18 processed successfully. The output directory also contains separate blur, brightness, contrast and exposure distribution plots, a raw-feature correlation heatmap, and two [before/after examples](../analysis/nine_class_stage7/descriptive_sample_1_per_class/example_1_raw_vs_processed.png) from distinct source datasets. These figures demonstrate the pipeline and are **not** evidence of clinical improvement. With one image per class, distribution shape and correlations are illustrative only. Full-inventory IQA is available but was not run.

Reproduce in a **new** output directory from the project root:

```powershell
python src/nine_class_iqa.py --sample-per-class 1 --output-dir analysis/nine_class_stage7/NEW_DESCRIPTIVE_RUN
```

`--sample-per-class 0` selects all non-source-test inventory rows; that larger analysis should be run only if needed. The module refuses an existing output directory and checks source hashes before and after measurement. It never edits raw photographs or earlier experiment outputs.

## Future prediction association, currently gated

The [performance module](../src/nine_class_iqa_performance.py) can later join `iqa_features.csv` to Stage 6 `predictions.csv` using `(source_dataset, image_path)`, checking the approved source-image hash for the chosen raw or processed view. It requires a real approved split and approval record, matching evaluation manifest/approval/checkpoint hashes, exact prediction coverage of the approved partition, labels and probabilities consistent with the manifest, and a separate `--final-test` flag for a frozen nine-class test. An IQA sample cannot be joined to a larger prediction cohort with missing measurements. **No approved prediction artifact exists now**, so no quality-versus-performance result or clinical claim is produced.

After that gate, the module writes equal-count feature-rank quantile accuracy/error summaries, per-class mean/median/interquartile quality features, confidence and normalized predictive-entropy summaries, joined rows, provenance and plots including per-class distributions and feature-versus-confidence/uncertainty scatterplots. Rank bins have deterministic source-key tie ordering; their boundaries and sample counts must be reported. Confidence is maximum class probability; uncertainty is predictive entropy divided by `ln(9)`. These are observational associations, susceptible to source and class composition confounding. Validation may be used for exploratory questions; protected test must remain reserved for a predeclared final analysis, never for choosing quality thresholds or a model.

Future command, **only after Stage 6 approval, training and evaluation**:

```powershell
python src/nine_class_iqa_performance.py --approved-split PATH_TO_APPROVED_SPLIT.csv --approval PATH_TO_REAL_APPROVAL.json --inventory PATH_TO_APPROVED_INVENTORY.csv --evaluation-dir PATH_TO_STAGE6_VALIDATION_EVALUATION --iqa-csv PATH_TO_COMPLETE_IQA_FEATURES.csv --view raw --output-dir PATH_TO_NEW_IQA_ASSOCIATION
```

For the frozen final test, supply its Stage 6 evaluation directory and add `--final-test`; use a new output directory. The full approved prediction cohort must have IQA records in the chosen view.

## Tests and Stage 8 handoff

`tests/test_nine_class_stage7.py` uses synthetic images to check sharp versus blurred, bright versus dark, low versus high contrast, exposure fractions, uniform-image finite values, deterministic Stage 4 processing, raw/processed separation, original byte integrity, source-qualified joining, IQA hash mismatch, and rejection of absent or unapproved evaluation inputs. Stage 4–6 focused tests are regression checks. No checkpoint is loaded and no training runs in Stage 7.

**IQA implementation readiness:** yes. **Quality-performance findings:** unavailable until an approved nine-class cohort yields genuine Stage 6 predictions. **Processed-image clinical-use readiness:** unresolved because of the tonal-change finding above. Stage 8 can build uncertainty estimation using the same nine probability columns and cohort provenance; it should predefine calibration and uncertainty analyses on validation, then reserve the protected test for final reporting.
