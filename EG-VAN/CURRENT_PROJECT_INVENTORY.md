# EG-VAN current project inventory

**Audit date:** 2026-10-13 (Asia/Calcutta). **Project:** `D:\Cancerdetection\EG-VAN`.

## Scope and evidence standard

This is a read-only inspection of the current local tree, except for creation of this document. Counts are filesystem counts; CSV distributions were computed from the named files; image properties were decoded from the first 30 sorted files per collection using Pillow. No preprocessing, training, model inference, tests, downloads, or package installation was performed. **VERIFIED** means directly inspected now. **INFERENCE** is identified explicitly. **UNVERIFIED** means neither runtime nor external source verification was performed. Historical prose in `PROJECT_STATUS.md` and `models/frozen_stage23/FREEZE_README.md` is treated as a claim, not proof of present files.

## Current folder structure and storage

The tree below collapses image collections and 200 PH2 case directories. Counts and sizes include all descendant files and use bytes, not allocated disk blocks. Evidence: recursive filesystem enumeration of `D:\Cancerdetection\EG-VAN` on the audit date.

```text
EG-VAN/ [42,265 files; 21,016,551,162 bytes]
├── app/ [3; 9,787 B] inference.py, streamlit_app.py, __init__.py
├── checkpoints/ [1; 81,652,547 B] efficientnetv2s_leakage_aware_best.pt
├── data/ [42,194; 20,926,518,778 B]
│   ├── raw/ [20,035; 5,673,685,503 B] HAM metadata, four hmnist CSVs
│   │   ├── HAM10000_images_part_1/ [5,000 JPG]
│   │   ├── HAM10000_images_part_2/ [5,015 JPG]
│   │   └── images/ [10,015 JPG copies]
│   ├── processed/ [10,037; 1,272,216,933 B]
│   │   ├── images/ [10,015 JPG]
│   │   └── preprocessing_samples/ [20 JPG]
│   ├── splits/ [2; 703,101 B] split_naive.csv, split_leakage_aware.csv
│   ├── external/ [1,114; 822,141,228 B]
│   │   ├── PH2Dataset/ [453 files] 200 case folders: dermoscopy, lesion masks, some ROI masks
│   │   └── ph2/ [661 files]
│   │       ├── images/ [200 BMP plus .gitkeep]
│   │       ├── metadata/ [6 files] manifest, clinical text/XLSX, provenance and verification reports
│   │       └── original/ [453 files] PH2 package copy, 200 case folders
│   └── isic/ [11,006; 13,157,772,013 B]
│       ├── ISIC-2017_Training_Data/ [2,000 JPG, 2,000 superpixel PNG, metadata CSV]
│       ├── ISIC-2017_Validation_Data/ [150 JPG, 150 superpixel PNG, metadata CSV]
│       ├── ISIC-2017_Test_v2_Data/ [600 JPG, 600 superpixel PNG, metadata CSV]
│       ├── *_Part1_GroundTruth/ [2,750 segmentation PNG total]
│       ├── *_Part2_GroundTruth/ [2,750 feature JSON total]
│       └── three *_Part3_GroundTruth.csv files at isic/ root
├── external_validation/ [1; 2,552 B] ph2_validation_plan.md
├── logs/ [0; empty]
├── manuscript/ [18; 8,148,786 B] two Markdown files and submission/plos_one package
├── models/ [5; 28,998 B] frozen_stage23/ registry, manifest, loader, verifier, README
├── notebooks/ [1; 10,575 B] phase4c_gpu_smoke_test.ipynb
├── src/ [21; 99,169 B] pipeline modules, models/egvan/, explainability/
├── tests/ [17; 58,081 B] Python test files
├── .gitignore, build_splits.py, prepare_metadata.py, PROJECT_STATUS.md
└── CURRENT_PROJECT_INVENTORY.md [created by this audit; excluded from pre-write counts]
```

Direct evidence for sizes by major data folder: `data/raw` 5,673,685,503 B; `data/processed` 1,272,216,933 B; `data/external` 822,141,228 B; `data/isic` 13,157,772,013 B; `data/splits` 703,101 B. Empty-folder check found only `logs/` empty. `data/external/ph2/original/` and `data/external/PH2Dataset/` each have 453 files and 278,583,151 B; matching clinical text hashes were checked, but complete package equality was not hashed.

