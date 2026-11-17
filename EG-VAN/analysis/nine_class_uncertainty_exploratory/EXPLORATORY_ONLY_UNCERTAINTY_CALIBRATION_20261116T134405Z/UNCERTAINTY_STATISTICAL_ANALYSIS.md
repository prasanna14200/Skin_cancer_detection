# Statistical analysis

**EXPLORATORY / NON-CLINICAL.** No causal or clinical interpretation is supported.

## Overall calibration and uncertainty

There are 1,028 saved validation predictions: 628 correct and 400 incorrect. Mean confidence is 0.5824 (median 0.5156), while accuracy is 0.6109. Mean predictive entropy is 1.2414 nats (normalized 0.5650); mean top-two margin is 0.4329.

The existing equal-width, 10-bin top-label ECE is **0.0431**. The multiclass Brier score is **0.5177** and probability NLL is **1.1513 nats**. Cluster-bootstrap 95% intervals are in `UNCERTAINTY_CLUSTER_BOOTSTRAP_CI.csv`: ECE 0.0380-0.0794, Brier 0.4839-0.5498, and NLL 1.0717-1.2261.

The overall ECE is an aggregate top-label quantity, not proof of class-wise calibration. The predicted label is NV for 1,012/1,028 rows. In the 0.8-0.9 confidence bin, 274 rows have observed accuracy 0.953 and mean confidence 0.867; the 0.9-1.0 bin has 36 rows, all correct, with mean confidence 0.906. The latter is a small validation-only subset.

## Class-wise results

The class-wise CSV reports source-defined true-class support, precision/recall, confidence and entropy summaries, one-vs-rest Brier/ECE, and calibration conditional on predicted class. Predictions are highly concentrated: NV 1,012; BCC 15; MALIGNANT 1; all other classes 0. For the single MALIGNANT prediction, conditional accuracy is 1.0 but confidence is approximately 0.308; this is one observation and not a stable class calibration result. No class-wise conclusion should be drawn from the absence of predictions for seven classes.

## Error detection and risk-coverage

There are 400 errors (prevalence 0.389). Higher entropy ranked errors best among the three scores: AUROC 0.798 (cluster-bootstrap 95% interval 0.768-0.828), average precision 0.660 (interval 0.602-0.724). For 1-confidence, AUROC is 0.787 (0.758-0.820) and average precision 0.642 (0.583-0.708). For 1-margin, AUROC is 0.771 (0.741-0.806) and average precision 0.618 (0.560-0.684). The random-ranking AP baseline is the error prevalence, 0.389.

Image-level Mann-Whitney comparisons found higher uncertainty among incorrect predictions (raw p-values and Holm adjustment are in `UNCERTAINTY_ERROR_DETECTION.csv`). These p-values assume independent rows and are descriptive only; repeated groups and cohort limitations make formal inferential claims inappropriate.

At the fixed confidence threshold 0.8, 310/1,028 images are retained (30.2% coverage) with 95.8% observed accuracy on this validation artifact. At 0.9, only 36/1,028 are retained and all are correct. These are exploratory retrospective points, not validated thresholds or evidence that rejected/accepted predictions are clinically safe.

## Interpretation

Confidence and entropy show useful rank association with errors on this saved split. This does not establish well-calibrated probabilities, safe selective prediction, or generalization. Class collapse, class/source composition, repeated overlap groups, and unapproved data dominate interpretation. No confirmatory hypothesis testing or causal analysis was performed.
