# R1 Paper Source Inventory

Audit directory: `analysis/nine_class_paper_fidelity/R1_AUDIT_20261115T142000Z/`

## Primary paper

| Item | Evidence |
|---|---|
| Local file | `EG-VAN_A_Global_and_Local_Attention-Based_Dual-Branch_Ensemble_Network_With_Advanced_Color_Balancing_for_Multi-Class_Skin_Cancer_Recognition.pdf` in `E:\Cancerdetection` |
| Title | *EG-VAN: A Global and Local Attention-Based Dual-Branch Ensemble Network With Advanced Color Balancing for Multi-Class Skin Cancer Recognition* |
| DOI | `10.1109/ACCESS.2025.3561240` |
| Publication | IEEE Access, vol. 13 (2025), pp. 72852-72874 |
| Version identification | The local PDF first page gives received 20 March 2025, accepted 8 April 2025, publication 15 April 2025, and current-version date 1 May 2025. Crossref metadata independently reports the title, DOI, volume, year, and page range. |
| Relevant locations | Section IV-A, printed p. 72862; Table 2 and Section IV-C, printed p. 72863; Section IV-D, printed p. 72864; references [45] and [54], printed p. 72874. |
| Inspection method | Searchable text was extracted from the PDF text layer. Patient photographs and image pixels were not opened, rendered, processed, or used. |

The local PDF's text layer identifies the Table 2 title, “Complete detail of 9-class skin cancer dataset,” but not its body cells. The table is embedded as non-searchable content in the PDF. This audit did not render or visually inspect that table. Consequently, its per-class counts and source-column entries are not independently verified here.

## Other primary source consulted

| Source | Relevant evidence |
|---|---|
| Official ISIC 2017 Challenge, Task 3: Lesion Classification, <https://challenge.isic-archive.com/landing/2017/44/> | Headings “Goal,” “Definitions,” and “Data.” The official page describes two independent binary tasks over melanoma, nevus, and seborrheic keratosis; it lists 2,000 training images and counts of 374 melanoma, 254 seborrheic keratosis, and 1,372 nevi. Accessed 2026-11-15. |
| Official ISIC data page, <https://challenge.isic-archive.com/data/> | 2017 table lists 2,000 training, 150 validation, and 600 test images, with corresponding ground-truth releases. Accessed 2026-11-15. |

These ISIC pages document the official challenge release. They do not prove which source package EG-VAN actually downloaded.

## Existing project evidence (secondary to the paper)

| File | Use and limitation |
|---|---|
| `EG-VAN/analysis/nine_class_research_completion/paper_table2_transcription.csv` | Existing transcription records seven HAM10000 rows and two rows whose source is written as `ISIC 2017`, with 3,297 binary images total. This is a project transcription, not an independently verified primary-paper table. |
| `EG-VAN/docs/NINE_CLASS_RESEARCH_COMPLETION_PLAN.md`, “Original experiment” | Summarizes the paper transcription, identifies the source-name conflict and unreconciled augmentation totals, and states that author manifests, split seed, source version, and overlap rules are unavailable in the recorded project evidence. |
| `EG-VAN/docs/NINE_CLASS_DATASET_SUITABILITY_DECISION.md`, “Local evidence” | Describes the local binary tree as structurally similar to Fanconic, while explicitly leaving exact version, source identity, label derivation, ISIC-ID bridge, rights, and patient/lesion identity unresolved. |
| `EG-VAN/src/nine_class_stage4.py`, lines 24-25 and 74-90 | Defines local class order; preserves HAM `dx` values after uppercasing; maps local `benign`/`malignant` folder names to the last two classes; tags the binary source `FANCONIC_LOCAL_UNVERIFIED_VERSION`; leaves binary source image, lesion, and patient IDs blank. |
| `EG-VAN/analysis/nine_class_stage4/split_eligibility_audit.json` and `validation_report.json` | Record no final approved split and a blocked eligibility gate. These are project-state evidence, not evidence of the paper's original split. |

## Supplementary material search

A filename search for supplementary material under `EG-VAN` returned no matching file. No local supplement was identified in this search. This does not establish that no supplement or author artifact exists outside the repository.

## Evidence boundary

The only paper claims treated as primary evidence are claims supported by the identified paper text locations. Table 2's non-text cells are not promoted from the existing project transcription to verified paper evidence. The official ISIC source is used only to describe the official 2017 challenge release, not to infer the source or labels of EG-VAN's binary subset.