Major-folder purposes, based on actual contents: `app/` holds the local Streamlit UI and inference adapter; `checkpoints/` holds one baseline-named model file; `data/` holds datasets, processed outputs and split CSVs; `external_validation/` holds a PH2 plan; `logs/` is empty; `manuscript/` holds research/submission text and figures; `models/` holds only Stage 23 freeze metadata/loader code; `notebooks/` holds one Colab notebook; `src/` holds pipeline and architecture code; `tests/` holds Python tests. The tree gives each folder's exact path relative to the project path above, descendant file count, size, important contents, and empty status.

## Data inventory and class distributions — VERIFIED

| Collection and evidence | Distinct clinical images | Format / inspected dimensions and channels | Metadata and labels |
|---|---:|---|---|
| HAM10000 `data/raw/HAM10000_images_part_1`, `_part_2` | 10,015 | JPG; first 30 from each part: 600×450 RGB | `data/raw/HAM10000_metadata.csv`: 10,015 rows; `lesion_id,image_id,dx,dx_type,age,sex,localization` |
| HAM raw copy `data/raw/images` | 10,015 copies | JPG; first 30: 600×450 RGB | Same filenames as original parts; **all 10,015 pairs have equal SHA-256** |
| HAM processed `data/processed/images` | 10,015 outputs | JPG; first 30: 600×450 RGB | `data/processed/metadata_clean.csv`: 10,015 rows with same columns and row values as raw metadata; first ten processed files have different SHA-256 from raw |
| ISIC 2017 `data/isic` Training / Validation / Test_v2 Data | 2,000 / 150 / 600, total 2,750 | JPG; first 30 per split RGB, varying dimensions: training 1022×767 or about 1504×1129; validation/test range includes 1024×768 through 4288×2848 | Each Data directory has `image_id,age_approximate,sex` CSV. Three Part3 CSVs have `image_id,melanoma,seborrheic_keratosis`. |
| PH2 `data/external/ph2/images` | 200 | BMP; first 30 RGB, varying around 761–769×553–577 | `data/external/ph2/metadata/ph2_manifest.csv`: 200 rows; `image_id,image_path,clinical_code,external_label,ham_label,included`. |

HAM `dx` counts in both raw and cleaned metadata: **nv 6,705; mel 1,113; bkl 1,099; bcc 514; akiec 327; vasc 142; df 115**. Each metadata ID has a source JPG, processed JPG, and entry in each split file. The 10,015-row preprocessing log reports 10,015 `success` entries, and every recorded input and output path exists (`data/processed/preprocessing_log.csv`). There are 57 blank `age` values in both metadata files; no blank `dx` values. These checks establish files and log entries, not pixel-level quality for all 10,015 images.

| HAM split CSV (`data/splits/`) | Train | Val | Test | Unique lesions | Lesions crossing partitions |
|---|---:|---:|---:|---:|---:|
| `split_leakage_aware.csv` | 8,015 | 986 | 1,014 | 7,470 | 0 |
| `split_naive.csv` | 8,010 | 998 | 1,007 | 7,470 | 764 |

Both split CSVs have 10,015 rows and `image_id,lesion_id,dx,split`. Their total `dx` distribution equals the HAM metadata distribution. Leakage-aware train/val/test distributions, respectively: akiec 257/30/40, bcc 398/58/58, bkl 891/104/104, df 95/9/11, mel 899/107/107, nv 5366/663/676, vasc 109/15/18. Naive distributions: akiec 261/32/34, bcc 411/51/52, bkl 879/109/111, df 92/11/12, mel 890/111/112, nv 5364/670/671, vasc 113/14/15. Evidence: both CSVs, joined by image ID to `data/processed/images`.

ISIC Part3 ground truth uses two indicator columns; the mutually exclusive derived counts are Training: melanoma 374, seborrheic keratosis 254, other 1,372; Validation: 30/42/78; Test_v2: 117/90/393. Every Part3 image ID has a JPG in its corresponding Data directory. “Other” is a derivation from both indicators being zero, not a source diagnosis label. The ISIC tree also has 2,750 superpixel PNGs, 2,750 segmentation PNGs and 2,750 feature JSONs; these are annotations, not extra clinical photographs. No ISIC-specific loader or training entry point was found in `src/`.

