# Stage 6 training and evaluation readiness

Date: 2026-10-22. This is a **prepared system, not a training result**. The nine-class source-defined label order is `AKIEC, BCC, BKL, DF, MEL, NV, VASC, BENIGN, MALIGNANT`. The dataset decision is in [Stage 6 dataset resolution](NINE_CLASS_STAGE6_DATASET_RESOLUTION.md). As of this audit, no approved eligible cohort or final split exists, so full training and nine-class final evaluation are blocked.

## Paper-informed configuration and local choices

The architecture is the Stage 5 nine-logit EG-VAN factory. The [versioned configuration](../config/nine_class_training_v1.json) sets `(3, 384, 384)` input, batch size 32, Adamax at initial learning rate 0.001, focal loss, and 25 epochs as the paper-informed target. These settings do **not** establish exact paper reproduction; see the [Stage 5 paper-to-code audit](NINE_CLASS_STAGE5_ARCHITECTURE.md) for unresolved architecture details. The following are explicit local implementation choices: scalar focal alpha 0.25 and gamma 2; random initialization by default; optional independently supplied local branch weights; seed 42; optional inverse-frequency class weights from the approved *training* rows only; `ReduceLROnPlateau` on validation loss (factor 0.5, patience 2); gradient norm clip 1; CUDA mixed precision when available; early stopping disabled by default (optional, patience 5). All can be reviewed in the JSON before any run. No pretrained weights are downloaded.

For multiclass focal loss, the runner computes cross-entropy from **raw nine logits**, then applies `alpha × (1 − p_target)^gamma × cross_entropy` and optionally the normalized inverse-frequency weight for the target class. Class weights are based on the approved train partition only. Softmax is used only for reported probabilities. Stage 4's loader controls train-only random augmentation and deterministic validation/test transforms. The runner does not instantiate the test loader during training.

## Required cohort authorization and mechanical gate

There is intentionally no production approval file or split manifest. A future approved split CSV must preserve each Stage 4 inventory row's `image_path`, `source_dataset`, `original_label`, `class_name`, `class_index`, `image_id`, `lesion_id`, `patient_id`, `source_split`, `sha256`, `overlap_group`, and `duplicate_overlap_evidence_tier`, plus `provisional_eligibility_status=APPROVED_ELIGIBLE` and `split=train|validation|test`. An authorized inventory revision must be versioned if independent IDs or eligibility evidence change; the gate rejects silent alterations to locked source fields. The approval JSON must contain:

```json
{
  "approval_status": "APPROVED_BY_RESEARCHER",
  "approved_by": "actual reviewer identity",
  "approval_date_utc": "actual UTC timestamp",
  "adjudication_reference": "record of approved pair and eligibility decisions",
  "source_rights_reference": "record of verified source and image-use rights",
  "protected_test_policy_reference": "signed test-partition decision",
  "test_partition_frozen": true,
  "approved_split_sha256": "real SHA-256 of final split CSV",
  "source_inventory_sha256": "real SHA-256 of source inventory CSV"
}
```

This is a schema illustration, **not an approval**. A JSON file cannot independently prove that its declarations are true; the cited human and provenance records must actually exist. The training gate checks file hashes, image bytes and paths, labels and indices, per-row approval, nine classes in both train and validation, exact image-content duplicates, known and suspected overlap groups, available lesion/patient IDs, publisher source-test protection, and groups linked to any publisher test record in the inventory. It rejects synthetic fixture approvals in production. It does not infer independent patients from missing IDs. A protected test may be present in the split but is inaccessible to the training runner; final test evaluation additionally requires all nine classes in test and an explicit frozen-test declaration.

Full training also requires a frozen protected test containing all nine classes, though no test image is read during training. The current Stage 4 inventory has no `APPROVED_ELIGIBLE` rows or final split. Its `AI_*` evidence and proposed exclusions cannot be promoted to approval by the runner. [The read-only audit](../analysis/nine_class_stage6/dataset_readiness_audit.json) records this state and source hashes.

## Runner, checkpoints and evaluation

The [training runner](../src/nine_class_training.py) validates the cohort before model construction. Each new run uses a unique UTC plus UUID directory under `analysis/nine_class_stage6/runs/`. It writes `run_provenance.json`, `history.csv`, `last.pt`, and `best.pt`; the checkpoints carry model, Adamax, scheduler, scaler, epoch and metric state, plus config/manifest/approval and complete preprocessing-configuration hashes. `best.pt` is selected using validation loss only. A resume must point to that run's `last.pt`; its hashes must match the supplied config and cohort. Epoch-boundary reseeding makes data order and augmentation reproducible under a fixed environment. Bitwise identical results across different PyTorch/CUDA versions or hardware are not promised. Existing historical checkpoints are untouched.

