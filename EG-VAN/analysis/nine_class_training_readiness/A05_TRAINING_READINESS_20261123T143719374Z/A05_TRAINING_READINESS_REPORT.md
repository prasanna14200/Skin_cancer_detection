# A05 — EG-VAN Training Readiness and Safe Pilot Preparation

**Generated:** 2026-11-23T14:37:19.374Z  
**Status:** `A05_SYNTHETIC_SMOKE_TEST_COMPLETE_NOT_APPROVED`  
**Actual-image training authorization:** **NO**  
**Approval checklist:** `NOT_APPROVED`; 0 approved eligible images; `approved_four_way_split=false`; all 7 checklist items are `OPEN`.

## Summary

The existing nine-class Stage 6 pipeline was audited and a separate fail-closed authorization launcher was added at `src/nine_class_authorized_training.py`, with focused synthetic tests. The current approval checklist was passed to that launcher with `--launch`; it exited 2 with an explicit `NOT_APPROVED` error and did not start Stage 6.

A one-step CPU smoke using generated random tensors passed output-shape, focal-loss, gradient, Adamax, frozen-BatchNorm, deterministic replay, and checkpoint round-trip checks. It is **not model training or dataset performance**. No actual skin-lesion image, source metadata, source label, split, or checkpoint was used or modified by the smoke. No actual-image training, inference, evaluation, or preprocessing occurred.

The required source permissions and researcher decisions are not established. The proposed authorization configuration intentionally has no permitted source IDs or approved partition record IDs. A technically functioning pipeline does not establish approval.

## Evidence inspected

- A04 feasibility report and source/class eligibility matrix.
- The 2026-11-22 dataset eligibility plan and pending decision tracker.
- A01 intended-use evidence and completed decision draft; A02 Fanconic evidence and conservative exclusion draft; A03 provenance evidence and proposed researcher decision draft.
- Frozen exploratory split, Stage4 source manifest, central approval checklist, Stage4 class mapping, and Stage6 training configuration.
- EG-VAN model/branch/fusion modules; dataset loader; Stage6 runner, protocol, metrics/evaluation and synthetic GPU smoke modules; focused tests.

A01's academic-research declaration is not dataset permission. A02's proposed exclusion of Fanconic is not legal clearance or an approval. A03's technical validation is not a researcher decision. No pending decision was treated as resolved.

## Source-level training eligibility

| Source | Documented records | In frozen exploratory split | Outside split | Current conservative classification | Actual-image training |
|---|---:|---:|---:|---|---|
| HAM10000 | 9,310 | 9,310 | 0 | `RESEARCHER_DECISION_REQUIRED`; image rights, exact local acquisition/version, and patient independence are not established | NO |
| Fanconic local unverified version | 845 | 845 | 0 | `NOT_ELIGIBLE_UNDER_CURRENT_ASSUMPTIONS`; exclude all 845 pending provenance, rights, label, and identity evidence | NO |
| SIIM-ISIC 2020 training v2 | 200 | 79 | 121 | `PROVISIONAL_NOT_APPROVED`; 79 remain provisional and 121 remain outside the frozen split | NO |

HAM: A03 supports local hash consistency and metadata-content correspondence for the original seven `dx` classes, but not exact upstream image-byte identity or per-image rights. Twelve A03 HAM decisions and three HAM tracker decisions are pending. A03 also reports no patient IDs, 13 R6 photo decisions with blank reviewer IDs, and 210 unreviewed candidates involving 181 frozen HAM IDs; these do not establish human reviewer identity or patient independence. The recorded `mel` class is not equated with general `MALIGNANT`.

Fanconic: the local folder label is not verified diagnostic provenance. No source version, applicable rights, or independent patient/lesion identity is established. The A02 draft recommends excluding all 845; this report preserves that assumption without treating the draft as a completed approval.

SIIM: the 79 records in the split retain only their provisional status. The evidence reports 41 `CC-BY` and 38 `CC-BY-NC` API license codes for those 79, while exact individual versions and the interaction with aggregate Challenge terms remain unresolved. The 121 outside-split records are not added to the cohort. Four SIIM tracker decisions and one global review decision remain pending.

