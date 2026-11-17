# R8 external-validation feasibility

**Decision: no eligible, approved full nine-class external cohort is available locally.** This is an exploratory, non-clinical feasibility assessment only. External model evaluation, training, and inference were not performed. No clinical validity, cohort approval, or paper reproduction is claimed.

## Candidate-source findings

| Source | Locally available evidence | Candidate labels | Overlap-screen result | Decision |
|---|---|---|---|---|
| PH2 | 200 source-labeled images: common nevus 80, atypical nevus 80, melanoma 40. All decoded; derived, preserved-original, and second-copy image trees match byte-for-byte, and all 200 match the historical integrity hashes. | Candidate subset: NV 80, MEL 40. Atypical nevus 80 remains unsupported and excluded. | 99 images had 580 perceptual candidate relations; all were dHash-only at distance <=6. 101 had no candidate, but patient independence is unknown. No exact-hash overlap. | Not a nine-class cohort. No patient/lesion IDs; local release date/version and exact Kaggle-v2 byte linkage are unverified. Prior PH2 use in a legacy classifier is recorded. |
| SIIM–ISIC 2020 pilot | 100 locally acquired images, 100 distinct source patient IDs and 100 distinct lesion IDs; all image hashes match the acquisition ledger and all images decoded. All have the melanoma-task target 0. Detailed diagnoses: unknown 82, nevus 17, seborrheic keratosis 1. | Only detailed diagnoses get tentative subset mappings: NV 17 and BKL 1. The 82 unknown cases remain unmapped. The task-level negative is not mapped to EG-VAN `BENIGN`. | 68 images had 6,448 perceptual candidate relations (6,430 dHash-only, 14 pHash-only, 4 both); 32 had no candidate. No exact-hash overlap. All candidates remain unreviewed. | Bounded, single-task pilot; not a nine-class cohort. The earlier, narrower pilot screen marked 16 images uncertain; all 16 are among the 68 current candidates, with 52 additional images flagged only under this broader screen. |
| ISIC 2017 Task 3 | 2,750 metadata IDs: nevus 1,843, melanoma 521, seborrheic keratosis 386. No matching image filename was found among 38,316 project image files. | Potential mappings to NV/MEL/BKL only; no local image bytes to verify or evaluate. | Not screenable without matching image files. | Metadata only; local image-package provenance and rights are not established. |
| HAM10000 and local Fanconic-like source | Stage 4 internal manifest contains 10,015 HAM10000 and 3,297 Fanconic-like images. The additional 3,297-image numeric tree is byte-identical to the internal Fanconic-like tree (one image hash has two paths). | These sources are already in the development inventory. | Not eligible for external screening as independent data. | Excluded from the external candidate set. |

The Stage 9 candidate screen used the existing rule: exact SHA-256, verified same identifier namespace, or pHash/dHash Hamming distance <=6. It returned 7,028 perceptual relations (580 PH2; 6,448 SIIM), with no exact-hash or identifier matches. The high relation count is driven primarily by dHash-only hits and is candidate retrieval—not confirmation of duplicate photographs. Every candidate and every no-candidate result remains unresolved; a no-candidate result does not establish patient independence.

PH2's recorded terms limit use to non-commercial research/education, prohibit redistribution and commercial use, and require citation. Its provenance validator reports `VERIFIED` for that narrow documented scope, but no unrestricted license is claimed, and the exact local-release-to-Kaggle-v2 byte link is unverified. SIIM pilot rights records show aggregate CC BY-NC 4.0, required attribution, and image-level licenses of 57 CC-BY and 43 CC-BY-NC; the served files are not proven byte-identical to the fixed Challenge ZIP.

## Why the frozen model was not evaluated

The checkpoint provenance labels the run `EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION` and records all records as not approved. Stage 9 contains a header-only external-manifest template and synthetic software-verification summary, not an approved cohort or external approval. The evaluator requires an approved internal split and checkpoint provenance bound to it, plus an approved external manifest, rights/mapping evidence, overlap review, and explicit external approval. Those gates were not bypassed.

No candidate covers all nine target classes. PH2 offers at most a two-class candidate subset; the 100-image SIIM pilot offers only 18 detailed-diagnosis candidates across NV/BKL and 82 unknown labels; ISIC 2017 images are unavailable locally by ID. None is eligible for full nine-class external validation.

## Minimum requirements for a future study

1. Establish a fixed source/version and permitted-use record, preserving PH2 citation/non-commercial/no-redistribution limits and SIIM aggregate plus image-level attribution.
2. Obtain independent review of label mappings; never map SIIM task-negative `benign` to EG-VAN `BENIGN`, or map unknown diagnoses or PH2 atypical nevi.
3. Resolve every exact/possible cross-source image candidate and document the limitation that PH2 lacks patient identifiers and SIIM identifiers have no verified cross-source namespace bridge.
4. Secure a genuinely independent, defensibly labeled cohort covering all nine classes for a full nine-class evaluation.
5. Establish an approved internal split/checkpoint provenance and freeze the external manifest, source rights, label mapping, overlap decisions, and explicit external approval before inference.

The frozen checkpoint hash, input/source hashes, screen outputs, and independent validation are recorded in the accompanying evidence register, overlap-screen files, and validation report.
