# EG-VAN Showcase — Final 8-Page Validation

**Status:** EXPLORATORY / NON-CLINICAL

Completed: 2026-11-22

## Eight-page completion status

All eight pages are accessible in the Streamlit sidebar:

1. Home
2. EG-VAN Reconstruction Explorer
3. Image Prediction Demo
4. Image Quality Assessment
5. Uncertainty & Calibration
6. External Validation
7. Research Workflow
8. Results and Limitations

## Files created or modified

- `project_showcase/Home.py`
- `project_showcase/pages/4_Image_Quality_Assessment.py`
- `project_showcase/pages/5_Uncertainty & Calibration.py`
- `project_showcase/pages/6_External_Validation.py`
- `project_showcase/pages/7_Research_Workflow.py`
- `project_showcase/pages/8_Results_and_Limitations.py`
- `project_showcase/assets/style.css`
- `project_showcase/tests/test_showcase_data.py`
- `project_showcase/FINAL_8_PAGE_VALIDATION.md`

Existing reconstruction and prediction implementation files were preserved and
audited rather than rebuilt.

## Features completed

### 1. Home

- Project title, motivation, objective, architecture summary and research status.
- Navigation links to every other page.
- Actual exploratory accuracy: 61.09%.
- No 80.09% display or paper-accuracy claim remains.

### 2. EG-VAN Reconstruction Explorer

- Existing verified source architecture remains available.
- EfficientNetV2-S, modified ResNet50, SCGA, non-local, MFF and nine-class head
  remain source-verified and clearly differentiated from synthetic shape evidence.

### 3. Image Prediction Demo

- Genuine CPU loading of the frozen nine-class checkpoint.
- Strict state-dictionary validation and checkpoint hash display.
- JPEG/PNG upload, preview, predicted class, top three and nine probability bars.
- Real controlled validation-image inference remained functional.

### 4. Image Quality Assessment

- 14 proxy features and 1,028 linked samples.
- Correct/incorrect mean and median comparison.
- Global and BH-adjusted comparison results loaded from the original IQA CSV.
- 9 / 14 overall BH-significant comparisons and 13 / 42 eligible tests documented.
- Association, confounding and causal limitations are explicit.

### 5. Uncertainty & Calibration

- Saved-probability accuracy, ECE, Brier, NLL, confidence and entropy.
- Error-detection AUROC and average-precision tables.
- Fixed-confidence threshold data loaded from the original CSV.
- 310/1,028 at >=0.8 and 36/1,028 at >=0.9 operating-point summaries.
- No calibration fitting or MC dropout claim.

### 6. External Validation

- PH2, SIIM-ISIC 2020 and ISIC 2017 findings loaded from R8 inventory evidence.
- Clear feasibility/completed/not-performed/status cards.
- Rights, identity, overlap and label-blocker explanations.

### 7. Research Workflow

- End-to-end source-linked workflow.
- Implemented, experimentally evaluated, partial and blocked statuses.
- Technical file references and data-flow explanation.

### 8. Results and Limitations

- 61.09% accuracy, 9.75% macro-F1, 47.17% weighted-F1 and 11.84% balanced accuracy.
- 1,028 validation samples; 628 correct and 400 incorrect.
- Actual nine-class predicted-count distribution.
- NV concentration of 1,012/1,028 (98.4%).
- Comparative evidence, limitations and future-work section.

## Tests and outcomes

- Python syntax compilation: passed.
- Showcase tests: **10 passed**.
- Existing inference test: passed.
- Checkpoint strict load and real-image smoke inference: passed.
- Dependency check: no broken requirements.
- All eight desktop routes returned content with no traceback.
- Desktop 1280×900 verification reported no horizontal overflow.
- Mobile 390×844 verification reported no horizontal overflow on the saved
  prediction/mobile smoke test.
- The uncertainty page was corrected after a source-column mismatch and was
  revalidated successfully.

## Screenshot paths

- `project_showcase/screenshots/page1_home.png`
- `project_showcase/screenshots/page2_architecture.png`
- `project_showcase/screenshots/page3_prediction.png`
- `project_showcase/screenshots/page4_iqa.png`
- `project_showcase/screenshots/page5_uncertainty.png`
- `project_showcase/screenshots/page6_external_validation.png`
- `project_showcase/screenshots/page7_workflow.png`
- `project_showcase/screenshots/page8_results.png`
- `project_showcase/screenshots/overview_mobile.png`
- `project_showcase/screenshots/phase4_prediction_mobile.png`

## Checkpoint integrity

Verified checkpoint:
`analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt`

SHA-256:
`3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`

The strict state-dictionary load remained successful. No checkpoint file was
modified.

## Research evidence integrity

Verified validation predictions:
`analysis/nine_class_validation_diagnostics/EXPLORATORY_ONLY_VALIDATION_20261112T154709Z_1dca162c/validation_predictions.csv`

SHA-256:
`fb46054fa919de0b3f9774f2e6a97546900c2e0edbde584125e622cf253f1b96`

Verified validation metrics:
`analysis/nine_class_validation_diagnostics/EXPLORATORY_ONLY_VALIDATION_20261112T154709Z_1dca162c/validation_metrics.json`

SHA-256:
`032244ba2bf30d216a96bd7c262107ec7b3d3c1e6d7fc7485bc1fd1646e238a1`

No source image, split, dataset, checkpoint or experiment evidence was modified.

## Unresolved issues

- The research cohort remains unapproved.
- The validation split is not established as leakage-safe.
- Full nine-class external validation was not performed.
- Paper fidelity remains partial.
- Clinical validity is not established.
- Uncertainty thresholds remain retrospective, not safety thresholds.

## Performance Improvement Sprint

A resource-bounded nine-class performance sprint was audited and recorded in
`analysis/performance_improvement/`.

- The frozen checkpoint's validation accuracy remains 61.09%.
- The 80% target was not achieved.
- No improved or new checkpoint was produced.
- A CPU-only one-batch forward/backward smoke test passed, with finite gradients.
- No GPU was available and approximately 0.78 GB RAM was free at audit, so
  no uncontrolled 25-epoch CPU training run was started.
- The existing cohort and split remain NOT_APPROVED and are not treated as a
  protected test.
