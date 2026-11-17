# R9 independent validation

Independent recalculation from saved files completed; no model code, checkpoint, or inference was used.

- Validation predictions: 1028 unique rows; probability vectors finite, nonnegative, normalized, and argmax-consistent. Recomputed accuracy=0.610894941634, macro-F1=0.097532366085, weighted-F1=0.471723925092, balanced accuracy=0.118353347345; all match saved metrics within 1e-12. Recomputed 9x9 confusion matrix exactly matches both JSON and CSV.
- Uncertainty: ECE=0.043081792354, multiclass Brier=0.517668953417, NLL=1.151326639323, mean confidence=0.582376376577, entropy=1.241405753324; error-detection AUC/AP match saved tables within 2e-8.
- IQA: 1028 unique linked rows; 14 features; 0 non-finite feature values; 628 correct/400 incorrect. Recomputed 42 Mann–Whitney tests and global BH values; overall q<0.05=9, all eligible q<0.05=13. Core saved values reproduced.
- Source image hashes: 1028 validation images independently match their linked SHA-256. Key checkpoint/split/provenance and prediction artifacts were rehashed before/after synthesis; 1044 files unchanged.
- Prior package manifests: 8 (R2F, R3, R4, R6, R7, IQA, uncertainty, R8) independently checked; every listed hash passed. R8's Windows path separators were normalized for comparison; R4's existing manifest omits `R4_VALIDATION.md` (reported as an inherited coverage gap, not repaired).
- R8 evidence confirms 300 candidate images, 7,028 retrieval relations, and zero external model evaluations. R6/R7 counts are sourced from their verified reconciliation/batch packages; no new human decisions inferred.
- All source references in `METRIC_PROVENANCE_REGISTER.csv` exist. The generated tables include dataset/partition, sample count, experiment ID, source file, status, and limitation for every metric row.
- No source image, label, split, checkpoint, or prior experiment package was modified.