PH2 clinical counts in the local manifest are common nevus 80, atypical nevus 80, melanoma 40. `included=true` covers 120 cases (80 common nevus mapped to HAM `nv`, 40 melanoma mapped to `mel`); atypical nevus 80 are excluded by the current mapping (`ham_label` blank). All 200 manifest image paths and all 200 flat BMPs exist. The preserved PH2 package in `data/external/ph2/original/PH2 Dataset images` contains 200 dermoscopic BMPs, 200 lesion-mask BMPs, and 50 ROI BMPs; `data/external/PH2Dataset` contains another 453-file package. **All 200 flat/original dermoscopic BMP pairs match SHA-256.** First 30 lesion masks decode as 1-bit images. PH2 source and allowed-use claims are recorded in `data/external/ph2/metadata/provenance.json` and `verification_report.json`; the original clinical text agrees by SHA-256 across the three local PH2 metadata/package copies. **UNVERIFIED:** external publisher identity and all-file hash equality between the two complete 453-file PH2 package copies were not independently checked.

No additional standalone binary classification dataset was found under `data/`. The only binary-target material inspected is PH2’s 120-case mapped subset and ISIC 2017 indicator labels. No nine-class image manifest, nine-class split, or additional 3,297-image dataset exists in the current `data/` tree. This is a filesystem finding, not a claim about possible external sources.

## Preprocessing outputs — VERIFIED

`src/preprocessing.py` defines `remove_hair` (blackhat threshold and Telea inpainting), `gray_world`, `retinex` (three Gaussian scales and per-channel normalization), and `preprocess_image` in that order. Its `main` discovers JPGs in the two HAM source parts, processes a deterministic sample, then optionally writes 10,015 outputs and `preprocessing_log.csv`. Current outputs are 10,015 JPGs in `data/processed/images` and 20 JPGs in `data/processed/preprocessing_samples` (ten original/sample images and ten before/after comparisons). The log claims full success; current file existence and ten processed-vs-raw hashes support that the sampled outputs are distinct. The audit did not rerun preprocessing or decode every output. No offline augmented image folder was found; random flip/rotation exists only in the training transform (`src/train.py:make_transforms`).

## Source-code inventory and important functions

All paths below are relative to this project. Status is **static inspection only** unless evidence is explicitly cited. Imports are summarized by principal third-party dependency; Python standard library is omitted where obvious.

