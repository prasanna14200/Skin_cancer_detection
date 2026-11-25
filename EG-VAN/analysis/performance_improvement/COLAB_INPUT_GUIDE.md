# EG-VAN Colab GPU Training — Input and Execution Guide

**Status: EXPLORATORY / NON-CLINICAL / NOT APPROVED**

Notebook: `analysis/performance_improvement/EG_VAN_COLAB_GPU_TRAINING.ipynb`

The notebook has not been run in Colab. No GPU training, benchmark duration, or
new model result is claimed.

## 1. Drive setup

The notebook mounts Drive in its **first code cell** and directly uses:

```text
/content/drive/MyDrive/EG-VAN
```

Your uploaded folder must retain the project structure, including `src/`,
`config/`, `data/`, and `analysis/`. No ZIP extraction or file upload variables
are required. The notebook stops if the expected folder or required files are
missing.

Notebook-generated files are isolated under
`/content/drive/MyDrive/EG-VAN/colab_runs/egvan_gpu_training/`. The results ZIP
is written directly into `colab_runs/`. Other content already in `colab_runs/`
is neither overwritten nor included in this notebook's archive.

## 2. Inputs verified by the notebook

Required source files:

- `src/models/egvan/egvan.py`
- `src/nine_class_dataset.py`
- `src/nine_class_metrics.py`
- `src/nine_class_training.py`
- `src/nine_class_exploratory.py`
- `src/nine_class_evaluation.py`
- `src/nine_class_stage4.py`

Required data/configuration:

- `analysis/nine_class_stage4/nine_class_source_manifest.csv`
- `analysis/nine_class_exploratory/exploratory_split.csv`
- `analysis/nine_class_exploratory/exploratory_provenance.json`
- `config/nine_class_preprocessing_raw_v2.json`
- `config/nine_class_training_t4_four_way_v2.json`
- The actual image files addressed by the source manifest.

Relative image paths are first resolved from the uploaded project root. If the
manifest uses dataset-relative paths instead, they are resolved from its `data/`
directory. The notebook does not guess by filename or silently skip missing
images. It compares split rows with the source manifest, verifies all image
files and hashes, checks labels/indexes, and stops if required classes or files
are missing or invalid.

The optional baseline is already in the uploaded project at:

```text
analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt
```

Random initialization is the default. Enabling the historical baseline requires
its recorded SHA-256, strict state-dictionary load, and provenance/configuration
checks to pass. The original checkpoint is never overwritten.

## 3. Execution order

In Colab, choose **Runtime → Change runtime type → T4 GPU**, then run cells from
top to bottom:

1. Mount Drive and confirm the project and `colab_runs/` paths.
2. Verify Python, PyTorch/Torchvision compatibility, dependencies, CUDA, GPU and
   available resources. The notebook stops if CUDA is unavailable.
3. Check required source, config, manifest, provenance and dataset paths.
4. Verify every manifest and split image, source-defined label, class index,
   format and SHA-256.
5. Audit the existing split and write a separate grouped development split under
   `colab_runs/`. It unions available lesion, patient, overlap-group and exact
   image-hash links. The original split CSV and test partition are not edited;
   the old test partition is excluded and never evaluated.
6. Build the actual nine-class EG-VAN model and perform a CUDA forward/backward
   smoke test. No pretrained weights are downloaded.
7. Initialize the existing `NineClassDataset` with the verified preprocessing
   configuration.
8. Review the separate CE, weighted-CE, weighted-sampling and focal variants.
9. After checking flags and GPU capacity, run the selected training experiment.
   The runner benchmarks a microbatch and saves resumable checkpoints after
   every epoch.
10. Set `SELECTED_CHECKPOINT` to the chosen run's `best.pt` and run the
    development-validation evaluation.
11. Export the research checkpoint, metrics, class mapping and preprocessing
    metadata.
12. Package the outputs and download the ZIP.

No experiment runs by default. Keep `RUN_TRAINING=False` and
`AUTHORIZE_EXPLORATORY_TRAINING=False` until the checks above pass. To train,
explicitly enable both and run Cell 8. Review its rough training-only duration
estimate, then set `CONFIRM_TRAINING_AFTER_BENCHMARK=True` and run Cell 9. Start
with `MAX_EPOCHS_OVERRIDE=1`; use `None` for the configured 25 epochs only if the
measured GPU runtime is acceptable. The duration estimate excludes validation,
data I/O and checkpoint overhead.

## 4. Editable run settings

The project and output roots are intentionally fixed to the uploaded Drive
folder and `/content/drive/MyDrive/EG-VAN/colab_runs/`. Other settings are in
the notebook's configuration cells:

