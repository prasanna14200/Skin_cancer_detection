# Reproducibility

Status: **EXPLORATORY / NON-CLINICAL**.

## Source evidence

`UNCERTAINTY_SOURCE_EVIDENCE.csv` records paths, byte lengths, and SHA-256 digests for the saved predictions and metrics, frozen split, checkpoint, run provenance, training config, uncertainty and diagnostic implementations, and R3/R4 audit documents. The checkpoint digest is `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`; the prediction digest is `fb46054fa919de0b3f9774f2e6a97546900c2e0edbde584125e622cf253f1b96`; the split digest is `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740`.

## Reproduction outline

1. Use the existing frozen diagnostic verifier to validate run provenance and checkpoint, config, split, source-preview, and preprocessing identities.
2. Join saved predictions to the frozen validation partition by `(source_dataset, image_path)`. Require unique complete keys, matching source labels, probability validity, and predicted-class argmax consistency.
3. Use `nine_class_uncertainty.validate_probabilities`, `uncertainty_from_probabilities`, `calibration_metrics(bins=10)`, `risk_coverage_curve`, and `selective_at_threshold` without loading the checkpoint for inference.
4. Compute one-vs-rest reliability and class summaries, error-detection ranking, and overlap-group cluster bootstrap intervals from the saved probabilities and split metadata.
5. Recompute file hashes from `UNCERTAINTY_MANIFEST.sha256`; validate the exact source inventory and image hashes against the saved per-image rows.

The probability-method runtime was CPython 3.10.16, NumPy 2.2.6, OpenCV 5.0.0, and PyTorch 2.14.0+cpu from the existing project site-packages. Plotting/statistical analysis used CPython 3.13.5, NumPy 2.1.3, pandas 2.2.3, SciPy 1.15.3, scikit-learn 1.6.1, and Matplotlib 3.10.0. No packages were installed.

Bootstrap intervals use 1,000 replicates, seed `20261116`, and source-qualified recorded overlap groups. The output manifest covers every deliverable except itself to avoid recursive hashing.
