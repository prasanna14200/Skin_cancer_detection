# A03 - HAM10000 Source Rights and Image Provenance Investigation

**Retrieved:** 2026-11-23 UTC  
**Scope:** Evidence-only review of the 9,310 HAM10000 records in the frozen EG-VAN exploratory split.  
**Status:** `EVIDENCE_PACKAGE_COMPLETE_NOT_APPROVED`.

## Executive summary

- The official Harvard Dataverse record for DOI `10.7910/DVN/DBW86T` has seven released versions: 1.0, 1.1, 1.2, 2.0, 3.0, 3.1, and 4.0. The versioned `data.dvcore:termsOfUse` field in all seven records has the same SHA-256 and is headed **Creative Commons Attribution-NonCommercial 4.0 International Public License**. The original paper's Table 1 separately lists HAM10000 as CC BY-NC 4.0 with 10,015 images. This verifies collection-level evidence, not the identity or rights of each local image.
- The frozen split contains 9,310 unique HAM image IDs. All 9,310 IDs appear in the official v1 and v4 metadata-file content retrieved through Dataverse; all six common fields (`lesion_id`, `dx`, `dx_type`, `age`, `sex`, `localization`) match the local metadata row exactly. The v4 metadata's additional `dataset` source field is absent from the local metadata CSV.
- All 9,310 local images are readable 600x450 JPEGs. Their recomputed SHA-256 values match both the frozen split and the Stage4 source manifest. **No local image was byte-matched to an official upstream image archive**: 9,310 are identifier-only matches and 0 are verified upstream byte matches. The official files API exposes only archive-level checksums, and the 2,770,088,655-byte image archives were not downloaded.
- A material new discrepancy prevents a confident statement about the local metadata file's raw-byte identity. The local CSV is 563,277 bytes with MD5 `70bb67f71bd23dde0bd2eda4bdcc98e5`. The v1/v2 file listing reports that same MD5 but 683,457 bytes; the actual file body returned for file ID 3172582 is 683,457 bytes with MD5 `e623d553b413b94c0d85936de49d50dc`. For v3/v4, the listing reports 830,428 bytes and MD5 `8f85fb1aa29d80a2797247e434deb79d`, while the retrieved body has MD5 `1d13fed99da9c3e925fb523df87d527e`. These API checksum inconsistencies are unresolved. They do not negate the exact row-field comparisons, but they prevent a verified raw-file identity claim.
- HAM's original seven `dx` classes are preserved in EG-VAN's `original_label` for all 9,310 records. No HAM diagnosis was mapped to `BENIGN` or `MALIGNANT`. Source metadata provides 6,979 lesion IDs, but no patient IDs. No patient-level independence can be established.
- A01 records academic research as the researcher's only declared intended use. That declaration does not establish licensing permission. The approval checklist remains `NOT_APPROVED`, with zero approved images and no approved four-way split; training authorization remains absent.

## 1. Scope and inspected local paths

- Frozen split: `analysis/nine_class_exploratory/exploratory_split.csv` (10,234 total rows; 9,310 rows have `source_dataset=HAM10000`).
- Actual Stage4 source manifest: `analysis/nine_class_stage4/nine_class_source_manifest.csv` (10,015 HAM10000 rows). The requested `analysis/nine_class_final_cohort/nine_class_source_manifest.csv` was not present.
- Local metadata: `data/raw/HAM10000_metadata.csv` (10,015 unique image IDs; 563,277 bytes).
- Local image directories: `data/raw/HAM10000_images_part_1` (5,000 files) and `data/raw/HAM10000_images_part_2` (5,015 files). The frozen split references 9,310 of these files.
- A read-only workspace search found no local `HAM10000*.zip` archive, acquisition receipt, download log, or named acquisition record. This does not rule out records outside the workspace. The local image folder names and `ISIC_*.jpg` filenames are not proof of acquisition provenance.

## 2. Methods and reproducibility

This investigation used read-only PowerShell and .NET operations:

