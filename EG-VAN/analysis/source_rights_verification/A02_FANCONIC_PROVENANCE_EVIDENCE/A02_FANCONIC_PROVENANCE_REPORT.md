# A02 — Fanconic Origin and Version Evidence Report

**Review date:** 2026-11-23  
**Scope:** Read-only provenance, local-file identity, label, and rights evidence review for the 845 records identified as `FANCONIC_LOCAL_UNVERIFIED_VERSION`.  
**Status:** Evidence package prepared for researcher review. This is not a dataset approval, legal clearance, or training authorization.

## Executive summary

The local project contains 845 Fanconic-tagged records in the exploratory split. Their current local files are present, readable JPEGs at 224 × 224 pixels in RGB mode. Fresh SHA-256 values for all 845 files match both the exploratory split and the Stage4 source manifest. No exact duplicate SHA-256 values occur within these 845 files, and none matches another source row in the Stage4 manifest.

The current public Kaggle listing is a **strong metadata-level candidate** for the files' source: it reports the Fanconic dataset title, owner Claudio Fanconi, current version 4, and 2019-06-19 update date. On 2026-11-23, its paginated public file-list API returned 6,594 unique path/size entries. All 845 affected local paths map to a version-4-listing path with the same relative path and byte size. The sorted remote `name,size` listing hash is `7a201f33b916f2ed141d53b67877dac3938b97f96e9b1250b9797c4e72dbcbdb`, consistent with the previously documented listing.

**This does not verify that any local file is byte-identical to Kaggle version 4 or prove that version 4 was the package acquired for EG-VAN.** Kaggle's listing supplies no per-file SHA-256/content checksum. No acquisition receipt/date, original local archive, local-to-upstream content crosswalk, original ISIC image IDs, patient/lesion IDs, or per-image contributor-license mapping was found. The exact upstream origin and local version therefore remain **UNVERIFIED** for all 845 records.

The Kaggle metadata lists `licenseName=Unknown`. Its description points to ISIC Archive rights and includes an uploader warning against monetization; these statements are not a per-image license grant or verified permission for academic research. The PLOS article describing a 3,297-image Kaggle collection reports 1,800 benign and 1,497 malignant 224 × 224 RGB images and says rights are bound to the ISIC Archive, but it does not identify these 845 local files individually. ISIC terms describe contributor-selected licenses per image; no source IDs exist here to determine which terms apply.

**Recommendation:** Keep all 845 records excluded from approved-cohort consideration until authoritative origin/version and per-file identity, label provenance, and applicable rights evidence are supplied and reviewed. No source was approved, no labels or identity decisions were changed, and no training, evaluation, or inference was performed.

## Scope and actual file locations

The requested `analysis/nine_class_final_cohort/nine_class_source_manifest.csv` was not present. The actual Stage4 manifest is `analysis/nine_class_stage4/nine_class_source_manifest.csv` (13,312 rows; columns: `image_path`, `source_dataset`, `original_label`, `class_name`, `class_index`, `image_id`, `lesion_id`, `patient_id`, `source_split`, `sha256`, `overlap_group`, `duplicate_overlap_evidence_tier`, `provisional_eligibility_status`).

Other inspected records and schemas:

| Actual path | Rows | Relevant columns |
|---|---:|---|
| `analysis/nine_class_exploratory/exploratory_split.csv` | 10,234 total; 845 Fanconic | `image_path`, `source_dataset`, `original_label`, `class_name`, `class_index`, `image_id`, `lesion_id`, `patient_id`, `source_split`, `sha256`, `overlap_group`, `approval_status`, `split`, `research_status` |
| `analysis/source_rights_verification/DATASET_ELIGIBILITY_PLAN_20261122/DATASET_SOURCE_ELIGIBILITY_MATRIX.csv` | 10,355 | `record_key`, `source_dataset`, `image_path`, `source_defined_label`, `image_id`, `lesion_id`, `patient_id`, `existing_human_review_status`, `existing_approval_status`, `eligibility_classification`, `blocker_codes`, `evidence_reference`, `recommended_disposition` |
| `analysis/source_rights_verification/DATASET_ELIGIBILITY_PLAN_20261122/ELEVEN_RESEARCHER_DECISIONS_TRACKER.csv` | 11 | `decision_id`, `dataset`, `current_status`, `required_evidence_or_action`, `evidence_already_available_and_gap`, `approval_effect`, `plan_disposition` |
| `analysis/source_rights_verification/A01_INTENDED_USE_EVIDENCE_20261122/A01_INTENDED_USE_RESEARCHER_DECISION_COMPLETED_DRAFT.md` | Markdown | A01 states academic research as the declared project purpose; it does not grant data permissions or authorize model work. |