| File / category | Purpose, important API, inputs → outputs, dependencies | Static status / nine-class reuse |
|---|---|---|
| `prepare_metadata.py`, `src/prepare_metadata.py` / metadata | Root `load_metadata`, `image_file_exists`, `main` validate HAM CSV and JPG IDs, write cleaned CSV; `src` file delegates with `runpy`. CSV → cleaned CSV. | Present; 10,015-row output exists. Tied to HAM columns and paths; extend schema/label mapping for nine classes. |
| `build_splits.py`, `src/build_splits.py` / splitting | Root split logic uses CSV/random; `src` wrapper delegates via `runpy`. Metadata → two split CSVs. | **Broken now:** `build_splits.py:203` contains `print(f"[BLOCKED] {exc}")+`, causing `SyntaxError`; wrapper inherits failure. Existing split files remain present. Nine-class source/lesion protocol would need redesign. |
| `src/preprocessing.py` / preprocessing | `remove_hair`, `gray_world`, `retinex`, `process_one`, `main`; OpenCV/NumPy; original HAM JPG → processed JPG/log. | Implementation present and outputs exist; hardcodes HAM source folders and 10,015 count. Algorithms potentially reusable after new input policy; output provenance must stay separate. |
| `src/dataset.py` / loading | `validate_split_integrity`, `HAM10000Dataset`; CSV and processed JPG → `(Tensor, class_index)` via PIL/PyTorch. | Present; fixed seven-element `CLASS_NAMES`. Needs nine-class label map, source-aware paths and new split schema. |
| `src/models/baseline_effnet.py` / baseline architecture | `build_model`; torchvision EfficientNetV2S → classifier with `NUM_CLASSES=7`. | Present; `num_classes` is an argument, but callers/metrics remain seven-class. |
| `src/models/egvan/efficientnet_branch.py` / architecture | `EfficientNetBranch`; torchvision EfficientNetV2S feature taps 2/3/5/7 → four feature maps (48/64/160/1280 channels). | Present; class-independent, reusable if pretrained-weight and shape policies are verified. |
| `src/models/egvan/modified_resnet50.py` / architecture | `ModifiedResNet50`; torchvision ResNet50 stages plus `SCGA` at first two and `NonLocalBlock` at last two → 4 maps (256/512/1024/2048). | Present; class-independent. |
| `src/models/egvan/spatial_attention.py`, `scga.py`, `non_local.py`, `mff.py` / architecture | `SpatialAttention`, `GroupMeanMaxAttention`, `SCGA`, `NonLocalBlock`, `MFF`; PyTorch spatial/group attention, nonlocal q/k/v, paired-scale fusion → feature maps. | Present; class-independent, subject to shape and numerical validation for any new experiment. |
| `src/models/egvan/egvan.py`, `__init__.py` / architecture | `EGVAN.forward_features` runs two branches and four serial MFFs; `forward` pools aggregate → logits. Imports component modules. | Present; default `num_classes=7` but constructor accepts ≥2; nine-class head possible with new mapping/training protocol. |
| `src/train.py` / baseline configuration | `set_seed`, `focal_loss`, `make_transforms`, `build_run_components`, optimizer/scheduler configuration. PIL/NumPy/PyTorch/torchvision; split CSV → model/datasets. | **Partial:** no executable epoch loop or `main` here; hardcodes 384 px and seven-class baseline through `build_model`/dataset. |
| `src/run_baseline.py` / baseline training | `run_epoch`, `metrics_from_confusion`, `main`; train/val/test loaders, CUDA loop, best/final checkpoint and metrics JSON. | Implemented in code; not run during audit. Requires CUDA and third-party packages. Rework seven-class metrics/dataset for nine classes. |
| `src/evaluate.py` / baseline evaluation | `evaluate_checkpoint`, `main`; existing checkpoint/split/processed images → accuracy, macro F1, recalls, confusion matrix JSON. | Implemented statically; no runtime evaluation performed. Uses seven-class dataset/head. |
| `src/external_eval.py` / external evaluation | `read_clinical_labels`, `audit_manifest_rows`, `checkpoint_audit`, `audit_project`, `run_evaluation`, `main`; PH2 manifest, clinical text, baseline checkpoint → audit and optional CUDA predictions/metrics. | Data paths exist; caller must supply a compatible checkpoint. The one local baseline-named checkpoint was not deserialized or checked against this evaluator. Strict seven-class checkpoint shape and PH2 two-label mapping; not a generic nine-class evaluator. |
| `src/image_quality.py`, `src/run_quality_analysis.py` / quality | `compute_image_quality` proxies; `build_quality_table`, `summarize`, `model_error_analysis`; OpenCV/NumPy/Matplotlib, processed images/split/checkpoint → CSV/plots. | Present, not run; optional checkpoint path must be supplied. Seven-class constants and `class_count=7`. |
| `src/run_uncertainty_analysis.py` / uncertainty | `entropy`, `calibration_bins`, `selective_prediction`, `postprocess_saved_outputs`, `run_inference`; saved predictions or checkpoint → summaries/plots. | Present, not run; checkpoint required and seven-class shape/order checks. |
| `src/explainability/gradcam.py` / explainability | `gradcam` computes target-layer gradient heatmap from a model/input/target class. PyTorch → heatmap. | Present; no standalone driver found in current `src/`. Reusable with appropriate nine-class target and layer. |
| `models/frozen_stage23/load_frozen.py`, `verify_freeze.py` / frozen model | Registry/hash verification, `load_classifier`, `predict_rgb_image`, verifier CLI; registry/checkpoint/policy → model and predictions. | **Referenced but missing dependencies:** selected checkpoint and policy module under absent `experiments/` and `analysis/`; current load cannot complete. Hardcoded seven-class order/output. |
| `app/inference.py`, `app/streamlit_app.py` / app | `load_pipeline`, `analyze_image`, Streamlit `main`; upload → frozen-model prediction/Grad-CAM/uncertainty view. | Present statically, but loader depends on missing frozen artifacts. Seven-probability shape and entropy divisor `log(7)`. |
| `notebooks/phase4c_gpu_smoke_test.ipynb` / notebook | 6 code and 2 Markdown cells; Colab Drive mount, GPU check, baseline batch/optimizer smoke flow. | Present; hardcoded `/content/drive/MyDrive/EG-VAN`, Colab/CUDA dependent; not executed. |
| `tests/*.py` / tests | 17 files covering EG-VAN modules, paper alignment, external PH2 paths, app, quality/uncertainty, and one nine-class shape contract. | Files present; not executed. `tests/test_nine_class_shape_contract.py` is untracked; its presence is not a nine-class dataset/training implementation. |

