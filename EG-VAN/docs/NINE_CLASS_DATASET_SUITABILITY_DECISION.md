# Nine-class dataset suitability and source verification

Decision date: 2026-10-19. This is a provenance and evaluation gate. No image, audit CSV, script, checkpoint, or split was changed; no dataset was downloaded. Current proposed exclusions remain proposals, not file removals.

## Paper source and reference trail

The [EG-VAN paper, §IV-A](https://www.researchgate.net/publication/390831641_EG-VAN_A_Global_and_Local_Attention_based_Dual-Branch_Ensemble_Network_with_Advanced_color_balancing_for_Multi-Class_Skin_Cancer_Recognition) calls its second input a two-class skin cancer dataset with malignant and benign labels and over 3,200 images; it cites **[45] and [54]**. It does **not** give a direct download URL, archive checksum, version number, per-image list, or derivation of those labels. Its first input is HAM10000's seven diagnoses. A nine-class model combines these two differently scoped label sets.

- **[45]** is O. Attallah, *Skin-CAD: Explainable deep learning classification of skin cancer from dermoscopic images by feature selection of dual high-level CNNs features and transfer learning*, *Computers in Biology and Medicine* 178 (2024), 108798, DOI [10.1016/j.compbiomed.2024.108798](https://doi.org/10.1016/j.compbiomed.2024.108798). Its [data availability statement](https://www.sciencedirect.com/science/article/abs/pii/S0010482524008837) explicitly names **“Skin Cancer: Malignant vs. Benign”** at [Kaggle `fanconic/skin-cancer-malignant-vs-benign`](https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign), accessed 20 November 2023. This is the strongest source identification in the cited chain; it identifies a collection page, not EG-VAN's exact downloaded version.
- **[54]** is K. Sethanan et al., *Double AMIS-ensemble deep learning for skin cancer classification*, *Expert Systems with Applications* 234 (2023), 121047, DOI [10.1016/j.eswa.2023.121047](https://doi.org/10.1016/j.eswa.2023.121047). Its [accessible article description](https://www.sciencedirect.com/science/article/pii/S095741742301549X) says it combines HAM10000 with a “malignant vs. benign” dataset for nine categories. Accessible source text did not establish a versioned package, per-image list, or publisher URL. It corroborates the kind of dataset, not exact source bytes.

An independent [PLOS ONE study of the Fanconic collection](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0269826) reports 3,297 images (1,800 benign, 1,497 malignant), RGB at 224 × 224, divided into train/test folders. It states the pictures are processed ISIC Archive images and that image rights follow the Archive. This supports a **structural match**, not a byte-for-byte identity claim. The paper's CC BY 4.0 article license is not a license grant for the underlying images.

## Local evidence

Only `data/isic/data/` is the canonical proposed binary tree. Its current labels and counts are `train/benign` **1,440**, `train/malignant` **1,197**, `test/benign` **360**, and `test/malignant` **300**: 3,297 JPG entries. Thirty sampled images from each branch decode at 224 × 224; the historical full-image audit reports the same format. The `data/isic/{train,test}/` mirror is byte-identical and is never an additional data source. Filenames such as `1003.jpg` are numeric local names, not source ISIC image IDs; names repeat across labels/splits. `train/malignant/768.jpg` and `769.jpg` are byte-identical.

There is no local README, archive, metadata table, label provenance record, license file, package receipt, version number, original ISIC ID map, lesion ID, or patient ID inside `data/isic/`. The folder labels identify the local class assignment but do not independently validate clinical diagnosis. The exact download date, upstream package revision, whether the binary train/test assignment is a protected official test, and per-image rights cannot be established from local files. Therefore **SOURCE_IDENTITY_VERIFIED = NO**, even though the structure strongly resembles Fanconic.

The latest [overlap completion summary](../analysis/nine_class_overlap_completion/completion_summary.json), [proposed exclusion ledger](../analysis/nine_class_overlap_completion/proposed_binary_exclusions.csv), and [focused queue](../analysis/nine_class_overlap_completion/human_review_queue.csv) preserve the evidence. There are **2,369 proposed binary exclusions**, including 2,365 records confirmed as the same photograph as a HAM image. SHA-256 found no byte-identical cross-source copy: the confirmed cross-source matches are recompressed/resized photos or assistant-visual confirmations. The audit leaves **425** unresolved priority pairs and a **760-pair** focused queue, with 344 retained binary entries touching at least one unresolved candidate. These figures are evidence of substantial source overlap, not proof that all remaining images are independent lesions or patients.

| Class | Original binary entries | Proposed excluded | Retained upper bound | Retained source train | Retained source test | Retained with unresolved candidate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BENIGN | 1,800 | 1,717 | **83** | 64 | **19** | **83** |
| MALIGNANT | 1,497 | 652 | **845** | 680 | 165 | 261 |
| Total | 3,297 | 2,369 | **928** | 744 | 184 | 344 |

All **19** provisionally retained benign source-test entries have unresolved candidate relations. One misclassification among 19 changes benign test accuracy by about **5.3 percentage points**, before further exclusions or lesion grouping. The source-test branch has 184 retained entries overall, but its original 660-image binary test contained 476 confirmed HAM photo matches. The remaining binary test records therefore do **not** currently support a credible paper-comparable nine-category test result. The source-test status itself is not documented by a local source record. Relabeling or borrowing HAM diagnoses to inflate BENIGN would change the task; automatically discarding every visually similar candidate would also bias it.

## Alternative source and rights check

The named primary collection remains [Fanconic on Kaggle](https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign); no **official, version-pinned alternative** or file-checksum manifest for EG-VAN's binary subset was found. The [ISIC Archive](https://www.isic-archive.com/) is a possible upstream source for original images and metadata, but the local numeric filenames lack the map needed to recover them. Another Kaggle uploader has a similarly named [collection](https://www.kaggle.com/datasets/abhikray/skin-cancer-malignant-vs-benign); its equivalence, authorship, and version relation to the cited Fanconic package are unverified, so it is not a substitute.

The Kaggle dataset page was reachable by URL, but its metadata/version/license fields were not accessible in this review. Do not assign a dataset-level license from third-party descriptions. The [ISIC terms](https://challenge.isic-archive.com/terms-of-use/) and [ISIC licensing FAQ](https://www.isic-archive.com/blank-1) say image owners set licenses per image, including CC0, CC BY, and CC BY-NC. Without original ISIC IDs and a rights manifest, the license of each local image is unresolved; check before redistributing images or making a use claim. The paper's CC BY article license does not resolve that uncertainty.

## Feasibility comparison

| Route | Scientific status with present files | Required evidence before evaluation |
| --- | --- | --- |
| **A. Paper-faithful nine-class reconstruction** | **No exact reproduction.** The cited source family is identifiable through [45], but the paper's binary package version, original image assignments, split, and overlap handling are not. Matching 3,297 counts does not fill those gaps. | Author/source package manifest or version and split details; image-level provenance; explanation of paper overlap handling. A current download alone cannot recover an unspecified historical snapshot. |
| **B. Leakage-controlled nine-label adaptation** | **Conditional research adaptation, not ready for final split.** Same intended nine output names and architecture can be used, but the surviving BENIGN pool is 83, with 19 provisional source-test entries, all unresolved. This is a source-conditioned benchmark, not nine exclusive clinical diagnoses. | Resolve high-risk BENIGN and source-test candidates, verify provenance/rights and protected test policy, then reassess class/test size. Group confirmed photo relations and HAM lesion IDs; never claim patient independence without identifiers. |
| **C. Seven-class EG-VAN fallback** | **Most defensible immediate data route, if approved as a changed research objective.** HAM10000 has 10,015 images, seven verified `dx` labels, and available HAM `lesion_id`. The paper also reports seven-class EG-VAN results, but its exact image split remains unavailable. | Explicitly label this a seven-class reconstruction, use a documented lesion-grouped split, and avoid comparing it as the original nine-class experiment. No training or split was created here. |

## Decision and next action

Pause further large-scale pair adjudication until the project chooses its scientific target. First seek a **versioned Fanconic package record or author confirmation**, original binary label/ISIC-ID mapping, the paper's source image/split list if available, and licensing evidence. This is a metadata/provenance task; **no image download is required now**. If a later version comparison is approved, obtain only the exact [cited Fanconic collection](https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign) at a documented version, checksum its package, and compare file hashes/perceptual identities without overwriting local images. An unversioned fresh copy cannot prove paper equivalence.

If exact source evidence cannot be obtained, choose between (B) a carefully qualified nine-label adaptation after BENIGN/test review and (C) a clearly labeled seven-class fallback. Do not make a final split, preprocess the combined collection, train, or claim nine-class paper reproduction on the present evidence.

## Requested report fields

PAPER_BINARY_SOURCE: Two-class “malignant and benign” skin cancer dataset cited as [45] and [54]; [45] identifies the Fanconic Kaggle collection. The paper itself gives no version or direct package manifest.

LOCAL_BINARY_SOURCE: `data/isic/data/`, 3,297 canonical JPG entries in train/test and benign/malignant folders; mirror excluded.

SOURCE_IDENTITY_VERIFIED: **NO**.

OVERLAP_IMPACT: 2,369 proposed binary exclusions; 2,365 are confirmed HAM-photograph copies; 425 priority pairs unresolved and 760 pairs in the focused queue.

REMAINING_CLASS_COUNTS: BENIGN **83** (64 train, 19 source test); MALIGNANT **845** (680 train, 165 source test); all are upper bounds.

TEST_SET_FEASIBILITY: **NO** defensible nine-category test yet; every retained benign source-test record has unresolved candidate overlap and 19 is too small for a stable class estimate.

ALTERNATIVE_SOURCE_FOUND: Official ISIC upstream archive identified, and a similarly named Kaggle uploader found; neither is a verified alternate version of the exact paper binary collection.

NINE_CLASS_RECONSTRUCTION_FEASIBLE: Exact paper reproduction **NO**; leakage-controlled nine-label adaptation **conditional and currently blocked**.

RECOMMENDED_NEXT_ACTION: Verify Fanconic/paper package provenance and rights, then decide whether to adjudicate the remaining BENIGN/test cases for adaptation or approve a clearly labeled seven-class fallback.

DOWNLOAD_REQUIRED: **NO**, not for the present suitability decision.

IF_DOWNLOAD_REQUIRED_EXACT_SOURCE: If a later approved version comparison requires it, use `https://www.kaggle.com/datasets/fanconic/skin-cancer-malignant-vs-benign` at a recorded version; the EG-VAN paper's exact version is unknown.

REMAINING_BLOCKERS: Unverified binary version and label/ISIC-ID map; unknown per-image licenses and patient identities; undocumented paper image assignments and overlap handling; all retained BENIGN images have unresolved candidate relations; very small provisional benign source-test set.
