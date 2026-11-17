# Reproducibility

Status: **EXPLORATORY / NON-CLINICAL**.

## Inputs and provenance

See `IQA_SOURCE_EVIDENCE.csv` for source paths, SHA-256 hashes, and byte lengths. The frozen best checkpoint SHA-256 is `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`; the validation prediction CSV SHA-256 is `fb46054fa919de0b3f9774f2e6a97546900c2e0edbde584125e622cf253f1b96`; the exploratory split SHA-256 is `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740`. Predictions were joined exactly by `(source_dataset, image_path)` and their `true_class` values matched split labels. Source images were decoded and rehashed during measurement.

## Metric implementation and runtime

The exact `measure_rgb` function was extracted from the hashed `src/nine_class_iqa.py` source and executed unchanged because the available image-measurement runtime lacked Matplotlib, an unused plotting import for this function. Metric runtime: CPython 3.10.16, OpenCV 5.0.0, NumPy 2.2.6, using the existing CPython 3.10 project site-packages; no packages were installed. The function used the current IQA config's hair-kernel size 17 and line threshold 10.

Statistical and plotting runtime: CPython 3.13.5, pandas 2.2.3, NumPy 2.1.3, SciPy 1.15.3, Matplotlib 3.10.0.

## Reproduction outline

1. Read the frozen validation prediction CSV and `exploratory_split.csv`; require exact validation-key-set and target-label matches.
2. Verify frozen-run provenance with `nine_class_validation_diagnostic.verify_inputs()`; do not load model weights or run inference.
3. For each linked original image, verify its split SHA-256, decode with OpenCV, convert BGR to RGB, and call the existing `measure_rgb` function using the current IQA config thresholds. Recheck the file hash after measurement.
4. Define correctness from the saved predicted/true class equality; run two-sided asymptotic Mann-Whitney U tests, rank-biserial effect sizes, and global Benjamini-Hochberg adjustment.
5. Recreate tables and plots from `IQA_LINKED_PER_IMAGE.csv`; verify every output using `IQA_MANIFEST.sha256`.

No prediction probabilities were analyzed for calibration or uncertainty; they are retained in the linkage table solely as saved prediction provenance.
