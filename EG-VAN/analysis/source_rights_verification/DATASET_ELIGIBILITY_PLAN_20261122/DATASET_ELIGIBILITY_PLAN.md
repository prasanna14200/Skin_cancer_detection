# EG-VAN Dataset Eligibility & Researcher Decision Resolution Plan

Plan date: 2026-11-22  
Scope: existing local image records and frozen exploratory membership; planning only.  
Current checklist status: `NOT_APPROVED`. This plan neither approves a dataset nor authorizes training.

## Executive summary

The frozen exploratory split contains 10,234 records: 9,310 HAM10000, 845 FANCONIC_LOCAL_UNVERIFIED_VERSION, and 79 SIIM-ISIC 2020 training v2. The project has 200 locally acquired SIIM images in total; the other 121 are outside the frozen exploratory split and remain in the existing identity-candidate quarantine. The 121 are counted separately here, not added to or used to change the split.

For future review only, **9,389 split records** (9,310 HAM10000 and 79 SIIM) are classified `POTENTIALLY_ELIGIBLE_PENDING_REVIEW`. This means only that they may be assessed further under the recorded source terms; it is not legal clearance or eligibility. All remain `NOT_APPROVED`. The other 845 split records are classified `PROVENANCE_UNVERIFIED` and are recommended for exclusion from any approved cohort unless authoritative provenance, rights, and label evidence is obtained. The 121 acquired SIIM records outside the split are `IDENTITY_REVIEW_PENDING`.

The current nine-class cohort is **not realistically ready or eligible**: zero records are approved; the distinct `MALIGNANT` class is entirely dependent on the unresolved Fanconic source; the SIIM `BENIGN` interpretation and aggregate/per-image terms remain pending; and class availability is highly imbalanced. No source label is equated with another source's diagnosis.

## Evidence read and scope

The plan was built from the on-disk independent review, source-rights audit, exploratory split, stage-4 source manifest, SIIM acquisition/identity files, and approval checklist. Primary references:

- `analysis/source_rights_verification/FINAL_INDEPENDENT_REVIEW_20261122/FINAL_INDEPENDENT_REVIEW_REPORT.md`
- `analysis/source_rights_verification/FINAL_INDEPENDENT_REVIEW_20261122/CLAIM_BY_CLAIM_VERIFICATION.csv`
- `analysis/source_rights_verification/FINAL_INDEPENDENT_REVIEW_20261122/UNSUPPORTED_OR_OVERSTATED_CLAIMS.csv`
- `analysis/source_rights_verification/FINAL_INDEPENDENT_REVIEW_20261122/REMAINING_RESEARCHER_DECISIONS.csv`
- `analysis/source_rights_verification/RIGHTS_AUDIT_20261122T071105Z/SOURCE_RIGHTS_RESEARCH_REPORT.md`
- `analysis/source_rights_verification/RIGHTS_AUDIT_20261122T071105Z/SOURCE_RIGHTS_EVIDENCE_REGISTER.csv`
- `analysis/source_rights_verification/RIGHTS_AUDIT_20261122T071105Z/HAM10000_LICENSE_SCOPE_ANALYSIS.md`
- `analysis/source_rights_verification/RIGHTS_AUDIT_20261122T071105Z/FANCONIC_PROVENANCE_INVESTIGATION.md`
- `analysis/source_rights_verification/RIGHTS_AUDIT_20261122T071105Z/UNRESOLVED_RIGHTS_QUESTIONS.csv`
- `analysis/nine_class_final_cohort/approval_checklist_v1.json`

The final-review claim register contains 104 rows, including 79 individually re-fetched SIIM API records. The review retained 11 researcher decisions as pending. The 10,234-row split and all labels/partitions were treated as read-only.

## Dataset-specific findings

### HAM10000