1. `Import-Csv` loaded the frozen split, Stage4 manifest, local metadata, versioned identity ledgers, and review files; records were filtered by `source_dataset=HAM10000` or by exact `ISIC_` IDs from the frozen split.
2. `Get-FileHash -Algorithm SHA256/MD5` recorded local evidence-file hashes. A .NET SHA-256 stream hash was computed for each local HAM image. `.NET System.Drawing.Image::FromFile` checked image readability, dimensions, and format.
3. Harvard Dataverse API GET requests retrieved the dataset version history, each version's metadata and file listing, and only the small metadata file bodies (file IDs 3172582 and 4338392). All 14 versioned metadata/file-list requests returned HTTP 200. No image ZIP or other large archive was downloaded.
4. The article was checked through its DOI/Crossref metadata and Europe PMC full-text XML; the official ISIC data page was also retrieved. Raw response SHA-256 values, status, URLs, and reproducible extracted facts are in `A03_EVIDENCE_REFERENCE_REGISTER.csv`. The version/file extracts and per-image crosswalk are in `A03_UPSTREAM_VERSION_AND_FILE_CROSSWALK.csv`. The prior `HAM10000_DATAVERSE_V4_API_EVIDENCE.json` preserves the full v4 terms-field extract.
5. Local metadata fields and labels were compared by `image_id` with the actual downloaded v1 and v4 metadata contents. The same six fields were compared for each of the 9,310 frozen records.

The image archive MD5 values were inspected before any download. Together, the two official ZIPs are 2,770,088,655 bytes (about 2.77 GB), so they were not downloaded. No training, evaluation, inference, label changes, or identity adjudications were performed.

## 3. Authoritative source, versions, and files

The Dataverse dataset DOI is `10.7910/DVN/DBW86T`, published by Harvard Dataverse. The article is Tschandl, Rosendahl, and Kittler, *The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions*, DOI `10.1038/sdata.2018.161`. The article describes a 10,015-image collection from multiple sources. Dataverse version history returned these released versions:

| Version | Dataverse version ID | Release time (UTC) | File records | Terms-field SHA-256 |
|---|---:|---|---:|---|
| 1.0 | 137377 | 2018-06-04 15:06:27 | 3 | `15d4d8a8ada43a901459bc31feed59238d10e39b2e2814e3284e44b25734132a` |
| 1.1 | 139751 | 2018-07-29 02:45:59 | 3 | same |
| 1.2 | 153725 | 2019-06-17 11:15:12 | 3 | same |
| 2.0 | 195498 | 2020-06-22 20:29:59 | 6 | same |
| 3.0 | 229434 | 2021-01-29 20:57:16 | 6 | same |
| 3.1 | 339585 | 2023-01-14 14:51:07 | 6 | same |
| 4.0 | 340412 | 2023-02-07 10:10:46 | 7 | same |

Across all seven versions, the versioned `data.dvcore:termsOfUse` field is 15,662 Unicode characters and has the displayed SHA-256. Its heading is `Creative Commons Attribution-NonCommercial 4.0 International Public License`. The inspected response has no top-level `data.license` field. `data.dvcore:fileTermsOfAccess.dvcore:fileRequestAccess=false` is an access-request setting, not a license grant. Full file IDs, names, sizes, checksums, version API hashes, and per-image rows are recorded in the crosswalk.

| Dataverse file record | File ID(s) | Listed size | Listed MD5 | Scope |
|---|---:|---:|---|---|
| `HAM10000_images_part_1.zip` | 3172585 | 1,366,522,108 bytes | `4639bfa73ab251610530a97c898e6e46` | Same across all seven versions |
| `HAM10000_images_part_2.zip` | 3172584 | 1,403,566,547 bytes | `da43d6cc50f6613013be07e8986b384b` | Same across all seven versions |
| `HAM10000_metadata.tab`, v1.0-2.0 | 3172582 | 683,457 bytes | `70bb67f71bd23dde0bd2eda4bdcc98e5` | Same file record across v1.0, 1.1, 1.2, 2.0 |
| `HAM10000_metadata.tab`, v3.0-4.0 | 4338392 | 830,428 bytes | `8f85fb1aa29d80a2797247e434deb79d` | Same file record across v3.0, 3.1, 4.0 |

The v2.0+ version file listings also include segmentation and ISIC 2018 challenge files; v4.0 includes `ISIC2018_Task3_Test_GroundTruth.tab`. All 34 version-file records are in the crosswalk. The two image ZIP MD5 values are archive-level checksums only; no per-image checksum or upstream image inventory was returned by the inspected APIs.

### Metadata file checksum discrepancy

The local CSV's size and SHA-256 are 563,277 bytes and `06aee5e603d313ba69de38263053c792a1dff030eb9c44a96ceb477ceefb99a5`; its MD5 is `70bb67f71bd23dde0bd2eda4bdcc98e5`. The official v1/v2 file listing advertises that MD5 but a different size (683,457 bytes). Downloading file ID 3172582 returned 683,457 bytes, MD5 `e623d553b413b94c0d85936de49d50dc`, SHA-256 `50af5cc86d60b5a30a1dbdcf11bba1465717d109811c96dd87fe51b9f9efdefe`. For v3/v4, file ID 4338392 returned 830,428 bytes, MD5 `1d13fed99da9c3e925fb523df87d527e`, SHA-256 `a430c61b1f42eb6b080ded6f7a9dbd2dd707cfe64db318e1ea62d43ab97a6505`, while the file listing advertises MD5 `8f85fb1aa29d80a2797247e434deb79d`.