All 845 exploratory rows are locally labeled `original_label=malignant`, mapped to `MALIGNANT` / class index 8. The local source split is 680 `train` and 165 `test`; exploratory partitions are 512 `train`, 84 `validation`, 84 `calibration`, and 165 `test`. These are unapproved planning assignments, not evidence of clinical truth or eligibility.

## Acquisition trail findings

| Question | Finding | Evidence status | Evidence limit |
|---|---|---|---|
| Original acquisition location | Local files are under `data/isic/data/{train,test}/malignant/`. Kaggle version 4 is a plausible metadata-level source candidate. | `PARTIALLY_VERIFIED` | A local folder path is not a download record; the exact origin is unverified. |
| Acquisition date | No local receipt, log, or date was found in the inspected project provenance records. | `UNVERIFIED` | Kaggle's version update date is not the local acquisition date. Ask the original acquirer/maintainer for download or transfer records. |
| Original name and version | Kaggle currently reports **Skin Cancer: Malignant vs. Benign**, current version 4, last updated 2019-06-19. | `VERIFIED` for the listing; `UNVERIFIED` for local version | The EG-VAN paper and local files do not state which exact package version was used. |
| Publisher / contributor | The Kaggle listing names Claudio Fanconi as owner/creator. The original ISIC image contributors are not identified locally. | `VERIFIED` for Kaggle listing metadata; `UNVERIFIED` for image contributors | Kaggle uploader identity does not establish ownership or rights in underlying images. |
| Download URL / receipt | Kaggle's version-4 page exposes a download URL; no EG-VAN acquisition receipt or download log was found. | `PARTIALLY_VERIFIED` | A public download endpoint does not prove that these local bytes were obtained from it. |
| Original archive name, size, checksum | The version-4 page's structured data reports a downloadable ZIP of **340,467,838 bytes**. The archive filename and SHA-256 were not exposed in the retrieved metadata. Kaggle's dataset view reports `totalBytes=171,612,705`; the file-list API reports 6,594 paths totaling 343,225,410 bytes, including mirrored paths. These are distinct listing/archive measures and are not checksums. | `PARTIALLY_VERIFIED` for listed size; `UNVERIFIED` for archive identity/checksum | No archive was downloaded. A 340 MB download is substantial and requires researcher confirmation before retrieval. |
| Dataset documentation and license | Kaggle API reports `licenseName=Unknown`. The description says rights are bound to the ISIC Archive and includes the uploader's monetization warning. | `VERIFIED` as statements on the listing; permission `UNVERIFIED` | These do not identify per-image contributor licenses or establish permission for the local files or declared academic use. |
| Local transformations | The 845 files currently decode as JPEG, RGB, 224 × 224. | `VERIFIED` for current file properties; history `UNVERIFIED` | There is no transform/extraction log or upstream byte comparison. Similar dimensions to the article are not proof of identical files or transformations. |
| Claimed Kaggle match | Exact mapped relative path and byte size match current version-4 file-list metadata for 845/845 records. | `PARTIALLY_VERIFIED` | A path/size match is only a possible match. No upstream per-file checksum or verified archive crosswalk exists. |

### Public listing metadata revalidation

The current public dataset-view API reports: title `Skin Cancer: Malignant vs. Benign`; owner `Claudio Fanconi`; current version `4`; `lastUpdated=2019-06-19T21:51:11.657Z`; `totalBytes=171612705`; and `licenseName=Unknown`. The version notes say the data set was split into train and test. The page's structured data reports a version-4 ZIP of 340,467,838 bytes.

The file-list API was read as public metadata only, in 33 pages of up to 200 rows. It returned 6,594 unique paths and sizes; no image files or archive contents were fetched. For each affected local path, the leading local prefix `data/isic/` maps to the path listed by Kaggle, and its byte size equals the listing value. The listing contains no per-file SHA-256/content checksum. The current listing therefore improves the provenance lead but does not establish local acquisition authenticity or byte identity.