- The paper lists the 10,015-image collection as CC BY-NC 4.0. The article's CC BY 4.0 notice and its CC0 waiver for metadata made available in the article are distinct scopes.
- A fresh official Harvard Dataverse version-file API check found the same CC BY-NC 4.0 terms hash for versions 1.0–4.0. The official image archive checksums are stable across these versions: `HAM10000_images_part_1.zip` MD5 `4639bfa73ab251610530a97c898e6e46`, and `HAM10000_images_part_2.zip` MD5 `da43d6cc50f6613013be07e8986b384b`.
- The local `data/raw/HAM10000_metadata.csv` is 563,277 bytes with MD5 `70bb67f71bd23dde0bd2eda4bdcc98e5`. This matches the official Dataverse v1.0/v2.0 record's reported original CSV size and MD5. The v3.0/v4.0 metadata record instead reports original size 690,218 bytes and MD5 `8f85fb1aa29d80a2797247e434deb79d`; the local CSV is therefore not byte-identical to that v3/v4 original. The v1/v2 MD5 match supports file-record correspondence but does not establish acquisition history or independently grant rights; the metadata file's use still needs researcher review.
- The 9,310 local image IDs match IDs in the 10,015-row local metadata file. The two official ZIP checksums are available, but local extracted image bytes have not been compared against the contents of those archives. No local image is individually rights-cleared by an ID join.
- All 9,310 split rows have lesion IDs (6,979 unique values) but no patient IDs. The split has zero known group crossings; the project provenance still records unknown patient/photo identity. Group-aware partitioning is not proof of independent patient or photographic identity.
- Existing source-defined classes are retained exactly: `akiec`, `bcc`, `bkl`, `df`, `mel`, `nv`, and `vasc`. No class mapping is changed here.

Official version-file endpoints checked on 2026-11-22:

- `https://dataverse.harvard.edu/api/datasets/:persistentId/versions/1.0/files?persistentId=doi%3A10.7910%2FDVN%2FDBW86T`
- `https://dataverse.harvard.edu/api/datasets/:persistentId/versions/2.0/files?persistentId=doi%3A10.7910%2FDVN%2FDBW86T`
- `https://dataverse.harvard.edu/api/datasets/:persistentId/versions/3.0/files?persistentId=doi%3A10.7910%2FDVN%2FDBW86T`
- `https://dataverse.harvard.edu/api/datasets/:persistentId/versions/4.0/files?persistentId=doi%3A10.7910%2FDVN%2FDBW86T`

### SIIM-ISIC 2020 training v2

- The official Challenge page identifies aggregate CC BY-NC 4.0 terms and citation DOI `10.34970/2020-ds01`. The official ISIC Terms describe contributor-selected image licences separately. The interaction for the planned activities remains a researcher/legal decision; no individual code is said to override the aggregate terms.
- All 79 split records were independently matched to live API ID/license/attribution records: 41 `CC-BY`, 38 `CC-BY-NC`. Their local image hashes match the local source-attribution register. Individual API codes do not state licence versions.
- The local acquisition register contains 200 SIIM records, all with source target `0`/label `benign`. The other 121 are outside the frozen split; the existing candidate register flags all 121 as `QUARANTINE_CANDIDATE_RELATION`, all 200 as `UNREVIEWED`, and all 200 as `NOT_APPROVED`. The 79 split rows have no automated candidate relation, but they are also `UNREVIEWED` and not approved. No-candidate status is not proof of independence.
- A non-downloading HTTP HEAD request to the official fixed Challenge ZIP returned `Content-Length: 24707698022` and ETag `ebb879d3b9be0f5b4515e28dc8ebbb88-472`; no SHA-256 checksum header was returned. The multipart-style ETag is recorded as object metadata, not treated as a verified file checksum. No local image bytes were compared to the fixed ZIP.
- Source-defined `BENIGN` is retained as the existing exploratory label only. It is not treated as equivalent to any HAM10000 diagnosis or Fanconic label.

Official sources:

