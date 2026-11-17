# EG-VAN consolidated comparative analysis

**Status: EXPLORATORY / NON-CLINICAL.** This evidence synthesis does not approve the cohort, establish leakage-safe validation, claim clinical validity, or reproduce the EG-VAN paper. No training, fine-tuning, new inference, or dataset/split modification was performed for this package.

## 1. Research objective

Consolidate existing evidence about the nine-class EG-VAN reconstruction and its saved exploratory validation, image-quality/error association, uncertainty/calibration, and external-validation feasibility. All experiment outputs remain at their original locations; this package references and hashes them rather than modifying or copying them.

## 2. EG-VAN implementation summary

The implementation audit records a dual branch comprising EfficientNetV2-S and a modified ResNet50, SCGA spatial/group attention, non-local attention blocks, four Multi-Feature Fusion blocks, and a nine-class head. The existing synthetic architecture probe checks tensor shapes and finite gradients; it does not demonstrate paper-exact implementation or image performance. The run provenance records random initialization, no initialization hashes, raw resize/ImageNet normalization, a 384-pixel input, Adamax, focal loss, microbatch 8, gradient accumulation 4, CUDA AMP when available, and 25 planned epochs. The run's training history is not linked to the checkpoint run directory, so epoch-by-epoch training claims are not made here.

The architecture audit flags paper ambiguities in feature taps, group count, non-local details, fusion width/carry/aggregation, attention parameter count, augmentation, and nine-label data construction. The modified ResNet body parameter count in the local implementation differs from the paper's stated same-parameter-count claim. Paper fidelity remains partial (`R2F_FINAL_ASSESSMENT.md`; `R3_EGVAN_ARCHITECTURE_AUDIT.csv`).

## 3. Existing model performance

The saved validation artifact contains **1028** source-labeled records, with **628 correct** and **400 incorrect**. Independently recalculated accuracy is **0.610895**, macro-F1 **0.097532**, weighted-F1 **0.471724**, and balanced accuracy **0.118353**. The checkpoint SHA-256 is `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08` and the validation split SHA-256 is `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740`.

Predictions are highly concentrated: NV is predicted **1012 / 1028 (98.4%)**. The model gets 624/629 NV records correct, but recalls are zero for AKIEC, BKL, DF, MEL, VASC, and BENIGN; BCC recall is 3/49 and MALIGNANT recall is 1/84. The confusion matrix is preserved in the original validation artifact and tabulated in `MODEL_PERFORMANCE_SUMMARY.csv`. Thus accuracy alone obscures severe class collapse and is not evidence of useful nine-class discrimination.

## 4. IQA experiment

The later dedicated IQA experiment links the frozen validation predictions to raw-image v2 quality proxies for **1,028 images**, with 0 missing values across 14 features. It found 628 correct and 400 incorrect rows. Across 14 unadjusted overall feature comparisons, **9** passed the saved global Benjamini-Hochberg q<0.05 screen. Across all **42** eligible overall and within-class tests, **13** had q<0.05; the within-class signals came from NV (four) because only BCC and NV had at least two cases in both correctness groups.

For orientation, `color_cast_range` had rank-biserial effect 0.399 (q=1.66e-25); `underexposed_fraction` had effect -0.320 (q=1.02e-20). These are observational associations, not causal quality effects. The exploratory model predicts NV overwhelmingly, image-quality features can differ by class/source, and repeated overlap groups make nominal tests non-confirmatory. IQA values are raw-image engineering proxies, not validated clinical image-quality scores. See `IQA_RESULTS_SUMMARY.csv` and original per-image/plot files.

Earlier, separate descriptive preprocessing artifacts must not be conflated with the v2 prediction-linked analysis: Stage 7 has 9 images/18 raw-versus-processed measurements (`analysis/nine_class_stage7/descriptive_sample_1_per_class/iqa_features.csv`, v1); Stage 10 has 26 images/104 measurements across four preprocessing variants (`analysis/nine_class_stage10/preprocessing_summary.json`). Neither stage links image quality to classifier error.

## 5. Uncertainty and calibration

Existing saved probabilities—not new inference—were used for the later uncertainty experiment. Independent recalculation from the 1,028 probability vectors gives 10-bin equal-width top-label ECE **0.0431**, multiclass Brier **0.5177**, NLL **1.1513 nats**, mean confidence **0.5824**, and mean predictive entropy **1.2414 nats**. Error-detection AUROC was **0.798** for normalized entropy, **0.787** for 1-confidence, and **0.771** for 1-top-two-margin. Entropy's average precision was **0.660**, against error prevalence **0.389**.