`src/models/egvan/egvan.py` is the actual dual-branch implementation. `src/train.py` and `src/run_baseline.py` instead build the plain EfficientNet baseline (`src/models/baseline_effnet.py`). A full EG-VAN experiment training script is absent from the current tree because `experiments/` is absent. The one local checkpoint in `checkpoints/` is named for the baseline; its internal state was not deserialized.

## Actual pipeline dependency map and status

| Stage | Actual entry point and dependencies | Status from current evidence |
|---|---|
| HAM ingestion/metadata | `prepare_metadata.py` → raw HAM CSV/JPG → `data/processed/metadata_clean.csv` | **IMPLEMENTED; output present**, execution not repeated |
| HAM preprocessing | `src/preprocessing.py` → source parts → `data/processed/images`, log, samples | **IMPLEMENTED; outputs present**, full pixel verification not done |
| Split creation | `src/build_splits.py` → root `build_splits.py` → `data/splits/*.csv` | **BROKEN CURRENT ENTRY POINT** due line 203 syntax error; old outputs present |
| Baseline loading | `src/dataset.py` → processed JPG and split CSV | **IMPLEMENTED STATICALLY; references exist** |
| Baseline initialization/forward | `src/models/baseline_effnet.py`; `src/train.py:build_run_components` | **IMPLEMENTED STATICALLY**; no model instantiated here |
| EG-VAN initialization/forward | `src/models/egvan/egvan.py` and four component modules | **IMPLEMENTED STATICALLY**; no current full-run entry point |
| Baseline training/validation/checkpoint | `src/run_baseline.py` → `src/train.py`, `src/dataset.py`, `src/evaluate.py` | **IMPLEMENTED STATICALLY**; one named baseline checkpoint exists; present runtime behavior unverified |
| Baseline test | `src/run_baseline.py` final test; standalone `src/evaluate.py` | **IMPLEMENTED STATICALLY**; no current test run or metrics file under active folders |
| PH2 external evaluation | `src/external_eval.py` → PH2 files/provenance + caller-supplied seven-class baseline checkpoint | **PARTIALLY IMPLEMENTED**; data present, checkpoint compatibility/runtime unverified; no current output folder |
| Frozen EG-VAN inference/app | `models/frozen_stage23/load_frozen.py` → app modules | **REFERENCED BUT MISSING** checkpoint and policy code |
| Explainability | `src/explainability/gradcam.py`; app calls explanation path | **PARTIALLY IMPLEMENTED**; no standalone current driver, app loader blocked |
| Nine-class training/evaluation | No current data manifest, split, or training entry point | **NOT FOUND** |

## Missing and broken references — VERIFIED

- `build_splits.py:203` is invalid Python syntax; `src/build_splits.py` calls it via `runpy`, so the current split-generation entry point is broken. This was found with `ast.parse`, without running the script.
- `models/frozen_stage23/model_registry.json` and `load_frozen.py` require `experiments/stage23_resnet50_imagenet_init_exp1/run/best_checkpoint.pt`; the entire `experiments/` directory is absent. `load_frozen.py` also imports `analysis/stage13_melanoma_ablation/stage13c_abc_selective_qk_fp32_gate.py`; `analysis/` is absent. The freeze's pinned source-artifact references therefore cannot all resolve.
- `data/external/ph2/README.md` references `docs/PHASE_5_PH2_EXTERNAL_VALIDATION_REPORT.md` and `docs/PROJECT_DOCUMENTATION.md`; `docs/` is absent. `PROJECT_STATUS.md` also references absent `docs/`, `analysis/`, and `experiments/` items. These are documentary references, not evidence that those folders currently exist.
- `models/frozen_stage23/FREEZE_README.md` references `analysis/final_model_freeze/evaluation_boundary_audit.md`; absent with `analysis/`.
- The PH2 manifest paths currently exist. The PH2 evaluator's expected original package (`data/external/ph2/original/PH2 Dataset images`) also exists; no broken PH2 image reference was found in the checked manifest.

