# Independent validation

**EXPLORATORY / NON-CLINICAL.**

## Independent verification result

Independent verification passed in a separate CPython 3.13 process:

- Rehashed all **10 source-evidence files**, including the frozen checkpoint and uncertainty implementation; every hash and file size matched the source register.
- Independently rehashed all **1,028 source images** and matched every digest to the frozen validation split and per-image output. The checkpoint hash still matches saved validation metrics.
- Confirmed exact unique 1,028-row source-qualified key matching across saved predictions, split, and linked output; labels and probability argmaxes matched.
- Recomputed accuracy (**628/1,028 = 0.6108949416**), 10-bin top-label ECE (**0.0430817924**), multiclass Brier (**0.5176689534**), probability NLL (**1.1513266393 nats**), mean confidence, entropy, class prediction counts, error AUROC/AP, reliability-bin counts, and fixed-threshold coverage from the underlying probability table.
- Verified all five plot files are readable PNGs and all reported classwise support/prediction/true-positive counts match source rows.
- Confirmed the calibration partition has **1,023 `NOT_APPROVED` records** and no saved prediction artifact. No calibrator was fit.

The final manifest covers every deliverable except itself to avoid recursive hashing.