- `https://challenge.isic-archive.com/data/#2020`
- `https://challenge.isic-archive.com/terms-of-use/`
- `https://doi.org/10.34970/2020-ds01`
- `https://isic-archive.s3.amazonaws.com/challenges/2020/ISIC_2020_Training_JPEG.zip`

### FANCONIC_LOCAL_UNVERIFIED_VERSION

- All 845 split images remain `UNVERIFIED_ORIGIN_PENDING`. The local folder/source label is `malignant`; the source package, version, acquisition receipt, remote checksums, image IDs, contributor permissions, and clinical label provenance are not established.
- All 845 have blank image, patient, and lesion identifiers. Filename, folder, size, and the possible Kaggle v4 metadata match do not establish origin, rights, or diagnosis.
- Recommend excluding these records from any approved cohort unless authoritative package/acquisition evidence, file-level checksum mapping, contributor terms, and label provenance are obtained and reviewed. This is a hold recommendation, not an irreversible deletion or label change.

## Eligibility classification and counts

The record-level matrix assigns exactly one allowed classification to each of 10,355 locally relevant images: the 10,234 frozen-split records plus the 121 acquired SIIM records outside that split.

| Classification | Records | Meaning |
|---|---:|---|
| `POTENTIALLY_ELIGIBLE_PENDING_REVIEW` | 9,389 | 9,310 HAM and 79 SIIM split records that may be considered after all open rights, identity, label-policy, and researcher decisions are resolved. |
| `PROVENANCE_UNVERIFIED` | 845 | Fanconic split records; source/version and label origin are not established. Recommend exclude from approved cohort until resolved. |
| `IDENTITY_REVIEW_PENDING` | 121 | Acquired SIIM records outside the frozen split with automated candidate relations and no human adjudication. |
| **Currently approved** | **0** | Approval checklist remains `NOT_APPROVED`; no current training eligibility is established. |

Open blockers overlap; counts by blocker must not be added as if they were disjoint records:

- **Rights/intended-use review open:** all 10,355 local records. HAM exact image file-level scope, SIIM aggregate/per-image interaction, and Fanconic permissions have not received a researcher decision for the planned use.
- **Exact source-file identity evidence incomplete:** 9,310 HAM extracted images (archive MD5s exist but were not compared to local bytes), 200 SIIM images (fixed ZIP byte identity is unverified), and 845 Fanconic images (origin itself is unverified).
- **Explicit SIIM human identity review pending:** 200/200 acquired records: 121 candidate-relation records and 79 no-candidate records, all `UNREVIEWED`. The 3,268 candidate edges include 4 `PROBABLE_PHOTO_RELATION` and 3,264 `UNCERTAIN`; all are unreviewed. None of those edges involve the 79 split SIIM IDs.
- **Patient IDs absent:** 10,155 records (all 9,310 HAM and 845 Fanconic). HAM lesion IDs exist for all 9,310; Fanconic lesion IDs are absent for all 845.
- **Image/lesion/patient IDs absent:** 845 Fanconic records.
- **Source-label policy / label provenance pending:** 200 SIIM records require researcher acceptance of the source-defined `benign` use; 845 Fanconic labels lack verified provenance. In the frozen split this affects 79 SIIM plus 845 Fanconic records.
- **Recommended exclusion under current evidence:** 845 Fanconic images. No other record is approved; the 121 SIIM candidate records remain quarantined outside the frozen split pending review.

See `CLASS_LEVEL_ELIGIBILITY_SUMMARY.csv` for reconciled source/class counts and the explicitly non-additive blocker columns.

## All 11 researcher decisions

All remain `PENDING_RESEARCHER_REVIEW`; this plan does not fill or change the researcher template:

