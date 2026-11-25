# FANCONIC_LOCAL_UNVERIFIED_VERSION provenance investigation

## Finding

The exploratory split contains **845** rows labeled `FANCONIC_LOCAL_UNVERIFIED_VERSION`. Their source/folder label is `malignant`, not an independently verified clinical diagnosis. Exact upstream identity/version is not established: `UNVERIFIED_ORIGIN_PENDING`. No license, research-use permission, commercial-use permission, or redistribution permission is inferred.

## Local investigation

- All 845 rows have blank `image_id`, `patient_id`, and `lesion_id`; no Archive record, contributor attribution, or image-level license can be joined.
- Source partition counts: 680 `train`, 165 `test`; exploratory assignment: 512 train, 84 validation, 84 calibration, 165 test. These are counts, not approval of a split.
- No authoritative acquisition receipt for these 845 files was found.
- No verified remote file checksums exist in the local evidence. The prior metadata-only file-list comparison is not a content hash and is not proof of byte identity.
- All 845 records have no image-level source identifiers, so no originating image or contributor-license mapping is verified.
- Local recovery notes describe 3,297 images in `data/isic/data/{train,test}/{benign,malignant}/`. A prior metadata-only Kaggle query (recorded 2026-10-19) reported uploader Claudio Fanconi, version 4, `licenseName=Unknown`, and a train/test note. The notes report matching local/Kaggle path names and byte sizes only.
- Kaggle v4 remains a provenance lead only, not rights evidence or proof these 845 files came from that exact release. No local `LICENSE`, `README`, terms, attribution, image-ID, or provenance file was found under `data/isic/`.
- The paper citation, folder labels, public availability, and uploader statements do not establish rights for these exact image files.

## Minimum additional evidence

1. Authoritative versioned package/acquisition identity with file-level checksums.
2. Per-file mapping to original source records and applicable contributor license/attribution.
3. Official package terms, access conditions, and any separate agreement.
4. Researcher review of research/publication, commercial, redistribution, derivative/model-weight, output, and demo uses.

Until that evidence exists, source identity and permission remain unresolved. Do not treat filenames, folder names, file sizes, or public availability as provenance or a license grant.

References: `analysis/nine_class_exploratory/exploratory_split.csv`, `analysis/nine_class_stage4/nine_class_source_manifest.csv`, `docs/NINE_CLASS_DATASET_RECOVERY_PLAN.md`, [candidate Kaggle page](https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign?datasetVersionNumber=4). Until these gaps are resolved, no use is approved by this audit.