The [evaluation command](../src/nine_class_evaluation.py) is separate. It checks checkpoint, run and cohort hashes and writes a fresh output directory with `metrics.json` and per-image `predictions.csv` (nine class probabilities). Metrics include accuracy, macro and weighted F1, per-class precision/recall/F1/support and a confusion matrix. Low class support is warned about. If any class is absent from test, the metrics function suppresses overall test accuracy and the final-test command refuses to run. The probabilities are available for a later calibration analysis; no calibration fit or held-out performance is claimed. Validation can be rerun for diagnostics; the frozen final test is reserved for one predeclared assessment after model selection.

## GPU handoff after cohort approval

Use a Python environment with compatible `torch`, `torchvision`, `numpy`, `pandas`, `Pillow`, `opencv-python`, `scikit-learn`, and `pytest` versions recorded in the run environment. Verify the Stage 4 loader's optional processing dependencies in its documentation. Mount the **approved** image tree, inventory, split CSV and approval JSON together at stable paths in Colab or Kaggle; keep mirrored Fanconic trees outside the manifest. Persist the run directory to durable storage between sessions. If local pretrained branch weights are authorized, mount them and set `initialization.mode=local` plus their local paths; do not request a network download. Record those weight files and their hashes.

Commands below are **future instructions only**. Run them from the project root after the dataset decision and approval are complete:

```powershell
$env:PYTHONPATH = "src"
python src/nine_class_training.py --approved-split PATH_TO_APPROVED_SPLIT.csv --approval PATH_TO_REAL_APPROVAL.json --inventory PATH_TO_APPROVED_INVENTORY.csv --validate-only
python src/nine_class_training.py --approved-split PATH_TO_APPROVED_SPLIT.csv --approval PATH_TO_REAL_APPROVAL.json --inventory PATH_TO_APPROVED_INVENTORY.csv --runs-root PATH_TO_PERSISTENT_RUNS
python src/nine_class_training.py --approved-split PATH_TO_APPROVED_SPLIT.csv --approval PATH_TO_REAL_APPROVAL.json --inventory PATH_TO_APPROVED_INVENTORY.csv --resume PATH_TO_RUN/last.pt
python src/nine_class_evaluation.py --approved-split PATH_TO_APPROVED_SPLIT.csv --approval PATH_TO_REAL_APPROVAL.json --inventory PATH_TO_APPROVED_INVENTORY.csv --checkpoint PATH_TO_RUN/best.pt --split validation --output-dir PATH_TO_NEW_VALIDATION_REPORT
python src/nine_class_evaluation.py --approved-split PATH_TO_APPROVED_SPLIT.csv --approval PATH_TO_REAL_APPROVAL.json --inventory PATH_TO_APPROVED_INVENTORY.csv --checkpoint PATH_TO_RUN/best.pt --split test --final-test --output-dir PATH_TO_NEW_FINAL_TEST_REPORT
```

For Linux notebooks, use `export PYTHONPATH=src` and the same Python commands. Set `--root` to the mounted project root if it differs from the checkout. A 58,087,667-parameter two-branch model with 384-pixel inputs can exceed a hosted GPU's available memory at batch 32; reduce only the configurable batch size after a synthetic resource check and record the deviation. No GPU peak memory or training duration has been measured. Resume from `last.pt` after interruption, with the same approved cohort and config. Preserve the entire run directory and environment details when exporting artifacts. A crash between checkpoint and CSV history writes may leave the final history row absent; checkpoint epoch and metrics remain authoritative when resuming.

## Stage 6 validation and readiness

The synthetic tests use a tiny linear model, synthetic tensors and temporary fixture manifests; they check focal gradients and optimizer steps, checkpoint and optimizer/scheduler restore, output metrics, label tampering, missing approval, unapproved rows, cross-split groups, publisher source-test use, and protected-test-linked groups. They never train on a clinical image. The Stage 4 and Stage 5 tests are run as regression checks. No actual run directory or clinical-data prediction report has been generated in Stage 6.

**Code readiness:** prepared and synthetic-tested. **Dataset readiness:** blocked by source identity, BENIGN adjudication, rights and eligibility approval. **Full training readiness:** no. **Final nine-class evaluation readiness:** no. The next research action is independent adjudication and a documented source/label decision, then an approved group-safe manifest with a meaningful protected BENIGN test cohort.
