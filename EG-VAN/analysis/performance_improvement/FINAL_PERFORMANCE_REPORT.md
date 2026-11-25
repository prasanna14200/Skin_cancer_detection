# Final Performance Improvement Report

**Status: EXPLORATORY / NON-CLINICAL**

## Outcome

The 80% target was not achieved. No genuine improved checkpoint was produced.
The only validated saved result remains 61.09% exploratory validation accuracy,
with 9.75% macro-F1 and severe prediction collapse toward NV.

## Failure diagnosis

The saved model is likely in an under-trained random-initialization state:
the frozen checkpoint embeds epoch index 1, while no epoch-history file is
present. The run is not proof that 25 epochs completed. The training partition
is highly imbalanced, with NV at 4,347 / 7,080 rows and BENIGN at 55 / 7,080.
The saved run disables class weighting and uses no weighted sampler.

No label-index mismatch was found. Preprocessing and nine-class state-dict
loading agree with the source order.

## Controlled experiments

A CPU gradient smoke test using one synthetic batch passed:

- logits shape: `(1, 9)`
- finite forward output
- 766 parameter gradients
- all 766 gradients finite
- no checkpoint or metric claim produced

No real balancing experiment was launched because the host has no compatible
GPU, approximately 0.78 GB free RAM at diagnosis, and the existing cohort
remains unapproved.

## Genuine measured result

| Metric | Result |
|---|---:|
| Accuracy | 61.09% |
| Macro-F1 | 9.75% |
| Weighted-F1 | 47.17% |
| Balanced accuracy | 11.84% |
| Validation samples | 1,028 |
| NV predictions | 1,012 |

## What remains required

1. Establish a named approved split and protected test partition.
2. Resolve patient/lesion identity and source rights.
3. Provide a compatible GPU or accept a CPU-only diagnostic-only scope.
4. Run train-only class-weighted baseline experiments.
5. Compare standard CE, weighted CE and focal loss.
6. Measure epoch history and per-branch gradients.
7. Freeze the best validation model, then evaluate it once on the untouched test.

No external validation, clinical readiness or paper reproduction is claimed.
