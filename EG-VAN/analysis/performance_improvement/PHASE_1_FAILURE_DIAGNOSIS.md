# Phase 1 — Failure Diagnosis

**Status: EXPLORATORY / NON-CLINICAL / NOT APPROVED**

## Objective

Diagnose why the saved nine-class EG-VAN checkpoint collapses toward `NV`
before proposing or running a new experiment.

## Evidence

### Label encoding

The source manifest and frozen split use the same class order:

`AKIEC, BCC, BKL, DF, MEL, NV, VASC, BENIGN, MALIGNANT`

The frozen confusion matrix and per-class metrics are internally consistent
with this order. There is no evidence of a class-index or label-decoding swap
causing the observed collapse.

### Existing training state

The frozen `best.pt` contains:

- checkpoint epoch index: `1`
- random branch initialization
- no recorded initialization hashes
- training accuracy: 61.21%
- training macro-F1: 11.04%
- validation accuracy: 61.09%
- validation macro-F1: 9.75%
- validation NV predictions: 1,012 / 1,028

The run directory contains `best.pt`, `last.pt`, and `run_provenance.json`.
No epoch-by-epoch `history.csv` or training log is present. The exact 25-epoch
run conclusion cannot be established from the saved artifacts.

### Loss and class balancing

The run configuration records:

- focal loss with alpha 0.25 and gamma 2.0
- Adamax learning rate 0.001
- microbatch 8
- gradient accumulation 4
- 384×384 raw resize/ImageNet preprocessing
- `class_weighting: false`

The training runner uses shuffled random sampling and does not construct a
weighted sampler. Focal loss does not by itself remove the majority-class
gradient advantage.

### Severe class imbalance

The exploratory training partition has:

| Class | Training rows |
|---|---:|
| NV | 4,347 |
| BKL | 754 |
| MEL | 629 |
| MALIGNANT | 512 |
| BCC | 371 |
| AKIEC | 223 |
| VASC | 103 |
| DF | 86 |
| BENIGN | 55 |

NV is 61.4% of training rows and 61.2% of validation rows.

### Prediction collapse

The validation confusion matrix predicts NV overwhelmingly:

- 1,012 of 1,028 validation rows predicted NV
- only BCC and MALIGNANT receive any other predicted examples
- recall is zero for AKIEC, BKL, DF, MEL, VASC and BENIGN
- BCC recall is 3 / 49
- MALIGNANT recall is 1 / 84

### Leakage and identity

The four-way exploratory split contains 10,234 rows:

- train: 7,080
- validation: 1,028
- calibration: 1,023
- test: 1,103

No overlap-group value crosses partitions. This result does not establish
patient independence: the manifest contains only 79 non-empty patient IDs,
and many source identities remain missing or unverified.

## Root-cause assessment

The dominant evidence-supported root cause is an under-trained random-initialization
model combined with extreme majority-class imbalance and no weighted sampling or
class weighting. The saved evidence is from epoch 1, not a completed 25-epoch
training history.

The following are not supported as proven root causes:

- class-index mismatch
- preprocessing mismatch that differs from the recorded run
- checkpoint/model output shape mismatch
- exact seven-class substitution

They remain secondary checks, not the primary explanation.

## Recommended experiments

1. Preserve the existing frozen evidence and train a separate named experiment.
2. Create a weighted-sampling baseline with class weights computed from train
   rows only.
3. Compare standard cross-entropy and weighted cross-entropy against unweighted
   focal loss.
4. Use early stopping only on the validation partition.
5. Track per-branch gradients and the confusion matrix each epoch.
6. Use a resource-bounded CPU-only smoke experiment before 25 epochs.

## Resource blocker

The available environment is CPU-only:

- PyTorch: 2.14.0+cpu
- Torchvision: 0.29.0+cpu
- Torch CUDA: unavailable
- RAM: 7.68 GB total; approximately 0.78 GB free at diagnosis
- E drive: approximately 63.02 GB free

Full CPU training of the 699 MB checkpoint and 58-million-parameter model is
not a feasible uncontested run in the current low-memory state.