The earlier local recovery report documents that the full local canonical tree and mirror had previously been compared to the version-4 path/size listing. This A02 revalidation independently establishes the same path/size correspondence for the 845 records in scope; it does not regenerate or independently verify every entry in those two full trees.

## File-level identity and duplicate findings

| Measure for the 845 in-split records | Result |
|---|---:|
| Rows accounted for in each generated per-record CSV | 845 |
| Missing local files | 0 |
| Unreadable files | 0 |
| JPEG, RGB, 224 × 224 | 845 |
| Total local file bytes | 32,176,340 |
| Recomputed SHA-256 matches exploratory split and Stage4 manifest | 845 / 845 |
| Exact SHA-256 duplicate groups within these 845 | 0 |
| Exact SHA-256 matches to other sources in the Stage4 manifest | 0 |
| Exact relative-path-and-size candidates in current Kaggle v4 listing | 845 |
| Verified upstream byte matches | 0 |
| Files with no established origin | 845 |

The exact file results are in `A02_LOCAL_FILE_HASH_INVENTORY.csv`; per-file Kaggle listing candidates and their limits are in `A02_UPSTREAM_IDENTITY_CROSSWALK.csv`. All crosswalk rows are marked as possible path/size matches, not verified content matches.

Existing overlap evidence also needs to be retained:

- Four prior-established **same-source** photo-relation edges touch four of these 845 paths. The counterparts are other local Fanconic binary paths; the evidence is not an upstream identity link.
- A prior cross-source perceptual screen contains **127 candidate pairs** involving **51** of the 845 local paths: 33 candidate pairs with PH2 and 94 with SIIM-ISIC 2020. These are perceptual candidates only, not confirmed duplicate or patient/lesion identity decisions.
- The exact-source-manifest SHA comparison found no cross-source byte-identical matches among the 845. This does not rule out recompressed, resized, transformed, or otherwise near-duplicate images.

The pairwise evidence and statuses are recorded in `A02_LABEL_AND_IDENTITY_PROVENANCE.csv`; source evidence is cited in the register. No existing identity decision was changed or upgraded.

## Label and identity provenance

The local file path/folder and manifests record the source label `malignant`; the 845 records in the exploratory split are mapped to `MALIGNANT`. This confirms the local assignment only. It does not establish the upstream label source, diagnostic criteria, clinical ground truth, or label adjudication. The PLOS ONE study reports a binary benign/malignant Kaggle dataset and its counts/dimensions; it does not supply a per-image label crosswalk for the EG-VAN files.

For all 845 records, the local exploratory and Stage4 manifests have blank `image_id`, `patient_id`, and `lesion_id`; no source ISIC identifier or contributor attribution was found. Numeric filenames are local filenames, not verified ISIC identifiers. No patient identity is inferred.

## Rights, academic research, attribution, and intended use

The researcher's A01 declaration is **academic research**. It does not grant rights or establish that a dataset's terms permit the proposed work.

- Kaggle currently lists the dataset license as `Unknown`. The uploader's description says rights are bound to ISIC Archive rights and includes a warning against monetizing models made using the data. This is listing/uploader text, not a per-image license record or a legal determination.
- The PLOS ONE article's data statement reports that the underlying data rights are bound to the ISIC Archive. Its article's CC BY notice is the article's publication license; it does not itself license the 3,297 underlying images or these 845 local files.
- Official ISIC terms describe contributor-selected CC0, CC BY, or CC BY-NC licenses for images. Because the local records have no source image IDs or attribution map, the applicable contributor, license, attribution, and version cannot be determined for any individual file.
- Therefore, permission for academic research is **not established**. Attribution requirements, publication, public hosting, redistribution, modification, and model/output use are also unresolved. No legal conclusion is made.

## Evidence classifications