The existing source/label/partition counts remain in A04's `A04_CLASS_COUNT_AND_PARTITION_SUMMARY.csv`; A05 did not regenerate counts or create a split. All nine classes have zero approved eligible records under the current checklist. A seven-class HAM-only scope might be considered after independent rights, provenance, identity, and researcher review, but it is not currently cleared or approved.

## Pipeline audit

- **Architecture:** dual EfficientNetV2-S and modified ResNet50 branches, SCGA/non-local attention, four paired MFF fusion scales, 128 fusion channels, and a nine-logit head; 58,087,667 trainable parameters. Default initialization is random. This is a local nine-output EG-VAN reconstruction/adaptation, not a verified exact reproduction of the paper's training setup or results.
- **Inputs and mapping:** 384x384 RGB; `raw_resize_imagenet_v2`; ImageNet mean `(0.485, 0.456, 0.406)` and standard deviation `(0.229, 0.224, 0.225)`. The loader preserves the fixed nine-class order and refuses missing images or mapping mismatches. No loader was run in A05.
- **Objective/optimizer:** focal loss (`alpha=0.25`, `gamma=2.0`; class weighting disabled), Adamax at `0.001`, gradient clipping at `1.0`, and `ReduceLROnPlateau` (`factor=0.5`, `patience=2`).
- **Batching/precision:** microbatch 8, gradient accumulation 4, nominal sample accumulation 32, CUDA-gated FP16, and frozen BatchNorm running statistics. Accumulation is not equivalent to physical batch-32 BatchNorm. Early stopping is disabled; configured maximum is 25 epochs.
- **Reproducibility/checkpoints:** seed 42 across Python/NumPy/Torch/CUDA; cuDNN deterministic enabled and benchmark disabled; epoch-seeded loader order. Run directories are unique; `last.pt` and `best.pt` are atomically saved with configuration/cohort hashes, optimizer/scheduler/scaler state, and RNG state. Resume is restricted to the run's `last.pt` at an epoch boundary. A mid-epoch interruption has no batch-level recovery checkpoint.
- **Evaluation/logging:** validation/test summaries include accuracy, macro-F1, weighted-F1, per-class precision/recall/F1/support, confusion matrix, and loss; final-test accuracy is withheld when a class is missing. Per-epoch history stores loss, accuracy, macro-F1, and learning rate; checkpoints retain full train/validation metric objects. Calibration and uncertainty analysis still require a separately approved calibration cohort and a defined procedure.
- **Hardware:** local PyTorch is CPU-only and CUDA is unavailable. Separate saved Tesla T4 evidence reports synthetic one-step 384x384 passes through microbatch 8 (4,262 MiB peak reserved for batch 8). It does not measure a full epoch, full-run duration, or approved-image training. Approximate FP32 parameter, gradient, and two Adamax-state storage alone is about 886 MiB, before activations and other allocations.

Detailed components, findings, source paths, and source SHA-256 values are in `A05_TRAINING_PIPELINE_AUDIT.csv`.

## Authorization safeguards and remaining limitation

The new launcher fails closed unless the checklist and four-way split are approved; the approved count and each partition are nonempty; source IDs and source rights/identity status are verified; all required researcher decisions are resolved; partition record IDs match the approved split and inventory; no record or identity crosses partitions; calibration/test records are not in training; and a researcher approval record binds the evidence hashes. Stage 6's existing approved-split validator then checks locked labels, image hashes, protected source-test groups, and class presence.

**Current-state verification:** with the real checklist and `--launch`, the launcher returned exit code 2: `TRAINING AUTHORIZATION BLOCKED: Approval checklist status is 'NOT_APPROVED'; expected APPROVED`. No training process was started.

The existing Stage6 runner remains directly callable and was not modified because it is a protected implementation. The new launcher is the designated safe entry point; this A05 change does not prevent a user from bypassing it by invoking Stage 6 directly. Do not bypass the launcher. The source change adds safeguards but does not confer any authorization.