Thus the listing's v1/v2 checksum, the local MD5, file size, and downloaded datafile body cannot all describe the same bytes. The earlier eligibility-plan statements that v1/v2 metadata was 563,277 bytes and v3/v4 metadata was 690,218 bytes are superseded by this current API recheck; the currently retrieved listings report 683,457 and 830,428 bytes. The cause of the mismatch is **unresolved**. The local metadata file's raw-byte identity to a specific official release is **not established**.

Despite that raw-byte discrepancy, both downloaded official metadata contents have 10,015 rows, and all 9,310 frozen IDs match exactly on `lesion_id`, `dx`, `dx_type`, `age`, `sex`, and `localization`. This is metadata-content correspondence, not an image-byte match or proof of local acquisition history.

## 4. Local image identity and integrity

`A03_LOCAL_IMAGE_HASH_INVENTORY.csv` contains one row per frozen HAM image with absolute and relative path, image ID, SHA-256, byte size, dimensions, format, readability, local-manifest comparisons, and upstream identity status.

| Check | Result |
|---|---:|
| Frozen HAM records and unique IDs | 9,310 / 9,310 |
| Existing, readable local images | 9,310 / 9,310 |
| JPEG, 600 x 450 | 9,310 / 9,310 |
| Local SHA-256 equals frozen split hash | 9,310 / 9,310 |
| Local SHA-256 equals Stage4 manifest hash | 9,310 / 9,310 |
| IDs present in retrieved official v1/v4 metadata | 9,310 / 9,310 |
| Verified local-to-upstream image byte matches | **0** |
| Per-image upstream hashes available in inspected API | 0 |

Image classification: **9,310 `VERIFIED_UPSTREAM_ID_ONLY`; 0 `VERIFIED_UPSTREAM_BYTE_MATCH`; 0 `POSSIBLE_FILENAME_MATCH_ONLY`; 0 `NO_UPSTREAM_MATCH`**. The ID-only result is supported by official metadata records; it does not mean an image file was found inside a downloaded upstream archive. No local archive, archive checksum, or per-image upstream hash establishes which Dataverse version was extracted.

Two exact local duplicate pairs were found by SHA-256; both pairs have the same source lesion ID and remain in one proposed partition:

| Image IDs | SHA-256 | Source lesion ID | Partition |
|---|---|---|---|
| `ISIC_0024366`, `ISIC_0029861` | `b8b37d24e294c5182a1884741c109d8b3bc58edaa993e8c331bd2a15e3e603e6` | `HAM_0002300` | calibration |
| `ISIC_0024777`, `ISIC_0029938` | `b1780747e0ccd3d31652bcf942a0f4bb22af6e058a5dc8b84202e997b7247b8d` | `HAM_0001895` | train |

No exact SHA-256 match between these frozen HAM images and non-HAM rows in the Stage4 manifest was found. This is a local byte comparison; it does not establish identity to an upstream source.

## 5. Metadata, labels, and source attribution

The authoritative v1 and v4 metadata contents agree with the local metadata on the six common fields for all 9,310 frozen records. The v4 metadata also contains a `dataset` source field that the local CSV does not contain. Its values among the frozen records are:

| Official v4 `dataset` field | Frozen records |
|---|---:|
| `vidir_modern` | 3,155 |
| `rosendahl` | 2,060 |
| `vienna_dias` | 374 |
| `vidir_molemax` | 3,721 |

These are source-field values, not an independently verified image-to-contributor or image-to-license map. No equivalence to a paper-table source/license entry is assumed where a separate authoritative crosswalk is absent.

The original diagnosis `dx` distribution and `dx_type` counts for the frozen split are:

| Original `dx` | Count | EG-VAN `class_name` / index |
|---|---:|---|
| `akiec` | 327 | AKIEC / 0 |
| `bcc` | 514 | BCC / 1 |
| `bkl` | 1,099 | BKL / 2 |
| `df` | 115 | DF / 3 |
| `mel` | 883 | MEL / 4 |
| `nv` | 6,230 | NV / 5 |
| `vasc` | 142 | VASC / 6 |

