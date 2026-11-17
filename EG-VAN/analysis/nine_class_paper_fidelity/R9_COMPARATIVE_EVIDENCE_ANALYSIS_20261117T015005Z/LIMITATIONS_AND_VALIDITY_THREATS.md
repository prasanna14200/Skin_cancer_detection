# Limitations and validity threats

## Cohort and reference-standard validity

- All nine-class records used by the saved model evaluation are exploratory and unapproved. No clinical-validation status, study approval, or leakage-safe research estimate is established.
- Source-defined `BENIGN` and `MALIGNANT` labels have not been proven equivalent to a single clinical taxonomy or mutually exclusive of the seven HAM diagnoses.
- 84 Fanconic-like validation records lack recorded source image, lesion, and patient IDs; path/hash linkage is not an identity bridge.
- Missing patient IDs and incomplete source-version/rights provenance affect independence and reproducibility claims.

## Leakage and dependence

- The validation artifact reports 192 repeated overlap-group values covering 429 rows. Their dependence and relationship to source/test boundaries remain incompletely established.
- R6 records 9 SAME_PHOTO, 10 DISTINCT, 2 UNCERTAIN and 428 unreviewed queue relationships; 430 relationships remain unresolved. Its separate source-test inventory contains 471 unresolved conflicts.
- A zero known-group-crossings field or a no-candidate result cannot establish photographic or patient independence.

## Model and measurement validity

- Predictions are highly concentrated in NV (1,012/1,028); six classes have zero recall. Overall accuracy is therefore a misleading summary without macro-F1, balanced accuracy, per-class support, and confusion counts.
- The checkpoint uses random initialization according to run provenance. Architecture taps, attention/fusion settings, preprocessing, augmentation and paper data construction are only partially specified or differ from the paper.
- IQA measurements are 14 deterministic raw-image engineering proxies. They are not clinical quality labels, and associations cannot establish causality or image-quality mediation.
- IQA comparisons are vulnerable to class/source confounding, sparse within-class groups, repeated records, and image-level test assumptions. BH correction does not correct confounding or clustering.
- Calibration results are based on saved probabilities on one unapproved validation partition. ECE depends on binning; per-class predictions are sparse/collapsed. The separate calibration partition is unapproved and has no saved predictions.
- Cluster bootstrap intervals use recorded source/overlap-group clusters; correctness of those groups and patient independence are unverified. Image-level rank-test p-values are not cluster-adjusted.
- Confidence-threshold/risk-coverage points are retrospective and not validated safety thresholds. No temperature fitting, MC dropout, threshold optimization, or prospective selective-prediction study was performed.

## External and paper validity

- R8 screened candidate images but did not run external inference. PH2/SIIM mappings, rights, exact package versions, overlap adjudication, and internal approval do not support full-nine-class external validation.
- R8 pHash/dHash candidate retrieval is not a duplicate identity decision. All candidates remain unreviewed.
- Paper-reported 98.20% accuracy and 96.68% F1 are not project measurements. R2F/R3 document incomplete paper fidelity and unresolved source, split, augmentation, model, and count details.
- Older R3/R4 statements that no real IQA association or real-model uncertainty analysis existed predate the later dedicated packages. Those later outputs update evidence availability, but do not update approval or validity status.

## Scope of this synthesis

No training, fine-tuning, inference, dataset preparation, source-label change, split edit, checkpoint edit, or prior-package edit was performed. Statistical recalculation verifies arithmetic within saved exploratory artifacts; it does not upgrade the design or validate the cohort.