## Synthetic-only smoke and test evidence

The direct smoke passed on CPU at batch 1 and 64x64, using only generated random tensors and label index 8. It verified finite nine-logit output/loss/gradients, an Adamax parameter update, unchanged frozen BatchNorm running statistics, exact fixed-seed forward replay, and the existing checkpoint save/load helpers. The temporary smoke checkpoint was removed. It does not validate the configured 384px CUDA/FP16 run.

- New authorization tests: exit 0; **9 passed**.
- Focused existing Stage6/shape/GPU-smoke tests: **17 passed, 1 failed, exit 1**. The failing exploratory-checkpoint test stopped while importing `nine_class_iqa.py`: `ModuleNotFoundError: No module named 'matplotlib'`. This environment dependency was not added to project manifests.
- Synthetic-only smoke details and limits: `A05_SYNTHETIC_SMOKE_TEST_RESULTS.md`.

The prior T4 synthetic report is separate historical evidence, not this run and not actual model training. No model-performance metrics are available.

## Proposed training configuration

This config is embedded to keep the A05 output directory to exactly five files. It is **not executable authorization**: all approved source/record lists are empty and all 23 tracked/A03 decision IDs remain pending. The SHA-256 is over canonical UTF-8 JSON (`sort_keys=true`, compact separators).

**Canonical configuration SHA-256:** `34680aa395f2b19b4efff3653f91b987abd0f4969b7014a5af9c682df4fdbeeb`

```json
{
  "schema_version": "nine_class_training_v2",
  "authorization_schema_version": "nine_class_training_authorization_v1",
  "split_protocol": "four_way_v1",
  "label_order": [
    "AKIEC",
    "BCC",
    "BKL",
    "DF",
    "MEL",
    "NV",
    "VASC",
    "BENIGN",
    "MALIGNANT"
  ],
  "architecture": "EG-VAN",
  "num_classes": 9,
  "fusion_channels": 128,
  "image_size": 384,
  "input_shape": [
    3,
    384,
    384
  ],
  "preprocessing_mode": "raw_resize_imagenet_v2",
  "normalization_mean": [
    0.485,
    0.456,
    0.406
  ],
  "normalization_std": [
    0.229,
    0.224,
    0.225
  ],
  "initialization": {
    "mode": "random",
    "efficient_local_state": null,
    "resnet_local_state": null
  },
  "permitted_source_ids": [],
  "approved_training_record_ids": [],
  "approved_validation_record_ids": [],
  "approved_calibration_record_ids": [],
  "approved_test_record_ids": [],
  "required_decision_ids": [
    "HAM-D01",
    "HAM-D02",
    "HAM-D03",
    "HAM-D04",
    "HAM-D05",
    "HAM-D06",
    "HAM-D07",
    "HAM-D08",
    "HAM-D09",
    "HAM-D10",
    "HAM-D11",
    "HAM-D12",
    "HAM-FILE-IDENTITY",
    "HAM-IMAGE-RIGHTS",
    "HAM-INTENDED-USE",
    "FAN-ORIGIN",
    "FAN-IMAGE-RIGHTS",
    "FAN-INTENDED-USE",
    "SIIM-TERMS-INTERACTION",
    "SIIM-INDIVIDUAL-VERSION",
    "SIIM-PACKAGE-IDENTITY",
    "SIIM-INTENDED-USE",
    "GLOBAL-REVIEW"
  ],
  "pending_researcher_decisions": [
    "HAM-D01",
    "HAM-D02",
    "HAM-D03",
    "HAM-D04",
    "HAM-D05",
    "HAM-D06",
    "HAM-D07",
    "HAM-D08",
    "HAM-D09",
    "HAM-D10",
    "HAM-D11",
    "HAM-D12",
    "HAM-FILE-IDENTITY",
    "HAM-IMAGE-RIGHTS",
    "HAM-INTENDED-USE",
    "FAN-ORIGIN",
    "FAN-IMAGE-RIGHTS",
    "FAN-INTENDED-USE",
    "SIIM-TERMS-INTERACTION",
    "SIIM-INDIVIDUAL-VERSION",
    "SIIM-PACKAGE-IDENTITY",
    "SIIM-INTENDED-USE",
    "GLOBAL-REVIEW"
  ],
  "optimizer": "Adamax",
  "learning_rate": 0.001,
  "focal_alpha": 0.25,
  "focal_gamma": 2.0,
  "class_weighting": false,
  "batch_size": 8,
  "gradient_accumulation_steps": 4,
  "batchnorm_policy": "freeze_running_stats",
  "mixed_precision": "cuda_if_available",
  "epochs": 25,
  "maximum_epochs": 25,
  "num_workers": 0,
  "seed": 42,
  "scheduler": {
    "name": "ReduceLROnPlateau",
    "factor": 0.5,
    "patience": 2
  },
  "gradient_clip_norm": 1.0,
  "early_stopping": {
    "enabled": false,
    "patience": 5
  },
  "checkpoint_directory": "analysis/nine_class_stage6/runs",
  "evaluation_metrics": [
    "loss",
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "per_class_precision_recall_f1_support",
    "confusion_matrix"
  ],
  "approval_gate_requirements": [
    "checklist_approved_and_four_way_split_frozen",
    "approved_eligible_image_count_positive",
    "approved_source_ids_nonempty_and_verified",
    "all_partitions_have_explicit_approved_record_ids",
    "no_record_or_identity_overlap_across_partitions",
    "no_calibration_or_test_records_in_training",
    "all_required_researcher_decisions_resolved",
    "hash_bound_researcher_approval_record",
    "Stage6_approved_split_and_image_hash_validation"
  ]
}
```

