# Nine-class EG-VAN: T4 evidence and conditional training handoff

Date: 2026-10-24. **Computational smoke passed; clinical training remains blocked.** This is a nine-output paper-aligned adaptation with fixed order `AKIEC, BCC, BKL, DF, MEL, NV, VASC, BENIGN, MALIGNANT`. No cohort, split, image or checkpoint was approved or changed for this report. The subsequent [dataset recovery decision](NINE_CLASS_DATASET_RECOVERY_DECISION.md) records the official 2020 metadata-only screen and current alternative-source route.

## Reproducible T4 evidence

The [source-preserving verifier](../analysis/nine_class_training_readiness/verify_gpu_results.py) checks the three saved JSON reports for Tesla T4 / PyTorch `2.11.0+cu130`, synthetic-only mode, `(B,3,384,384)` inputs, `(B,9)` outputs, FP16 autocast and GradScaler, finite focal loss and unscaled gradient norm, changed classifier weights, reset gradients, and unchanged BatchNorm running statistics. Its [summary](../analysis/nine_class_training_readiness/gpu_benchmark_verified.json) records source SHA-256 hashes and can be regenerated at a fresh output path. Original benchmark JSON files remain unchanged.

```bash
python analysis/nine_class_training_readiness/verify_gpu_results.py --output analysis/nine_class_training_readiness/gpu_benchmark_verified_repeat.json
```

| Batch | Saved report | Peak allocated MiB | Peak reserved MiB | Single step seconds | Focal loss | Unscaled gradient norm | Result |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `t4_batch1_001` | 1152.7 | 1184 | 7.280 | 0.494531 | 4.787318 | Passed |
| 2 | `t4_batch2_001` | 1226.1 | 1344 | 2.149 | 0.471173 | 3.049926 | Passed |
| 4 | `t4_batch4_8_001` | 2072.2 | 2332 | 3.114 | 0.418252 | 1.716106 | Passed |
| 8 | `t4_batch4_8_001` | 3804.6 | 4262 | 3.161 | 0.426674 | 1.345343 | Passed |

The batch-2 report also repeats batch 1 and records a 3.062-second step; the table uses the standalone batch-1 trial. All four recorded steps report finite logits/loss/gradients, a finite changed classifier, FP16/GradScaler, Adamax, and 167 BatchNorm modules with frozen running statistics. Step time includes input generation, forward, backward, optimizer work and CUDA synchronization; model setup is separate. These single steps include startup and are not reliable throughput estimates. The batch-8 report measured 14.36 GiB initially free and 4.16 GiB peak reserved, leaving more than the smoke script's 25%-plus-2-GiB headroom rule. This does not measure a full epoch, data loading, long-run allocator behavior or checkpoint I/O.

## Proposed T4 optimization config and Stage 6 audit

The new [T4 configuration](../config/nine_class_training_t4_v1.json) proposes **microbatch 8 × 4 accumulation = nominal effective batch 32**, 384-pixel input, raw-resize/ImageNet normalization, focal loss (`alpha=0.25`, `gamma=2`), Adamax (`lr=0.001`), CUDA AMP, gradient clip 1, and frozen BatchNorm running statistics. These are local choices; effective batch 32 does not recreate the running statistics of a true batch-32 forward. Frozen statistics on a randomly initialized model may affect convergence and need an approved-data validation pilot before they are treated as a good final policy. A different policy or microbatch needs a new versioned config and run; the config SHA-256 prevents resuming across such changes.

The existing [Stage 6 runner](../src/nine_class_training.py) already accumulates per-sample focal losses across microbatches, divides by the actual accumulated sample count including a short last group, unscales AMP gradients before division/clipping, steps Adamax once per group, and resets gradients. Existing synthetic equivalence tests cover accumulation; a new focused test covers the T4 config and frozen BatchNorm behavior. Validation runs in evaluation mode. The runner checkpoints model, optimizer, scheduler, GradScaler, provenance hashes and epoch metrics; `last.pt` supports epoch-boundary resume and `best.pt` follows validation loss. It does not resume a partial epoch. The explicit BatchNorm policy is the only training-loop addition made here; legacy configs default to their previous training-statistics behavior. The architecture and dataset gates were not changed.

The [Colab notebook](../notebooks/nine_class_colab_training.ipynb) remains guarded and defaults all train/evaluation flags to false. Its runtime probe now accepts a compatible CUDA build such as the measured `torch==2.11.0+cu130` when the installed torchvision backbones construct successfully, and it selects the 8×4 T4 config. This is a software compatibility check; actual execution in that Colab runtime remains to be verified. The T4 config and raw preprocessing have distinct hashes from the old setup.

## Dataset decision remains blocked

The [Stage 12 snapshot](../analysis/nine_class_stage12/readiness_snapshot.json) reports **0 of 19** protected BENIGN primary pairs independently reviewed, **101** additional candidate relationships (six protected records affected), **0 approved BENIGN train/test records**, **0 approved source inventory rows**, no production approval file and no approved split. Stage 11B's 19 `AUTO_SAME_PHOTO` primary classifications are automated evidence, not independent decisions. The Stage 10 bounds of 64 publisher-train and 19 publisher-test BENIGN cases are upper bounds, not approved counts. The Fanconic version, label provenance, image-level rights and missing patient/lesion identifiers remain unresolved. No BENIGN case or protected test can be inferred from the successful GPU smoke.