1. `HAM-FILE-IDENTITY` — establish image archive identity and record that the local metadata CSV matches the official v1/v2 original-file MD5, not the v3/v4 original.
2. `HAM-IMAGE-RIGHTS` — determine source-level/per-image conditions and attribution implications for the local images.
3. `HAM-INTENDED-USE` — document research/publication, commercial, redistribution/adaptation, model, and demo use.
4. `FAN-ORIGIN` — obtain authoritative source/version/acquisition evidence and verified file checksums.
5. `FAN-IMAGE-RIGHTS` — establish contributor licences, attribution, and permitted uses for every image.
6. `FAN-INTENDED-USE` — review intended publication, commercial, redistribution, model, output, and demo uses only after origin/terms are established.
7. `SIIM-TERMS-INTERACTION` — record researcher/legal interpretation of aggregate versus contributor terms for the actual planned use.
8. `SIIM-INDIVIDUAL-VERSION` — obtain versioned evidence if needed; API codes alone do not state versions.
9. `SIIM-PACKAGE-IDENTITY` — obtain a publisher checksum/manifest or compare local bytes with the fixed Challenge package.
10. `SIIM-INTENDED-USE` — decide the planned commercial, redistribution, modification, model, prediction, and demo use.
11. `GLOBAL-REVIEW` — complete named researcher review, evidence references, exact intended use, label policy, and any legal interpretation.

The tracker and action plan specify owners' next evidence tasks and acceptance criteria without making any decision for the researcher.

## Ordered next actions

1. **Define intended use and decision criteria.** State whether the project is noncommercial research/publication only or includes commercial use, redistribution, models, predictions, or a public demo. Route unresolved licence interpretation to the researcher/legal reviewer.
2. **Resolve HAM file identity.** Use the official v1/v2 metadata match as evidence for that CSV; retrieve/verify the exact source archive or otherwise establish source provenance for each local HAM image against the official archive files. Keep the v1/v2 versus v3/v4 metadata difference explicit.
3. **Resolve Fanconic or exclude it.** Require versioned authoritative package/acquisition receipts, remote and local file hashes, image identifiers, contributor terms, and label provenance. If unavailable, keep the 845 records out of any approved cohort.
4. **Resolve SIIM terms and package evidence.** Obtain a meaningful official ZIP checksum/manifest and verify the 79 local split images; query and retain official API records for the remaining 121 if they are ever reconsidered; document the aggregate/per-image terms decision without assuming an override.
5. **Complete identity and label review.** Independently adjudicate SIIM candidates and establish the source-defined label policy; do not infer independence from no-candidate results or equate source labels with histological diagnoses.
6. **Only after evidence review, update approval materials through the authorized researcher process.** Preserve this frozen split and current checklist unless the user separately authorizes a new, versioned cohort/split. No training occurs before a separate approval.

## Risks and limitations

- A record classified as potentially eligible is not legally cleared, source-byte verified, independently identity-reviewed, or accepted for training.
- Local image hashes demonstrate consistency with local manifests, not identity to a publisher's archive.
- HAM file-level MD5s are available at official archive scope; the local extracted JPEGs were not matched to the ZIP contents.
- The fixed SIIM object's ETag is not treated as SHA-256; no verified package checksum was identified in the checked page or HEAD response.
- Fanconic has no authoritative acquisition or contributor-rights mapping; its source-folder label does not establish a clinical diagnosis.
- 121 SIIM candidate-relation records are outside the split and remain quarantined. No records were silently removed or moved by this plan.
- Numeric four-way preview counts and the prior preflight are planning evidence only; the stage-6 gate rejects the preview and the approval checklist reports zero approved eligible images.
- This is not legal advice, dataset approval, or training authorization.

## Integrity statement

Only the seven requested plan deliverables are written under this new directory. No source, label, split, checkpoint, original audit, identity decision, or approval file is edited. Final validation compares the protected source-rights manifest to the current workspace and rechecks the split, checklist, preprocessing configuration, existing checkpoint, and identity-decision files.

Final plan state: **`ELIGIBILITY_PLAN_COMPLETE_NOT_APPROVED`** if all required deliverables and integrity checks pass. This state means the plan is complete; it does not approve any record.
