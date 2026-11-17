# R3 Dataset Preparation Status

Audit scope: existing artifacts only. Dataset preparation was not rerun and no image contents were opened for this audit.

## Status distinction

**Operational preparation is complete for the exploratory workflow:** the source inventory, on-demand preprocessing, four-way exploratory assignment, source screening, loader preflight, and dataset metadata artifacts already exist. This does **not** mean there is a final research-grade cohort. The production/reproduction readiness gates remain blocked: Stage 12 records zero approved rows, no production approval, no approved split, 0/19 primary pairs reviewed, and 101 additional relations still unresolved.

## Existing source inventory

`analysis/nine_class_stage4/nine_class_source_manifest.csv` is a 13,312-row source inventory, not an approved training set. It contains 10,015 HAM10000 records and 3,297 records labeled `FANCONIC_LOCAL_UNVERIFIED_VERSION`. Aggregate source-label counts:

| Source-defined output label | Stage 4 inventory |
|---|---:|
| AKIEC | 327 |
| BCC | 514 |
| BKL | 1,099 |
| DF | 115 |
| MEL | 1,113 |
| NV | 6,705 |
| VASC | 142 |
| BENIGN | 1,800 |
| MALIGNANT | 1,497 |
| **Total** | **13,312** |

These are source labels, not nine validated, mutually exclusive clinical diagnoses. HAM diagnoses remain unchanged. The Fanconic source/version and its binary label derivation remain unresolved; a Fanconic `MALIGNANT` label is not interchangeable with HAM `MEL`. The original paper's aggregate count concordance does not establish local record identity or provenance.

An additional 200 SIIM–ISIC 2020 candidates are recorded in the final-cohort artifacts. The saved screen reports 121 candidate/quarantine records and 79 preliminary no-candidate records; none are approved. The exploratory split includes the 79 preliminary SIIM records as source-defined `BENIGN` labels, not as evidence of clinical label equivalence. All candidate rows remain unapproved.

## Existing splits and counts

The Stage 4 inventory deliberately has no approved split. A separate `analysis/nine_class_exploratory/exploratory_split.csv` is a frozen **EXPLORATORY_ONLY** four-way assignment over 10,234 records. Its SHA-256 is `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740`, matching the saved provenance and validation report.

| Partition | Records | AKIEC | BCC | BKL | DF | MEL | NV | VASC | BENIGN | MALIGNANT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Train | 7,080 | 223 | 371 | 754 | 86 | 629 | 4,347 | 103 | 55 | 512 |
| Validation | 1,028 | 42 | 49 | 108 | 9 | 84 | 629 | 15 | 8 | 84 |
| Calibration | 1,023 | 30 | 44 | 122 | 10 | 85 | 627 | 13 | 8 | 84 |
| Test | 1,103 | 32 | 50 | 115 | 10 | 85 | 627 | 11 | 8 | 165 |

The records are 9,310 HAM, 845 local binary-source `MALIGNANT`, and 79 SIIM source-negative `BENIGN`. The exploratory validator reports zero known overlap/hash/lesion/patient group crossings. However, the saved provenance explicitly says patient/photo identity is unknown; only 79 rows have a nonempty patient ID and 9,389 a nonempty lesion ID. This is metadata separation, not proof of independent people or images. The 165 publisher-source-test `MALIGNANT` records remain in the exploratory test partition and were not used for the reported validation metrics.

The saved real-image preflight verified hashes for 10,234 records and loaded nine real examples per class in each of the four partitions (36 examples total). It did not load every image through the model or approve the records.

## Preprocessing already present

- `data/processed/images` contains 10,015 legacy processed HAM files; this is not the nine-class exploratory model's input cohort.
- The nine-class Stage 4 loader can process on demand: hair masking/inpainting, Gray World, three-scale Retinex, RGB conversion, resize to 384x384, and ImageNet normalization. Numerical values are local implementation choices.
- The actual exploratory run used `raw_resize_imagenet_v2`: raw RGB resize and normalization, without Stage 4 hair removal, Gray World or Retinex.
- The Stage 7 sample and Stage 10 preprocessing comparison are descriptive artifacts. They do not prove clinical image-quality improvement or model-performance benefit.

## Readiness and separation of concerns

| Readiness dimension | Current state |
|---|---|
| Operational preparation artifacts | **Complete for exploratory workflow** |
| Paper-source identity/version verification | **Unresolved** |
| Record-level rights/permitted use | **Unresolved for the combined training cohort** |
| Source-label compatibility and class semantics | **Unresolved** |
| Patient/lesion identity and duplicate adjudication | **Incomplete; human review pending** |
| Research-grade leakage-approved split | **Not approved; none exists** |
| Exploratory four-way assignment | **Exists; not approved and not a validated test/calibration split** |

Stage 4 records 8,303 transitive overlap groups and 90 groups spanning publisher train/test after group joins. Stage 12 reports 0/19 primary pairs adjudicated, 101 additional relations unresolved, zero approved inventory rows, and no production approval/split. Treat these as dataset-readiness blockers, not as evidence that the operational preparation work was never done.
