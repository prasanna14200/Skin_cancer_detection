# R4 IQA Gap Analysis

## Current status
The project contains an image-quality assessment implementation, but the saved evidence is not a validated classification-performance or image-quality-to-error result.

## Implemented components
- IQA feature extraction and sample-level comparison code are present in `EG-VAN/src/nine_class_iqa.py`.
- Stage 7 and Stage 10 outputs contain descriptive sample and comparison artifacts.
- The implementation supports comparison across processed and baseline image states, but the audit did not find a validated model-quality linkage.

## Existing evidence
The saved evidence package shows descriptive metrics and plots, not a scientifically resolved IQA result:

- Stage 7: sample-level descriptive output.
- Stage 10: a four-variant descriptive comparison.
- The source audit in `R3_IQA_EXPERIMENT_AUDIT.md` explicitly records that the results are descriptive only and do not establish classification-performance association.

## Gap
There is no approved run where IQA features are correlated with a leakage-safe held-out classifier error pattern, per-class confusion or a calibrated uncertainty outcome. This means the IQA branch is not currently valid for scientific claim-making.

## Decision
The IQA implementation is reusable for exploratory research, but only after it is run on an approved cohort and tied to an actual model-output analysis on a frozen test set.

`IQA_EXPERIMENT_STATUS = DESCRIPTIVE_METRICS_IMPLEMENTED_AND_EXECUTED__CLASSIFICATION_ASSOCIATION_NOT_VALIDATED`
