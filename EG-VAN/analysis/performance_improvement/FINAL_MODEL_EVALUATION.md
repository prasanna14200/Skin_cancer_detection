# Final Model Evaluation

**Status: EXPLORATORY / NON-CLINICAL**

No genuinely improved model or new checkpoint was produced in this sprint.
The only available measured nine-class validation result remains the saved
historical checkpoint result.

## Historical checkpoint validation

- samples: 1,028
- accuracy: 61.09%
- macro-F1: 9.75%
- weighted-F1: 47.17%
- balanced accuracy: 11.84%
- correct: 628
- incorrect: 400
- NV predictions: 1,012 / 1,028

## Untouched test set

An 1,103-row test partition exists in the exploratory split, but it remains
part of a NOT_APPROVED exploratory four-way cohort. No test-set inference was
performed as the sprint did not establish a valid, independent selected model.
Accordingly, no test accuracy is claimed.

## 80% target

The 80% target was not achieved. The historical result is 61.09% validation
accuracy and remains a class-collapse result.

## Remaining bottlenecks

- unapproved cohort and split
- no GPU
- low available RAM
- extreme class imbalance
- random initialization
- no weighted sampling or class weighting in the saved run
- only epoch 1 is embedded in the frozen checkpoint
- missing epoch history
