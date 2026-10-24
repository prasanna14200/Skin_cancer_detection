# Stage 11A: independent protected BENIGN photo review

Date: 2026-10-22. This package prepares **19** Fanconic publisher-test BENIGN ↔ HAM10000 candidate pairs for a new independent photographic review. It records **zero** new reviewer decisions. Judge only whether two images are the same *photograph*; do not classify the lesion, infer a shared patient, or approve a dataset record. No raw image, original label, Stage 3 evidence, split or model was changed.

## Reviewer instructions

Open [gallery.html](../analysis/nine_class_stage11a/gallery.html) locally in a browser. Image A and Image B are byte-identical copies of the original JPEG files with neutral names under `originals/`. They display at their native pixel dimensions (Fanconic 224×224; HAM 600×450), keep the original aspect ratios, and have no resampling, color enhancement, hair removal, Retinex, overlay, alignment, or markup. Click either image for a separate native image tab. The gallery is self-contained inside `analysis/nine_class_stage11a/`; keep its `originals/` subfolder beside the HTML file.

For each review ID, choose exactly one of `SAME_PHOTO`, `DISTINCT_PHOTO`, or `UNCERTAIN`. `SAME_PHOTO` means matching photographic content despite crop, scale or JPEG differences. `DISTINCT_PHOTO` means the photographic fields differ; it does **not** establish a different lesion or patient. If identity cannot be judged from the unchanged originals, choose `UNCERTAIN`. Use the notes field to cite visible landmarks, crop, artifacts or the reason for uncertainty. Decisions start blank; no prior automated decision or numerical score appears in the gallery or decision ledger.

Enter your real reviewer identity or code and an ISO 8601 **UTC** review date/time, then select **Download decision CSV**. Save the downloaded file outside the original package or under a new, clearly named path. The page does not write back to the source ledger. Download progress before closing the browser; the page does not save unfinished selections automatically. Do not edit [review_id_mapping.csv](../analysis/nine_class_stage11a/review_id_mapping.csv) or [additional_candidate_relations.csv](../analysis/nine_class_stage11a/additional_candidate_relations.csv) while reviewing. Share the local image package externally only after confirming image-use rights, which remain unresolved.

## Coordinator mapping and evidence

Keep this section and the mapping/additional-relations CSVs with the coordinator until the independent reviewer has exported decisions. The reviewer-facing materials are `gallery.html`, `originals/`, and the blank ledger schema.

The review IDs were assigned by sorting frozen Stage 3G candidate-pair IDs, independently of prior review order. The [mapping CSV](../analysis/nine_class_stage11a/review_id_mapping.csv) holds the exact pair IDs, source paths, HAM image and lesion IDs, protected partition, original dimensions, SHA-256s, and references to the frozen evidence. These original paths are **absent from the blinded gallery**. The [package manifest](../analysis/nine_class_stage11a/package_manifest.json) records hashes of the Stage 3G strong-pair file, Stage 3I pair file and sheet manifest, and Stage 4 source inventory. The generator verified each of the 38 original JPEGs against the Stage 3I and Stage 4 hashes and verified each neutral copy has the same SHA-256.

| Review ID | Fanconic `data/isic/data/test/benign/` filename | HAM image ID | Additional candidate relations outside this 19-pair package |
| --- | --- | --- | ---: |
| R01 | `1443.jpg` | `ISIC_0029401` | 0 |
| R02 | `670.jpg` | `ISIC_0028214` | 0 |
| R03 | `1646.jpg` | `ISIC_0029733` | 1 |
| R04 | `1018.jpg` | `ISIC_0028736` | 0 |
| R05 | `1074.jpg` | `ISIC_0028809` | 36 |
| R06 | `912.jpg` | `ISIC_0028588` | 0 |
| R07 | `878.jpg` | `ISIC_0028509` | 2 |
| R08 | `802.jpg` | `ISIC_0028399` | 0 |
| R09 | `1393.jpg` | `ISIC_0029328` | 3 |
| R10 | `61.jpg` | `ISIC_0027278` | 0 |
| R11 | `311.jpg` | `ISIC_0027662` | 0 |
| R12 | `1297.jpg` | `ISIC_0029182` | 0 |
| R13 | `1191.jpg` | `ISIC_0028981` | 0 |
| R14 | `532.jpg` | `ISIC_0027987` | 0 |
| R15 | `678.jpg` | `ISIC_0028235` | 0 |
| R16 | `575.jpg` | `ISIC_0028045` | 55 |
| R17 | `559.jpg` | `ISIC_0028023` | 4 |
| R18 | `1342.jpg` | `ISIC_0029252` | 0 |
| R19 | `1642.jpg` | `ISIC_0029728` | 0 |

The six records with additional relations account for **101 other candidate pairs**, including **nine previously unresolved uncertain relations**. They are explicitly listed as `NOT_REVIEWED_IN_STAGE11A` in the separate [additional-relations CSV](../analysis/nine_class_stage11a/additional_candidate_relations.csv). A `DISTINCT_PHOTO` decision for one displayed primary pair leaves the other relations open. The package found **zero missing original images** and **zero ambiguous primary mappings**. Fanconic patient/lesion identifiers and the exact paper source version remain unverified.

## Validate a returned decision file

From the project root, run:

```powershell
python src/nine_class_stage11a_review.py --validate "PATH_TO_RETURNED_DECISIONS.csv" --summary-out "analysis/nine_class_stage11a/review_summary_new.json"
```

Choose a **new** summary filename. The validator rejects duplicate/missing/unknown review IDs, altered neutral image IDs or evidence references, unsupported decisions, incomplete reviewer identity/date, non-UTC dates, and metadata on blank decisions. Blank rows are valid and remain unreviewed. It reports decision counts and, for each of the 19 BENIGN source-test records, whether its primary or additional photo relationships still block a photo-identity conclusion. It **always records `approved_eligible=false`**; `DISTINCT_PHOTO` cannot verify another relation, lesion/patient independence, label provenance or rights. The current [initial validation](../analysis/nine_class_stage11a/initial_validation.json) reports **0 reviewed / 19 unreviewed**. No completed human summary exists yet.

The package generator is [`src/nine_class_stage11a_review.py`](../src/nine_class_stage11a_review.py). It refuses an existing output directory and does not rerun the overlap search. `python -m pytest tests/test_nine_class_stage11a.py -q` returned **9 passed**. The tests cover blank and completed synthetic ledgers, invalid choices and dates, missing originals, package paths and hashes, blinded gallery content, and overwrite refusal. The gallery JavaScript passed `node --check`. These synthetic checks do not count as independent human review.

## After the independent reviewer responds

Validate the returned CSV and preserve it as a new immutable review record with the reviewer's identity and date. Reconcile any disagreement with prior evidence without overwriting that evidence. Review the other candidate relations where relevant, especially the nine unresolved relations. Resolve source/version, label and rights evidence before any eligibility approval or protected nine-class split. Training remains blocked until those separate steps are complete.
