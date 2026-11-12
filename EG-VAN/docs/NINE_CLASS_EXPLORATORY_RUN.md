# Run the real-image nine-label exploratory experiment

**Status: technically ready for a Tesla T4; clinical data remain unapproved. No model training has run locally or in Colab from this package.** This is a modified, nonclinical source-defined task. It is not an exact reproduction of the EG-VAN paper.

The separate [exploratory runner](../src/nine_class_exploratory.py) consumes only the existing [four-way planning preview](../analysis/nine_class_final_cohort/four_way_planning_assignment_v1.csv), which already excluded candidate-bearing SIIM records and Fanconic BENIGN. It preserves every `NOT_APPROVED` status. HAM's seven diagnoses are unchanged; SIIM 2020 `benign,target=0` supplies BENIGN; Fanconic's original `malignant` folder label supplies MALIGNANT. These are source-defined labels, not nine mutually exclusive diagnoses. No Stage 6 clinical gate or approved cohort file was changed.

The frozen [exploratory split](../analysis/nine_class_exploratory/exploratory_split.csv) has **10,234** real images: train **7,080**, validation **1,028**, calibration **1,023**, test **1,103**. BENIGN has only **55/8/8/8**; MALIGNANT has **512/84/84/165**. All nine labels appear in each partition. Known overlap groups, exact hashes, available lesion IDs and available patient IDs were checked for crossings; publisher source-test images remain in test. The [real-image preflight](../analysis/nine_class_exploratory/real_image_preflight.json) verified all 10,234 image hashes and decoded one image per class in each partition. The **79 SIIM no-candidate images are not proven independent**, and Fanconic patient IDs and rights remain unverified. Test estimates, especially BENIGN, will have high uncertainty and possible residual source/identity bias.

## Colab execution

Copy the complete current project to `/content/drive/MyDrive/EG-VAN`, including existing `data/raw/`, `data/isic/data/`, both SIIM image folders under `analysis/`, all planning CSVs, source attribution and code. Open [the executable Colab notebook](../notebooks/nine_class_exploratory_colab.ipynb) in a Tesla T4 runtime. It mounts Drive, probes CUDA/torchvision compatibility, checks actual source files, runs the real-image preflight, trains and evaluates. It does not download datasets or weights. Its code cells are intentionally **unexecuted**.

From a Colab terminal after mounting Drive, the exact commands are:

```bash
cd /content/drive/MyDrive/EG-VAN
python src/nine_class_exploratory.py prepare
python src/nine_class_exploratory.py preflight
python src/nine_class_exploratory.py train
```

The existing [T4 four-way config](../config/nine_class_training_t4_four_way_v2.json) fixes 384 px, microbatch **8**, accumulation **4** (effective 32), FP16 autocast and GradScaler, Adamax, focal loss, frozen BatchNorm running statistics, and **25 planned epochs**. Weights initialize randomly, with no pretrained download. Runs persist directly to Drive under `analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_*/`; `last.pt`, validation-selected `best.pt`, `history.csv` and run provenance are written after each completed epoch. To resume an interrupted run, supply its actual `last.pt`:

```bash
python src/nine_class_exploratory.py train --resume /content/drive/MyDrive/EG-VAN/analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_ACTUAL_RUN/last.pt
```

After training finishes, replace the run name with the one printed by the runner:

```bash
python src/nine_class_exploratory.py evaluate --checkpoint /content/drive/MyDrive/EG-VAN/analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_ACTUAL_RUN/best.pt --output-dir /content/drive/MyDrive/EG-VAN/analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_ACTUAL_RUN/evaluation
```

Evaluation writes real-image prediction CSVs, accuracy, macro-F1, macro precision/recall, per-class metrics, confusion matrix, curves, raw-image quality versus error, and uncertainty/calibration summaries. Temperature is fitted on calibration only; the exploratory test is evaluated once with the validation-selected checkpoint. A concise `EXPLORATORY_ONLY_final_report.md` is generated **only after actual checkpoint evaluation**. External validation is omitted because no eligible independent cohort exists. Neither the notebook nor this document contains fabricated results.
