# ISIC 2017 Primary-Source Check

## Authoritative sources

1. **ISIC 2017 Challenge - Task 3: Lesion Classification [Closed]**  
   <https://challenge.isic-archive.com/landing/2017/44/>  
   Official ISIC challenge page; sections “Goal,” “Definitions,” “Data,” and “Ground Truth Data.” Accessed 2026-11-15. The page identifies the challenge as 2017 but gives no more precise release date.
2. **ISIC Archive data page**  
   <https://challenge.isic-archive.com/data/>  
   Official release table, 2017 row. Accessed 2026-11-15. The listed release filenames include `ISIC-2017_Training_Data.zip`, `ISIC-2017_Validation_Data.zip`, and `ISIC-2017_Test_v2_Data.zip`; the page lists 2,000 training, 150 validation, and 600 test images.

No image package was downloaded.

## Official task and labels

The Task 3 page describes two independent binary tasks over three diagnoses:

1. Melanoma versus nevus and seborrheic keratosis.
2. Seborrheic keratosis versus melanoma and nevus.

The page's training split contains 2,000 images: 374 melanoma, 254 seborrheic keratosis, and 1,372 nevi. Its ground-truth file has a separate binary target for each task. The page defines melanoma as malignant and nevus and seborrheic keratosis as benign; those diagnosis definitions do not turn the two challenge targets into one generic BENIGN/MALIGNANT target.

The official data page lists 2,000 train, 150 validation, and 600 test images for the 2017 release. Their combined count is 2,750, not 3,297.

## Comparison with EG-VAN

Direct visual inspection of EG-VAN Table 2 confirms the literal `Dataset Source` value `ISIC 2017` for both added rows:

| Printed class | Dataset Source | Original Images | Testing Images | Train images | Augmented Images |
|---|---|---:|---:|---:|---:|
| Malignant | ISIC 2017 | 1497 | 150 | 1347 | 6653 |
| Benign | ISIC 2017 | 1800 | 180 | 1620 | 6380 |

Section IV-A (printed p. 72862) describes the additional collection as a two-class benign/malignant skin-cancer dataset with more than 3,200 images and cites references [45] and [54]. Table 2 (printed p. 72863) labels its source `ISIC 2017`.

**Result:** `CONTRADICTED` if the table's source label is intended to mean the complete official ISIC 2017 Task 3 release with its official labels: the official release count and task-label schema differ. The exact EG-VAN binary package or any ISIC-derived subset cannot be identified from the paper's source label alone; that lineage is `UNVERIFIED`. No claim is made that the local project images are the complete official ISIC release.

## Evidence limit

The official pages establish the challenge's own release and labels. They do not establish which files EG-VAN authors used, whether they used an external derivative, or how the paper's generic benign/malignant labels were assigned. Author manifest, source version, original image-ID mapping, and label derivation remain necessary to resolve that claim.