At the retrospective confidence threshold >=0.8, 310/1,028 rows (30.2%) were retained and observed accuracy was 95.8%; at >=0.9, 36/1,028 (3.5%) were retained and all were correct. These are not selected, validated, or safe operating thresholds. ECE is top-label and binning-dependent; classwise prediction collapse dominates its interpretation. The four-way split has 1,023 calibration-partition records but no saved predictions there and remains unapproved; no temperature scaling was fit. MC dropout was not run and is not supported by this model. Cluster-bootstrap intervals use recorded source/overlap groups whose independence is unverified.

## 6. External-validation feasibility

External model evaluation was **not performed**. R8 screened 200 PH2 and 100 SIIM–ISIC 2020 pilot images against the internal inventory, finding 7,028 perceptual candidate relations: 580 PH2 and 6,448 SIIM. There were 167 images with candidates and 133 without a candidate; no exact hashes or verified-identifier matches were found. Candidate retrieval is not human identity adjudication. PH2 supports only a candidate NV/MEL subset, has 80 unsupported atypical nevi, no patient IDs, source-version byte-linkage limits, and documented prior legacy use. The SIIM pilot has 82 unknown detailed diagnoses, 17 nevus and one seborrheic keratosis; its task-level negative was not relabeled as EG-VAN BENIGN. ISIC-2017 metadata has no corresponding local image files by ID. None supplies an approved all-nine-class external cohort. The Stage 9 evaluator's approvals remain absent.

## 7. Comparative interpretation

The strongest supported empirical statement is that this particular unapproved validation artifact yields moderate overall accuracy but very low macro-F1/balanced accuracy because its predictions are concentrated in NV. The saved probabilities also rank errors above chance in this partition, and the raw-image IQA proxies show statistically detectable unadjusted associations with correctness under the experiment's Mann–Whitney/BH procedure. Those results are internally reproducible from saved artifacts, but remain exploratory because of unapproved cohort construction, unresolved identity/overlap, source/class confounding, repeated groups, and extreme classwise sample/prediction imbalance. Statistical significance in this artifact is not confirmatory evidence of generalizable effects.

## 8. Limitations and validity threats

- Every research record remains not approved; validation is exploratory only, with no approved protected test or leakage-safe evaluation.
- The validation artifact contains 1,028 records, including 192 repeated overlap-group values covering 429 rows; source/patient independence remains unverified.
- R6 reports 9 human-confirmed SAME_PHOTO, 10 DISTINCT, 2 UNCERTAIN and 428 unreviewed queue relationships. Thus 430 duplicate-candidate relationships remain unresolved (428 unreviewed plus 2 uncertain); 471 source-test conflicts are separate and remain unresolved. R7 produced another blank decision template, not new human decisions.
- The source set is imbalanced, and predictions collapse to NV. The BENIGN/MALIGNANT source labels are not demonstrated to be mutually exclusive clinical diagnoses or interchangeable with HAM labels.
- Source provenance/rights are incomplete for parts of the local Fanconic-like data; 84 validation records lack recorded source image, lesion and patient IDs. PH2/SIIM limitations are described in R8.
- Paper fidelity is incomplete: exact data lineage/splits, binary-label construction, augmentation transforms and several architectural/training details are unresolved. The paper's reported accuracy/F1 are paper claims, not reproduced results.
- IQA features are proxies and the inferential tests are confounded by source/class mixture and dependence. Uncertainty/calibration are validation-only, with no independent calibration set; no temperature fitting or threshold validation exists.
- There is no eligible full-nine-class external validation and no clinical validity claim.

## 9. Contributions supported by evidence

1. A substantial nine-class EG-VAN-style implementation exists, with synthetic architecture/gradient evidence and a frozen exploratory checkpoint.
2. The exploratory validation's classwise failure mode is documented transparently with exact confusion counts.
3. Existing saved predictions support reproducible retrospective IQA association and uncertainty/error-ranking analyses without retraining or inference.
4. A local external-source inventory and candidate-overlap screen identifies concrete PH2/SIIM/ISIC-2017 mapping, rights, identity, and approval blockers.

These are engineering and exploratory research contributions, not clinical or paper-reproduction claims.

## 10. Recommended next research steps

1. Resolve source identity, label semantics, use rights, duplicate candidates, and all 471 source-test conflicts; update human decisions only from auditable human evidence.
2. Obtain an independently reviewed, source/version-pinned all-nine-class dataset and construct an explicitly approved patient/lesion/photo-group-safe train/validation/calibration/test split.
3. Resolve paper questions with the original authors/source maintainers: exact class composition, source versions, split membership, augmentation definitions/counting, and architecture/training ambiguities.
4. Freeze a calibration partition with its own approval and provenance before any temperature fitting; predefine error-detection/abstention analyses.
5. Only after approvals, run a new gated training/evaluation protocol and external evaluation on a genuinely independent, label-compatible cohort. Do not reuse the current exploratory validation as a protected test.

The requested evidence tables and hashes are bundled with this report; no full research-paper manuscript is created.
