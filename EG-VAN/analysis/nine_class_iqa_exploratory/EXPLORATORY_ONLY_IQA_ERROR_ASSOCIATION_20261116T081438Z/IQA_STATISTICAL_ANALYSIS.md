# IQA statistical analysis

**EXPLORATORY / NON-CLINICAL.** These analyses describe associations in a frozen, unapproved validation artifact. They are not clinical evidence, causal estimates, or confirmatory inference.

- Linked records: 1028; correct: 628; incorrect: 400; accuracy recomputed from saved rows: 0.610895.
- Feature missingness: 0 values across 14392 measurements.
- Two-sided asymptotic Mann-Whitney U tests ran for 42 comparisons total: 14 overall plus eligible class-feature pairs. Tests require at least two observations in both correctness groups.
- Per-class tests were possible only for: BCC, NV. Other classes have fewer than two correct or incorrect cases.
- Effect size: rank-biserial correlation (equivalent to Cliff's delta), oriented as P(feature_correct > feature_incorrect) minus P(feature_correct < feature_incorrect); positive values mean higher metric values among correct predictions.
- Benjamini-Hochberg correction was applied globally across every eligible overall and per-class test; q < 0.05 is a screening flag only. Repeated overlap groups and unverified patient independence make nominal p/q-values non-confirmatory.
- Overall metrics with global q < 0.05: 9 of 14. Per-class metrics with global q < 0.05: 4.
- Important confounding: correctness is strongly class-dependent, and class/source composition differs between correct and incorrect groups. These unadjusted associations cannot isolate an image-quality effect.

Top overall signals (ranked by global q; descriptive only):

| Feature | n correct / incorrect | Rank-biserial | p | BH q |
|---|---:|---:|---:|---:|
| color_cast_range | 628 / 400 | 0.399 | 3.95e-27 | 1.66e-25 |
| rgb_mean_r | 628 / 400 | 0.391 | 3.27e-26 | 6.87e-25 |
| dark_border_fraction | 628 / 400 | -0.267 | 6.23e-23 | 8.72e-22 |
| underexposed_fraction | 628 / 400 | -0.320 | 9.69e-22 | 1.02e-20 |
| dark_line_fraction | 628 / 400 | -0.321 | 3.89e-18 | 3.27e-17 |
| sharpness_laplacian_variance | 628 / 400 | -0.282 | 2.31e-14 | 1.62e-13 |
| overexposed_fraction | 628 / 400 | -0.218 | 8.32e-14 | 4.99e-13 |
| rgb_mean_g | 628 / 400 | -0.156 | 2.51e-05 | 0.000132 |

## Per-class interpretation

The saved classifier predicted NV for 1012 of 1,028 images. Only BCC and NV had at least two correct and two incorrect examples, so only those classes have within-class tests. All seven other classes lack a sufficient correct/error group for these tests.

No confidence, calibration, uncertainty, external-validation, or causal analysis was performed.
