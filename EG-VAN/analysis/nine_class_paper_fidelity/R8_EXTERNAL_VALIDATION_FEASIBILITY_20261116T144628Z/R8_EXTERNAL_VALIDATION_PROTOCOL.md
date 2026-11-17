# External-validation protocol and boundary

## Scope

This package assesses whether existing local data can support future external evaluation. It does not approve any cohort or authorize inference. The candidate-screen input keeps original labels and source IDs, records candidate mappings separately, and marks records `QUARANTINED` or `EXCLUDED`.

## Populations examined

- PH2: 200 canonical dermoscopic images with source diagnoses and local integrity records.
- SIIM–ISIC 2020: the existing 100-image bounded pilot, with source image, patient and lesion IDs, detailed diagnosis, task label, license, attribution, and byte hash.
- ISIC 2017 Task 3: local ground-truth metadata only; no exact-ID image files were found.
- HAM10000 and the Fanconic-like binary data are internal development sources and were not treated as external.

## Candidate retrieval

The unchanged `src/nine_class_external_protocol.py::screen_external` implementation verified candidate paths and SHA-256 values, then used the Stage 4 source inventory and saved fingerprints. A relation is retrieved for exact SHA-256, a verified identifier-namespace match, or pHash/dHash Hamming distance <=6. This is a conservative candidate-retrieval rule, not an identity classifier, calibrated sensitivity threshold, or proof of patient independence.

The saved Stage 4 fingerprints were independently recomputed for all 13,312 internal images using the existing fingerprint function and OpenCV 5.0.0: 13,312 matched, with no missing, unreadable, or mismatching images. All current candidate relations remain unreviewed.

## Label policy

Only source-recorded diagnoses are carried forward. The accompanying mapping table distinguishes exact, clinically justified non-identical, unsupported, and unknown labels. PH2 atypical nevi remain unsupported. SIIM task target 0 is not equated with an EG-VAN class; only its detailed nevus and seborrheic-keratosis diagnoses have tentative NV/BKL subset mappings. Unknown diagnoses remain unmapped.

## Approval gate

The existing evaluator requires an approved internal split, checkpoint provenance bound to that split/configuration/preprocessing, a frozen external manifest, completed rights/mapping/overlap review, and explicit external approval. The current checkpoint is from an unapproved exploratory run. No gate was bypassed, and no training or inference was run.