The production `validate_approved_split` gate checks approval references and hashes, image bytes, fixed labels, exact/overlap and known lesion/patient groups, and publisher test isolation. Full training additionally requires a frozen test containing every class. A signed record is still a research claim: software cannot prove a reviewer judgment or licensing right is true. The minimum research action is independent adjudication of the 19 protected primary pairs and their relevant additional relationships, followed by a rights/provenance decision and an approved, group-safe nine-class inventory/split with a meaningful protected BENIGN test. If those pairs remove the available BENIGN test cases, a documented compatible source is needed; no substitute is authorized here.

## Existing downstream research components

| Component | Ready software | Needs real approved artifacts |
| --- | --- | --- |
| [Image-quality assessment](NINE_CLASS_STAGE7_IQA.md) | Deterministic raw/processed proxies and source-hash checks; a bounded descriptive sample exists. | A complete approved cohort and Stage 6 predictions for quality-versus-error analysis. Proxies do not certify clinical image quality. |
| [Uncertainty and calibration](NINE_CLASS_STAGE8_UNCERTAINTY.md) | Nine-probability entropy/confidence, ECE/Brier/NLL, selective metrics and guarded analysis. | Trained checkpoint and held-out predictions. Temperature fitting additionally needs a separate approved calibration partition and logits; MC dropout is unsupported by the present architecture. |
| [External validation](NINE_CLASS_STAGE9_EXTERNAL_VALIDATION.md) | Manifest schema, overlap screen, independent approval gate, frozen-checkpoint inference, nine-label/subset reporting. | Internal approved checkpoint, rights-cleared compatible external source, overlap adjudication and frozen external test approval. No external performance exists. |

The Stage 10 `raw_resize_imagenet_v2` preprocessing candidate avoids the documented tonal reversal in the full Retinex path. It is an explicit adaptation, not proof of superior accuracy or exact paper preprocessing. Select preprocessing and report deviations using validation only; do not tune on the protected test.

## Conditional Colab checklist and commands

Run this **only after** the independent decisions, source rights, approved inventory, split and approval JSON exist. Mount a GPU runtime and Drive; upload the current source and keep runs on Drive. Check `torch`, `torchvision`, CUDA and GPU compatibility without replacing the working PyTorch installation. Confirm the T4 config and fixed label order; ensure `APPROVED_SPLIT`, `APPROVAL` and `INVENTORY` name genuine files. The placeholders below intentionally do not name files that do not exist today.

```bash
cd /content/drive/MyDrive/EG-VAN
export PYTHONPATH=src
python -c "import torch, torchvision; print(torch.__version__, torchvision.__version__, torch.cuda.get_device_name(0), torch.cuda.mem_get_info())"
CONFIG=config/nine_class_training_t4_v1.json
INVENTORY=/absolute/path/to/approved_source_inventory.csv
APPROVED_SPLIT=/absolute/path/to/approved_split.csv
APPROVAL=/absolute/path/to/genuine_approval.json
RUNS_ROOT=/content/drive/MyDrive/EG-VAN/analysis/nine_class_stage6/runs
python src/nine_class_training.py --root "$PWD" --config "$CONFIG" --inventory "$INVENTORY" --approved-split "$APPROVED_SPLIT" --approval "$APPROVAL" --runs-root "$RUNS_ROOT" --validate-only
```

Review the validated class counts, source-test boundaries, preprocessing hash, initialization mode and available VRAM before enabling the full command. A full run remains a separate, explicit action after approval:

```bash
python src/nine_class_training.py --root "$PWD" --config "$CONFIG" --inventory "$INVENTORY" --approved-split "$APPROVED_SPLIT" --approval "$APPROVAL" --runs-root "$RUNS_ROOT"
```

On interruption, use the same config and files with `--resume "$RUNS_ROOT/ACTUAL_RUN_DIR/last.pt"`; never reuse a checkpoint after changing batch/accumulation or cohort hashes. Evaluate `best.pt` on validation for model selection. Reserve `--split test --final-test` for the single predeclared final assessment after selection. The training command has **not** been executed.

## Verification and minimum remaining work

`python -m pytest tests/test_nine_class_stage6.py tests/test_nine_class_stage11b.py -q --disable-warnings` returned **14 passed**; the Stage 7–9 focused suite returned **18 passed**. The local Windows torchvision installation emitted an optional image-extension diagnostic and warning; both test runs exited successfully. `verify_gpu_results.py` passed against the saved T4 JSON and wrote the hash-bound summary. No architecture rebuild, dataset gate change, clinical training, external validation or checkpoint was performed. Remaining implementation work is a four-way calibration protocol if temperature fitting is approved; the current notebook probe must still be exercised on the actual Colab runtime after upload.