| Original `dx_type` | Count |
|---|---:|
| `histo` | 4,896 |
| `follow_up` | 3,476 |
| `consensus` | 869 |
| `confocal` | 69 |

The local frozen `original_label` matches upstream `dx` for all 9,310 images. The project keeps the seven HAM diagnoses as their own source-defined classes; it does not convert them to `BENIGN` or `MALIGNANT`. The official metadata has 57 missing ages in the frozen subset; `lesion_id`, `dx`, `dx_type`, `sex`, and `localization` are present for all 9,310. Neither the local split nor source metadata provides patient IDs.

## 6. Lesion identity, duplicate evidence, and human decisions

Counts below distinguish source lesion identifiers from photo-pair evidence and patient identity:

| Evidence type | Count | Interpretation |
|---|---:|---|
| Frozen images with a source lesion ID | 9,310 | Source-record identity present |
| Unique source lesion IDs | 6,979 | Not a patient count |
| Lesion-ID groups containing multiple images | 1,779 groups / 4,110 images | Same source lesion ID, not necessarily duplicate photographs |
| Pairwise co-memberships from repeated lesion IDs | 2,951 | Source-reported same-lesion pairings; not patient relationships |
| Patient IDs available | 0 / 9,310 | Patient independence is not established |
| Exact local image duplicate pairs | 2 | Both within one proposed partition; detailed above |

The Stage3 pixel-scored review data has 1,997 pairs touching a frozen HAM image: 1,774 marked `confirmed_direct_pixel_automated` by strict pixel evidence and 223 marked `unresolved_human_review` / candidate-only. All 1,997 source rows say `human_review_status=not_human_reviewed`; automated similarity is not human or patient adjudication. The repository's `confirmed_duplicate_groups.csv` lists 1,774 frozen-HAM memberships in 1,772 groups, including two groups with two frozen HAM records; the Stage3 review summary says no row in that package is human-reviewed.

A separate R6 reconciliation ledger records 13 photo-pair decisions involving a frozen HAM image: 6 `SAME_PHOTO`, 7 `DISTINCT`, and 0 `UNCERTAIN`. These decisions are cross-source pairs; none has two frozen HAM endpoints, and reviewer IDs are blank. A `DISTINCT` photo decision is not evidence that the lesions or patients are distinct. In the 223-row R6 queue subset touching frozen HAM, 210 pairs involving 181 frozen HAM IDs remain unreviewed; the other 13 are represented in the separate reconciled ledger. The proposed Stage3i edge table has 1,848 edges touching frozen HAM: 1,790 `PRIOR_ESTABLISHED_PHOTO_RELATION`, 57 `AI_SUPPORTED_SAME_PHOTO`, and 1 `SUSPECTED_UNRESOLVED_OVERLAP`. These project evidence tiers are not patient-level conclusions, and no candidate was adjudicated by A03.

`A03_LESION_IDENTITY_AND_DUPLICATE_SUMMARY.csv` provides the summary metrics, exact local duplicate pairs, 13 recorded decision rows, and all 210 remaining candidate rows.

## 7. Dataset license and academic intended use

The paper's Table 1 and every inspected Dataverse version's terms field identify **CC BY-NC 4.0** at the dataset/collection level. Crossref's CC BY 4.0 entry and the article's own notice apply to the article, not automatically to its images. The article's CC0 statement is explicitly scoped to "the metadata files made available in this article"; it does not establish that the separate local `HAM10000_metadata.csv` is included. The Dataverse `fileRequestAccess=false` value is not a license.

If CC BY-NC 4.0 applies to a particular item, the license text includes NonCommercial and attribution conditions, including a license link and indication of modifications when sharing licensed material. This is a record of source text, not legal advice or a determination that the license applies to every local image. Attribution by source/contributor for each local image remains unresolved.

A01 declares **academic research only**. Academic intent alone is not permission. Publication of scientific results is distinct from reproducing or redistributing source images or metadata; the available evidence does not separately approve journal/conference publication, public hosting, source-data redistribution, model-weight sharing, predictions, or hosted demos. These use boundaries require researcher clarification and, as appropriate, rights-holder/institutional guidance. No legal conclusion is made.

## 8. Findings and unresolved evidence