## Seven-class assumptions and reuse

Explicit seven-class definitions/checks occur in `src/dataset.py:CLASS_NAMES`, `src/models/baseline_effnet.py:NUM_CLASSES`, `src/models/egvan/egvan.py:EGVAN.__init__` default, `src/run_baseline.py` confusion matrices, `src/run_quality_analysis.py:CLASS_NAMES` and `f1_macro` default, `src/run_uncertainty_analysis.py` class/shape checks, `src/external_eval.py` checkpoint shape and mapping, `models/frozen_stage23/load_frozen.py` fixed output/order, and `app/inference.py` probability/entropy checks. The current HAM split CSV contains only seven `dx` values. Class-independent attention, fusion, preprocessing functions, quality proxies, and Grad-CAM can be reused at the code level; nine-class work would still need verified new image sources and labels, a source-aware manifest/split, updated classifier and loss/metrics, and separate evaluation provenance. This is a reuse assessment, **not** evidence that a nine-class pipeline exists.

## Repository and environment — VERIFIED / UNVERIFIED

- Git repository top level is `D:/Cancerdetection`; checked-out branch is `main` tracking `origin/main`. Read-only `git -c safe.directory=D:/Cancerdetection` was necessary because Git reported dubious ownership; no Git configuration was changed. Before this document: porcelain status had **1 modified tracked file** (`EG-VAN/PROJECT_STATUS.md`), **2,224 deleted tracked files** (mostly absent historical `analysis/`/`experiments/` artifacts), and **2 untracked paths** (`EG-VAN/data/isic/`, `EG-VAN/tests/test_nine_class_shape_contract.py`). These changes predated this audit. The current `src/`, `app/`, model modules, root Python scripts and frozen-model files yielded no `git diff --name-only` output. This documents the checked-out commit comparison; it does not restore or explain deletions.
- No root `README.md`, `requirements.txt`, `pyproject.toml`, or `environment.yml` exists in this project. `.gitignore` and `PROJECT_STATUS.md` do exist. `Python 3.10.11` resolves to `E:\AgenticAiCourse\python3.10\python.exe`; `PIL`, `torch`, `torchvision`, `cv2`, `numpy`, `pandas`, `matplotlib`, `sklearn`, `streamlit`, and `openpyxl` were discoverable through `importlib.util.find_spec`, but versions/import compatibility and CUDA availability were **not verified**. Notebook config expects Colab Drive and GPU.
- Drive D: reported **16,810,647,552 free bytes** (about 15.66 GiB) and 157,286,395,904 total bytes through `.NET DriveInfo`; `Get-Volume` itself was denied access. The Markdown write is small relative to reported free space. Project file sizes total about 19.57 GiB before this document.

## Unverified items and final factual summary

**UNVERIFIED:** full decode integrity of every image; all hashes between the two 453-file PH2 package copies; processed-versus-raw hashes beyond the ten sampled HAM pairs; independent external dataset provenance; exact checkpoint contents; package versions/CUDA; any runtime training, evaluation, app, or model forward pass; source of the missing historical tracked artifacts; whether images across different datasets are semantically duplicate photographs. The first 30 image-property samples per collection are not whole-collection dimension claims. Local provenance JSON records claims but does not independently establish external source identity.

**Final factual summary:** The current tree contains the complete 10,015-ID seven-class HAM data/processed/split set, 2,750 ISIC 2017 clinical photographs with segmentation/features, and 200 PH2 dermoscopic cases with local copies. It contains baseline and dual-branch EG-VAN architecture code, baseline training/evaluation code, quality/uncertainty/Grad-CAM utilities, and one named baseline checkpoint. The split builder currently has a syntax error; the frozen Stage 23 loader points to absent experiment and analysis files. No nine-class dataset or end-to-end nine-class pipeline is present. The next useful action is to decide the intended nine-class data source and protocol only after reviewing this inventory; this audit made no such changes.
