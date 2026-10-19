# EG-VAN repository restructuring plan

Audit: 2026-10-19, `E:/Cancerdetection/EG-VAN`. This is a read-only plan. No files were moved, deleted, restored, or rewritten during this audit; this document is the only new file. The current project is inside the Git working tree rooted at `E:/Cancerdetection`, on `main`. Its configured `origin` is `prasanna14200/Skin_cancer_detection`, which is different from the requested [historical repository](https://github.com/prasanna14200/Skin_cancer_detection_using_dual_network). The latter was inspected through its GitHub contents API. Its `EG-VAN/` tree is historical evidence, not a description of the local working directory.

## Actual local tree and classification

Counts include descendant files. Sizes are logical file bytes, rounded; they do not measure allocated disk blocks or Git object storage. `KEEP` means required for the current research record or intended pipeline; `KEEP_OPTIONAL` means useful but not required to prepare nine-class data. No top-level folder has enough evidence to be called safe to delete.

| Local folder | Files | Size | Classification | Current contents and dependencies |
| --- | ---: | ---: | --- | --- |
| `data/` | 37,782 | 7.555 GiB | **KEEP** | HAM originals/metadata, binary source and mirror, PH2 external data, processed HAM images, preprocessing log, and frozen HAM split CSVs. Do not remove or relocate. |
| `src/` | 22 | 0.098 MiB | **KEEP** | Dataset, preprocessing, split wrappers, baseline training/evaluation, EG-VAN architecture, quality/external tools, and the unique perceptual-overlap audit script. Import paths assume this location. |
| `docs/` | 2 before this plan | 0.015 MiB | **KEEP** | Nine-class source/overlap audit and an empty preprocessing/split plan file. Preserve provenance conclusions. |
| `analysis/` | 2 | 5.07 MiB | **KEEP** | `nine_class_similarity/fingerprints.csv` and `candidates.csv`, the only local analysis files. These are research evidence, not disposable output. No local Python scripts are hidden here. |
| `tests/` | 17 | 0.055 MiB | **KEEP** | Architecture, nine-class shape, app, PH2, and historical Stage 23 tests. Several tests point to currently absent analysis/experiment artifacts. |
| `models/` | 5 | 0.028 MiB | **KEEP_OPTIONAL** | `frozen_stage23/` seven-class registry, source hashes, loader, verifier, README. Unique provenance record; loader currently cannot resolve its checkpoint and numerical-policy script. |
| `checkpoints/` | 1 | 77.87 MiB | **KEEP_OPTIONAL** | `efficientnetv2s_leakage_aware_best.pt`, a baseline-named checkpoint. Its training provenance and consumers should be checked before any storage action. |
| `app/` | 3 | 0.009 MiB | **KEEP_OPTIONAL** | Streamlit UI and inference adapter; depends on `models/frozen_stage23/` and its missing Stage 23 artifacts. |

Local root files: `.gitignore`, `PROJECT_STATUS.md`, `CURRENT_PROJECT_INVENTORY.md`, `prepare_metadata.py`, and `build_splits.py`. They are part of the working project and should remain in place. `configs/`, `experiments/`, `manuscript/`, `notebooks/`, `colab_artifacts/`, and `external_validation/` do **not** exist locally. There are no local archive candidates at the top level. Any future archive proposal for optional components needs its own dependency and backup review.

The Git working tree already reports 11,025 tracked deletions and six untracked paths at audit time, mostly under `data/`. Their origin and intent were not established; this plan does not treat Git status as authorization to restore or remove anything. The older `CURRENT_PROJECT_INVENTORY.md` describes folders that are now absent, so its historical tree is not a current inventory.

Nested-folder classification (all deeper case/image directories inherit their nearest listed parent's status):

| Existing subtree | Classification | Reason |
| --- | --- | --- |
| `data/raw/HAM10000_images_part_1/`, `_part_2/`, and raw metadata | **KEEP** | Original HAM source and identifiers. |
| `data/raw/images/` | **DUPLICATE_CANDIDATE** | Byte-identical copy of all 10,015 original HAM JPGs; still protected. |
| `data/raw/hmnist_*.csv` | **KEEP_OPTIONAL** | Derived HAM tabular representations; no current core loader uses them. |
| `data/isic/data/` | **KEEP** | Chosen canonical binary source and original train/test hierarchy. |
| `data/isic/train/`, `data/isic/test/` | **DUPLICATE_CANDIDATE** | Byte-identical mirror; explicitly protected. |
| `data/processed/images/`, `preprocessing_samples/`, logs and metadata | **KEEP** | Existing HAM derivatives and reproducibility evidence; consumers use `images/`. |
| `data/splits/` | **KEEP** | Frozen seven-class CSVs referenced by code, registry, and prior results. |
| `data/external/ph2/`, `data/external/PH2Dataset/` | **UNRESOLVED** | PH2 package/extracted or derived relationships not byte-audited; preserve both. Hundreds of per-image directories inherit this status. |
| `analysis/nine_class_similarity/` | **KEEP** | Unique audit evidence. |
| `src/models/egvan/`, `src/explainability/` | **KEEP** | Architecture and Grad-CAM imports. |
| `models/frozen_stage23/` | **KEEP_OPTIONAL** | Immutable seven-class research freeze record; currently missing external dependencies. |

## Historical GitHub versus local

The historical GitHub `EG-VAN/` contains `src/`, `data/`, `models/`, `tests/`, `docs/`, `analysis/`, `experiments/`, `manuscript/`, `app/`, `notebooks/`, `colab_artifacts/`, and `external_validation/`. Locally, `experiments/`, `manuscript/`, `notebooks/`, `colab_artifacts/`, and `external_validation/` are absent; `checkpoints/` is present locally but not a top-level folder in the historical GitHub listing. GitHub's `analysis/` has 43 direct entries and `experiments/` has 25, including unique code and configuration, not merely result files. Examples: `analysis/stage13_melanoma_ablation/stage13c_abc_selective_qk_fp32_gate.py`, `analysis/stage23_image_quality_final/analyze_quality.py`, `experiments/stage23_resnet50_imagenet_init_exp1/{initialization.py,train.py,config.json}`, and `experiments/egvan_reconstruction_controlled_exp1/train_colab.py`. These are **historical remote files**, not locally available scripts. The GitHub tree also contains a paper PDF at repository root; no PDF is present under the local project.

This comparison uses the [historical root tree](https://github.com/prasanna14200/Skin_cancer_detection_using_dual_network/tree/main/EG-VAN), [analysis tree](https://github.com/prasanna14200/Skin_cancer_detection_using_dual_network/tree/main/EG-VAN/analysis), and [experiments tree](https://github.com/prasanna14200/Skin_cancer_detection_using_dual_network/tree/main/EG-VAN/experiments). GitHub contents can change; no remote files were downloaded or restored. The configured local `origin` points to a separate repository whose current GitHub repository metadata reports no content size. Do not infer its contents from the historical URL.

## Protected code and dependency chain

The named architecture files all exist at their requested paths and must remain there. `efficientnet_branch.py` uses torchvision EfficientNetV2-S feature taps; `modified_resnet50.py` uses torchvision ResNet50 with SCGA on earlier stages and non-local blocks on later stages. `scga.py` calls `spatial_attention.py`; `mff.py` uses both attention components and paired branch maps; `egvan.py` joins four MFF outputs with terminal branch features, pools, and applies a linear classifier. Internal imports are relative to `src/models/egvan/`. This is an implemented dual-branch architecture, subject to existing paper-alignment/shape tests; it is not a completed nine-class experiment.

`EGVAN(num_classes=7)` is the current default. The constructor accepts `num_classes=9`, and `tests/test_nine_class_shape_contract.py` expresses a nine-output shape contract. The attention and fusion modules are class-count independent. The frozen Stage 23 registry, loader, and app are explicitly **seven-class**; the registry pins hashes of architecture files and `data/splits/split_leakage_aware.csv`. Altering those files or paths invalidates that freeze record.

`src/prepare_metadata.py` and `src/build_splits.py` delegate to the root scripts. The root metadata script reads HAM metadata and writes a HAM-only cleaned copy. The root split script is HAM-only and has a syntax error at its `print(...)+` line; it must not be reused unchanged for nine classes. `src/dataset.py` loads only seven HAM classes from `data/processed/images/` and the existing HAM split CSV. `src/preprocessing.py` deterministically applies hair removal, Gray World, and Retinex to HAM originals and writes the existing processed-image cache. `src/train.py` and `src/evaluate.py` train/evaluate a seven-class EfficientNetV2-S baseline, using PyTorch/torchvision/PIL/NumPy/OpenCV as applicable; they do not run the EG-VAN nine-class experiments. `src/models/baseline_effnet.py` has a configurable head, but its callers and metrics remain seven-class. The historical full EG-VAN experiment entry points under `experiments/` are missing locally.

Dependencies to protect: `data/raw/HAM10000_metadata.csv`, both `data/raw/HAM10000_images_part_*/` directories, `data/isic/data/` and its mirror, `data/processed/images/` and log, `data/splits/split_leakage_aware.csv` and `split_naive.csv`, `analysis/nine_class_similarity/`, `src/nine_class_similarity_audit.py`, `models/frozen_stage23/`, and `checkpoints/efficientnetv2s_leakage_aware_best.pt`. `src/run_quality_analysis.py`, `src/run_uncertainty_analysis.py`, `src/evaluate.py`, tests, and the frozen registry refer to processed images or the leakage-aware split. The selected Stage 23 checkpoint `experiments/stage23_resnet50_imagenet_init_exp1/run/best_checkpoint.pt` and numerical-policy module `analysis/stage13_melanoma_ablation/stage13c_abc_selective_qk_fp32_gate.py` are absent locally; app/frozen-model loading is incomplete. Do not substitute the baseline checkpoint.

## Data copies and disk space

Subdirectory sizes: `data/raw/` 5.284 GiB; `data/processed/` 1.185 GiB; `data/external/` 0.766 GiB; `data/isic/` 0.320 GiB; `data/splits/` below 1 MiB. Within raw data, `data/raw/images/` and the two HAM source parts each occupy about 2.580 GiB. The canonical binary `data/isic/data/` is 163.66 MiB and its top-level `train/` plus `test/` mirror totals another 163.66 MiB. The existing processed HAM image directory is 1,207.73 MiB. It is regenerable in principle from `src/preprocessing.py`, but exact regeneration depends on software versions and its bytes may underpin past results; classify it **KEEP**, not disposable.

`data/raw/images/` and the binary mirror are **DUPLICATE_CANDIDATES**, subject to the byte-level verification result below and explicit approval for any future storage change. `data/external/PH2Dataset/` and `data/external/ph2/` may represent package/extracted forms, but their relationship has not been byte-audited; classify both **UNRESOLVED/KEEP_OPTIONAL**, not redundant. Approximate theoretical duplicate storage is 2.58 GiB for a HAM copy plus 0.160 GiB for the binary mirror. **Approved immediate savings: 0 bytes**, because these paths are protected and no removal is authorized. Drive E: had about **49.4 GiB free** during this audit, sufficient for this plan document. Do not budget future training from these rounded figures.

## Nine-class compatibility and current scientific gate

HAM metadata has 10,015 seven-class entries. The canonical `data/isic/data/` has 3,297 folder-labeled benign/malignant entries, with one exact internal duplicate; its parallel tree is a mirror. The current [nine-class data pipeline audit](NINE_CLASS_DATA_PIPELINE.md) found extensive resized-image overlap with HAM10000: 1,926 high-confidence binaryâ€“HAM candidate pairs and 401 distinct binary source-test images with strong HAM matches. That creates mutually exclusive nine-class target conflicts and prevents a defensible combined split. The prior statement that cross-dataset review was still pending is obsolete.

Current code does **not** supply a validated combined nine-class metadata manifest, source-aware loader, duplicate/lesion-aware combined splitter, nine-class training entry point, or nine-class evaluator. Nine output logits are structurally configurable, but this alone is not nine-class readiness. The nine-class data target/provenance and overlap policy must be resolved before modifying these modules or constructing experiments. No patient independence can be claimed for the binary source.

## Minimal target structure and safe migration order

Keep the present import layout: `data/`, `src/`, `analysis/`, `tests/`, `docs/`, and essential root scripts/configuration. Keep `models/`, `checkpoints/`, and `app/` as separate optional historical/inference components; their current paths matter to the freeze metadata. Create `configs/` only if a verified nine-class protocol needs versioned settings. Create `experiments/` only when a new, separately named experiment is authorized, or restore specific historical artifacts through a provenance-checked process. Neither directory was created by this audit. Do not recreate `manuscript/`, `notebooks/`, `colab_artifacts/`, or `external_validation/` merely to match GitHub.

Safe order for a later approved change: (1) resolve the nine-class overlap/target problem; (2) identify the exact historical commit and review a complete backup or remote copy of any proposed archive target; (3) verify every dependent import, registry hash, split reference, and published-result reference; (4) stage one reversible move/copy at a time under new names without touching protected raw data; (5) run focused path/hash/loader checks; (6) only then evaluate a separate storage-reclamation proposal. No part of this migration was executed.

**Exact paths requiring user approval before any move, archive, restore, deletion, or overwrite:** `E:/Cancerdetection/EG-VAN/data/raw/images/`; `data/raw/HAM10000_images_part_1/`; `data/raw/HAM10000_images_part_2/`; `data/isic/data/`; `data/isic/train/`; `data/isic/test/`; `data/processed/`; `data/splits/`; `analysis/nine_class_similarity/`; `models/frozen_stage23/`; `checkpoints/`; `src/`; `app/`; `tests/`; and any historical `experiments/`, `analysis/`, or manuscript material proposed for restoration. Git metadata under `E:/Cancerdetection/.git/` is outside cleanup scope entirely. This list identifies review targets; it is not a recommendation to change them.

## Byte comparison result

The read-only SHA-256 comparison matched all **10,015** files in `data/raw/images/` byte for byte to files of the same name in the two HAM source parts; zero differed or lacked a matching name. It also matched all **3,297** canonical binary files to the corresponding path in the top-level `data/isic/{train,test}/` mirror; zero differed. These two copies are verified byte duplicates at audit time, but both remain protected. No PH2 byte comparison was made.