| Requirement | Finding | Status | Missing evidence / how to resolve |
|---|---|---|---|
| Dataset origin | The public HAM10000 collection and Harvard Dataverse record are verified. | `VERIFIED` at collection level | None for the public record; local acquisition provenance still needed. |
| Local acquisition location/date/receipt | No workspace receipt, download log, or original archive found. | `UNVERIFIED` | Researcher should provide the original download URL, date, receipt, and source package retained at acquisition. |
| Exact local image version | Local images are named and indexed in official metadata, but image bytes were not matched to an archive. | `NOT ESTABLISHED` | Obtain an authoritative per-image hash manifest, or obtain approval before downloading the large archives and compare all files. |
| Image archive integrity | Official version listings report archive names, sizes, and MD5s; archive contents not inspected. | `PARTIALLY_VERIFIED` | Verify a publisher-provided per-image manifest or compare local files to an authenticated archive. |
| Local metadata raw-file identity | File listing and downloadable content checksums conflict with each other and local size. | `CONTRADICTED` | Ask Dataverse/data curator to confirm canonical file bytes, size, and checksum for each release; repeat download and hash from an independently documented endpoint. |
| Local metadata row correspondence | All 9,310 IDs and six core fields match downloaded v1/v4 metadata contents. | `VERIFIED` for compared fields | Resolve raw-byte checksum conflict before asserting exact metadata-file provenance. |
| Original labels | `dx` and `dx_type` match upstream metadata fields; source `dataset` is present in v4 only. | `VERIFIED` as metadata correspondence | Preserve source diagnosis and source category; no binary equivalence or further remapping is supported. |
| Dataset license | Dataset-level CC BY-NC 4.0 is in paper Table 1 and all seven Dataverse terms fields. | `VERIFIED` at collection/version level | Confirm coverage of each local image/source component and obtain an authoritative contributor/rights crosswalk if required. |
| Per-image rights and attribution | No local per-image rights or attribution map. | `NOT ESTABLISHED` | Obtain authoritative image-to-contributor/terms mapping or a clear dataset-wide rights statement applicable to these files. |
| Academic use, publication, hosting, redistribution, model artifacts | Academic research is declared; use-specific rights decisions are not recorded. | `NOT ESTABLISHED` beyond A01 intent | Researcher must decide each use and resolve ambiguous terms with rights holder/institutional review as appropriate. |
| Patient identity | No patient IDs in source or frozen split. | `NOT ESTABLISHED` | Do not infer identity; obtain an authorized source-level patient/lesion map if one exists, otherwise retain as unknown. |
| Duplicate relationships | Two local exact hash pairs; repeated source lesion IDs; 210 unreviewed pair candidates touching frozen HAM. | `PARTIALLY_VERIFIED` | Any remaining candidates need independent, dated review; do not infer patient identity from similarity. |

Until local image identity, applicable rights, metadata checksum conflict, and researcher decisions are reviewed, the 9,310 records are **not approved for the approved cohort**. They remain potentially reviewable, not cleared.

## 9. Validation and preservation

Validation performed for this package:

- Exactly eight requested deliverables are expected in this directory. The crosswalk contains 9,351 rows: 7 terms/version rows, 34 version-file rows, and 9,310 local-image identity rows. The metadata/label table contains 9,310 unique IDs; the local image inventory contains 9,310 unique IDs; the identity/duplicate summary contains 245 rows. The decision template is intentionally 0 bytes.
- The 9,310 frozen IDs reconcile across split, image inventory, metadata provenance, and crosswalk. No image is classified as an upstream byte match. All local SHA-256 values agree with both local manifests; no image was missing or unreadable.
- The evidence register contains retrievable URLs/statuses/hashes and local references. The only unresolved local API-file integrity issue is explicitly recorded as `CONTRADICTED`, not silently treated as a match.
- Baseline and final SHA-256/size checks cover 37 protected prior files, including all A01 and A02 package files, the eligibility plan, source manifest, frozen split, checklist, HAM metadata, R6 ledgers, and the existing checkpoint/preprocessing file. No protected file changed. The frozen split remains `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740`; checklist remains `e9597aae3d03e3b1d549da474fc7befaa82ec2d7bf3872d0123d4a44359977be`; existing `best.pt` remains `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`.
- Approval remains `NOT_APPROVED`, `approved_eligible_images=0`, and `approved_four_way_split=false`. The checklist has no `training_authorized` property; no training authorization was granted.
- `A03_OUTPUT_SHA256.csv` records SHA-256 values for the other seven deliverables; its own self-hash is excluded to avoid a self-reference.

## 10. Final status

A03 is an **evidence package**, not a dataset decision or legal clearance. Its findings include verified collection-level terms and metadata field correspondence, but local image-byte identity, raw metadata-file identity, per-image rights, acquisition authenticity, and patient identity remain unresolved. The blank researcher decision template is left for the researcher. **Do not proceed to A04 until the researcher has reviewed this evidence and recorded the required decisions.**
