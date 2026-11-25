# EG-VAN Research Approval Audit

- Generated UTC: 20261122T065436Z
- Project: `/content/drive/MyDrive/EG-VAN`
- Source split: `analysis/nine_class_exploratory/exploratory_split.csv`
- Source split SHA-256: `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740`
- Approval checklist SHA-256: `e9597aae3d03e3b1d549da474fc7befaa82ec2d7bf3872d0123d4a44359977be`

## Current gate

- Existing approval status: **NOT_APPROVED**
- Approved eligible images in existing checklist: **0**
- Approved four-way split: **False**
- Rows marked APPROVED in split CSV: **0**
- Preprocessing status: `candidate_for_future_approved_cohort; no_training_authorized`

**This audit does not authorize training.** Do not train on this cohort until the researcher has resolved source rights, label policy, identity review, screening validation, eligible class counts, calibration/split freeze, and formal approval.

## Inventory

- Total split rows: 10234
- Partition counts: `{"calibration": 1023, "test": 1103, "train": 7080, "validation": 1028}`
- Source counts: `{"FANCONIC_LOCAL_UNVERIFIED_VERSION": 845, "HAM10000": 9310, "SIIM-ISIC 2020 training v2": 79}`
- Class counts: `{"AKIEC": 327, "BCC": 514, "BENIGN": 79, "BKL": 1099, "DF": 115, "MALIGNANT": 845, "MEL": 883, "NV": 6230, "VASC": 142}`
- Missing image paths at audit time: 0
- Identity candidate queue rows (not adjudications): 8224

## Files generated

- `source_class_partition_inventory.csv`
- `class_partition_eligibility_counts.csv`
- `status_and_source_counts.csv`
- `missing_image_paths.csv`
- `SOURCE_RIGHTS_REVIEW_TEMPLATE.csv`
- `LABEL_MAPPING_REVIEW_TEMPLATE.csv`
- `HUMAN_IDENTITY_ADJUDICATION_QUEUE.csv`
- `RESEARCHER_APPROVAL_CHECKLIST_TEMPLATE.csv`

## Limitations

- File existence does not establish image authenticity, rights, label correctness, or cohort eligibility.
- Matching identifiers and overlap groups are review candidates, not proof of duplicate photographs or leakage.
- Blank review fields require documented human/researcher decisions.
- No data, split, model, checkpoint, or training artifact was modified.