| Finding | Status | Meaning |
|---|---|---|
| 845 local records, current labels/paths/partitions, readable file properties and local SHA-256 values | `VERIFIED` | Verified about the current local records and bytes only. |
| Kaggle listing title, owner, current version, update date, `licenseName=Unknown`, and its published description | `VERIFIED` | Verified about what the current public listing states, not local provenance or rights. |
| All 845 mapped paths and byte sizes occur in the current version-4 metadata listing | `PARTIALLY_VERIFIED` | Strong metadata-level candidates; content identity remains unverified. |
| Local acquisition date, receipt, exact archive, and acquisition authenticity | `UNVERIFIED` | No supporting record located in the inspected project evidence. |
| Local-to-upstream file byte identity and exact local package version | `UNVERIFIED` | No official per-file checksums or archive comparison. |
| Original clinical label definitions, per-image source IDs, and patient/lesion identity | `UNVERIFIED` | Local folder labels exist, but authoritative per-image linkage does not. |
| Applicable license, per-image attribution, academic research permission, and downstream uses | `UNVERIFIED` | Listing says `Unknown`; ISIC contributor licenses cannot be mapped to these files. |
| Existing PH2/SIIM perceptual candidates | `PARTIALLY_VERIFIED` | Existing candidate records were inspected; they are not adjudicated identity findings. |
| Contradictory authoritative evidence | None identified in this scope | Lack of a contradiction is not evidence that origin or rights are established. |

## Minimum missing evidence and how to obtain it

1. **Acquisition authenticity and date:** Ask the original acquirer or project maintainer for the Kaggle download receipt/account history, acquisition date, exact URL/version, archive filename, and any transfer or extraction log. If no record exists, retain acquisition authenticity as unresolved.
2. **Exact local package/version and content identity:** Obtain researcher confirmation before downloading the version-4 archive; the listing reports 340,467,838 bytes. Preserve the retrieved archive and its independently computed SHA-256, then perform a read-only archive-to-local per-file SHA-256 crosswalk. A new copy can verify correspondence to that retrieved archive, but cannot by itself prove it was the historical EG-VAN acquisition.
3. **Upstream file checksums and source IDs:** Request a publisher-maintained checksum manifest and per-image original ISIC IDs/metadata from the Kaggle owner or cited study authors. If none exists, investigate potential ISIC matches using an authorized, documented process; a perceptual match alone must remain a candidate pending independent review.
4. **Label provenance:** Request the source label table, original label definitions/criteria, per-image identifiers, annotation/clinical provenance, and any label transformations from the dataset owner/authors. Do not equate the folder label with verified clinical diagnosis.
5. **Patient/lesion grouping:** Request authorized source patient/lesion identifiers or a documented grouping crosswalk. Do not infer identity from filenames or image similarity.
6. **Applicable terms and attribution:** Obtain authoritative terms and the contributor-selected license/attribution for each mapped ISIC image, plus any Kaggle dataset access/use terms or separate agreement. Have the researcher review the exact proposed academic activities and unresolved publication/hosting/redistribution questions; seek rights-holder or legal interpretation where needed.
7. **Transformation provenance:** Request original archive contents and extraction/resizing/conversion scripts or logs. Compare current bytes with the retrieved archive before attributing any transformation to the local pipeline.
8. **Existing overlap candidates:** Preserve the four same-source relations and 127 PH2/SIIM perceptual candidates for independent adjudication only if the researcher determines these records remain under consideration. Do not silently drop or relabel any record.

## Researcher decision status and recommendation

The tracker entries `FAN-ORIGIN`, `FAN-IMAGE-RIGHTS`, and `FAN-INTENDED-USE` remain `PENDING_RESEARCHER_REVIEW`. The approval checklist remains `NOT_APPROVED`; no source record is approved. A01's academic research declaration remains unchanged and is not an A02 provenance or rights decision.

**Recommended disposition:** all **845** records remain excluded from approved-cohort consideration until the missing origin/version, identity, label, rights, and intended-use evidence is resolved and formally reviewed. If authoritative evidence cannot be obtained, retain the exclusion. Do not substitute another source or silently change the split.

**A02 review readiness:** `READY_FOR_RESEARCHER_REVIEW_AS_EVIDENCE_ONLY`. The decision itself remains pending. No A03 work is included.

## Integrity and restrictions

The only new project files for this task are the seven deliverables in this A02 folder. The source manifest, exploratory split, eligibility matrix, decision tracker, A01 draft, approval checklist, preprocessing configuration, existing images, and checkpoints were read-only. The 845 current image SHA-256 values match the two source manifests. No archive or image was downloaded; no data, labels, split, identity decision, approval state, or model artifact was changed. No training, evaluation, or inference occurred.

`A02_OUTPUT_SHA256.csv` records the SHA-256 and byte size of the other six deliverables; the manifest does not hash itself.

## Evidence references

See `A02_EVIDENCE_REFERENCE_REGISTER.csv` for source URLs, local supporting files, scope, status, and limitations for each material claim.