## Reproducibility and preservation

- Repository commit before A05 additions: `eb835aa5b33fd788fab60e9634bf2761ceb303f7`.
- Smoke runtime: CPython 3.10.16, PyTorch 2.14.0+cpu, torchvision 0.29.0+cpu, CUDA unavailable.
- Configuration hash: `34680aa395f2b19b4efff3653f91b987abd0f4969b7014a5af9c682df4fdbeeb`.
- A pre-change size/SHA-256 baseline covers **1,189 selected protected files**, including A01-A04 evidence, checklist, exploratory split, source manifests, model/training implementation, tests/configs, and existing checkpoints. Post-change comparison: **0 missing and 0 changed**. This is a selected protected-file comparison, not a dataset-wide integrity scan.
- The approval checklist remains `NOT_APPROVED`, with zero approved eligible images, `approved_four_way_split=false`, and all seven items `OPEN`. Existing checkpoints were unchanged. A01-A04 evidence was not overwritten.
- No source image was read for the smoke or focused tests. Test fixtures used generated tensors or synthetic temporary bytes. No existing checkpoint was overwritten; the temporary synthetic checkpoint was separate and removed.

## Blockers and exact next action

Actual-image training remains blocked by the non-approved checklist, zero approved records, absent approved source/partition IDs, 23 pending decisions, unresolved rights and attribution, unresolved HAM archive/version and metadata checksum, absent patient identities and unverified R6 reviewer identities, and provisional SIIM record terms/identity. No external validation was performed or supported by an eligible independent cohort. The A04 exploratory four-way split must not be used as an approved split.

**Next action:** researcher review and resolve the applicable source-specific decisions and evidence gaps; obtain documented rights/identity review; create a separately reviewed, hash-bound approved inventory and frozen four-way split; update the checklist and decision/source registers through the approval workflow; then populate the proposed config only with approved source and record IDs. After those conditions are met, run the new launcher in a CUDA-capable environment:

```powershell
python src/nine_class_authorized_training.py --config <approved-config.json> --approval-checklist <approved-checklist.json> --source-eligibility-register <approved-source-register.csv> --decision-register <resolved-decision-register.csv> --approved-split <approved-four-way-split.csv> --approval-record <hash-bound-approval.json> --inventory <approved-source-inventory.csv> --runs-root analysis/nine_class_stage6/runs --launch
```

Do not run that command with the current exploratory split or current approval state. No A05 action authorizes training.