| Variable | Purpose |
|---|---|
| `CREATE_NEW_DEVELOPMENT_SPLIT` | Must remain `True`; a separate grouped split is required |
| `DEVELOPMENT_VAL_FRACTION` | Development-validation target fraction |
| `MICROBATCH` | T4 baseline microbatch (8) |
| `ACCUMULATION` | Gradient accumulation (4) |
| `EPOCHS` | Read from the checked training config (25) |
| `RUN_TRAINING` | Enables real GPU training |
| `AUTHORIZE_EXPLORATORY_TRAINING` | Explicit opt-in; required with training |
| `CONFIRM_TRAINING_AFTER_BENCHMARK` | Must be set after reviewing the Cell 8 duration estimate |
| `SELECTED_EXPERIMENTS` | `A_ce`, `B_weighted_ce`, `C_weighted_sampling`, `D_focal` (default: `D_focal`) |
| `EXPERIMENT_RUN_ID` | Unique run folder name; change it for a fresh run |
| `MAX_EPOCHS_OVERRIDE` | Use `1` for the initial benchmark; `None` for configured epochs |
| `RUN_RESUME` | Resume the exact run from its `last.pt` |
| `RESUME_CHECKPOINT` | Exact Drive path to that run's `last.pt` |
| `SELECTED_CHECKPOINT` | Best checkpoint frozen for validation/export |
| `RUN_FINAL_TEST` | Must remain `False`; the historical test is not approved |

## 5. Training and resume

Every run is saved under:

```text
/content/drive/MyDrive/EG-VAN/colab_runs/egvan_gpu_training/experiments/<experiment>/<run-id>/
```

Each completed epoch atomically saves `last.pt`; an improved checkpoint is
saved as `best.pt`. The history is checkpointed and written to
`training_history.csv`. Resume checks the experiment ID, run fingerprint,
development split, preprocessing and exact checkpoint path before restoring
model, optimizer, scheduler, AMP scaler, data-loader generator and RNG state.
Gradient accumulation weights microbatches by their sample counts, including a
partial final window.

To resume after disconnection:

1. Re-run cells 1–8 so Drive, integrity checks, grouped split and model/data
   configuration are reconstructed.
2. Keep the same experiment, `EXPERIMENT_RUN_ID`, seed, split, preprocessing,
   microbatch and accumulation values.
3. Set `RUN_TRAINING=True`, `AUTHORIZE_EXPLORATORY_TRAINING=True`, and
   `RUN_RESUME=True`, and `CONFIRM_TRAINING_AFTER_BENCHMARK=True`.
4. Set `RESUME_CHECKPOINT` to
   `/content/drive/MyDrive/EG-VAN/colab_runs/egvan_gpu_training/experiments/<experiment>/<run-id>/last.pt`.
5. Run the training cell. Resume one experiment at a time; do not resume from
   `best.pt`.

Use a new `EXPERIMENT_RUN_ID` for a new experiment. Existing run contents are
not silently overwritten.

## 6. Evaluation and outputs

Only the separate development-validation set is evaluated for model selection
and reported by default. The existing exploratory test partition remains
untouched and unevaluated; setting `RUN_FINAL_TEST=True` raises an error.
Results are exploratory, non-clinical, and not an exact EG-VAN paper
reproduction. No 80% target is claimed unless measured metrics support it.

All experiment outputs are under:

```text
/content/drive/MyDrive/EG-VAN/colab_runs/egvan_gpu_training/
```

The result ZIP is written directly to:

```text
/content/drive/MyDrive/EG-VAN/colab_runs/EG_VAN_COLAB_RESULTS.zip
```

If that ZIP already exists, the notebook creates a timestamped ZIP instead of
overwriting it. The archive contains only this notebook's output subfolder.
Where applicable, it includes checkpoints, per-epoch history,
development split, metrics JSON, confusion matrix CSV/PNG, classification
report, validation predictions and probabilities, class/preprocessing/model
configuration, experiment register, and checkpoint SHA-256.

The exported checkpoint is a research artifact, **not automatically accepted
by the existing Streamlit inference loader**. That loader is pinned to a frozen
checkpoint hash and verified run provenance; do not use a new export for public
inference without separate validation and an explicit loader change.

## 7. Files to upload back for verification

Upload the ZIP or, at minimum:

- `checkpoint_sha256.txt`
- `best_model.pt` and the corresponding run's `best.pt`/`last.pt`
- `model_config.json`, `class_mapping.json`, and `preprocessing_config.json`
- `metrics.json`
- `training_history.csv`
- `validation_classification_report.csv`
- `validation_confusion_matrix.csv` and `.png`
- `validation_predictions.csv` and `validation_probabilities.csv`
- `experiment_register_<run-id>.csv`
- `development_split.csv`

Do not upload credentials or unrelated Drive files. Independently validate the
checkpoint hash, state-dictionary load, class order, preprocessing, split
provenance and probability output before presenting results.
