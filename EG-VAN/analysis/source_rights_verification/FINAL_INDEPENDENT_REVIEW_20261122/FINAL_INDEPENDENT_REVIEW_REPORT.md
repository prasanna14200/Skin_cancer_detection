# Final Independent Source-Rights Audit Review

Review date: 2026-11-22  
Reviewed audit: `analysis/source_rights_verification/RIGHTS_AUDIT_20261122T071105Z`  
Scope: read-only evidence review; no original audit file or protected project data was changed.

## Executive summary

**Final status: `AUDIT_EVIDENCE_CONSISTENT_WITH_LIMITATIONS`**

The material rights-scope statements in the corrected audit are supported by the inspected paper, versioned Dataverse API response, official ISIC Challenge page and Terms of Use, Creative Commons legal text, and local records. The review independently re-fetched all 79 SIIM API records and matched their IDs, contributor-license codes, and attribution to the local source-attribution register. Counts were 41 `CC-BY` and 38 `CC-BY-NC`.

The audit correctly keeps HAM10000 article, article-metadata, and image-collection scopes separate; does not claim that local HAM image bytes match Dataverse; does not treat SIIM per-image API fields as overriding the aggregate Challenge license; and keeps Fanconic origin and rights unresolved. No source is approved and no legal clearance is established.

Limitations remain material: HAM local-file identity and per-image provenance are unverified; SIIM local bytes were not compared with the fixed Challenge ZIP and the individual API license codes do not state versions; Fanconic has no authoritative acquisition/provenance or license bridge. These limitations are stated in the audit rather than hidden.

## Dataset-by-dataset conclusions

### HAM10000

- The [original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6091241/) Table 1 explicitly lists HAM10000 as CC BY-NC 4.0 with 10,015 images. Its article notice separately applies CC BY 4.0 to the article, subject to third-party credit lines, and says the CC0 waiver applies to “the metadata files made available in this article.” That wording does not establish that the separate local `HAM10000_metadata.csv` is covered by the waiver.
- The [Harvard Dataverse v4.0 API](https://dataverse.harvard.edu/api/datasets/:persistentId/versions/4.0/metadata?persistentId=doi%3A10.7910%2FDVN%2FDBW86T) was re-fetched. It returned `status=OK`, version `4.0`, and the exact field `data.dvcore:termsOfUse`. Its 15,662-character value and SHA-256 `15d4d8a8ada43a901459bc31feed59238d10e39b2e2814e3284e44b25734132a` match `HAM10000_DATAVERSE_V4_API_EVIDENCE.json`. The field heading is `Creative Commons Attribution-NonCommercial 4.0 International Public License`; `data.license` is absent.
- A fresh local join found 9,310 unique split IDs, all present among the 10,015 local metadata IDs. This is not package-byte identity or rights verification for each image.
- No unsupported claim of local byte identity was found. Per-image/source-level rights and the local metadata file’s exact terms remain unresolved.

### SIIM-ISIC 2020 training v2

- The [official Challenge data page](https://challenge.isic-archive.com/data/#2020) lists 33,126 training records, metadata v2, links the aggregate data to [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), and gives the required citation with DOI `10.34970/2020-ds01`.
- The [official ISIC Terms of Use](https://challenge.isic-archive.com/terms-of-use/) say users assent by access or use, the Site can be used without creating an account, and uploading images or annotations requires an account. Contributors select CC0, BY, or BY-NC for an image; image use is subject to that contributor license. The separate CC0 scopes for annotations and the Site Database are not treated as image licenses.
- All 79 API endpoints returned HTTP 200 on this review. Their `isic_id`, `copyright_license`, and `attribution` values matched both the existing revalidation CSV and the local `acquired_source_attribution_v1.csv`; all 79 corresponding local image hashes also matched that register. Counts: 41 `CC-BY`, 38 `CC-BY-NC`. The API response has no per-image license-version field.
- The aggregate/per-image terms interaction is explicitly left for researcher review; the audit does not claim that an individual `CC-BY` code overrides the aggregate CC BY-NC 4.0 terms. The local images’ byte identity to the fixed Challenge JPEG ZIP remains unverified.

### FANCONIC_LOCAL_UNVERIFIED_VERSION

- The exploratory split contains 845 Fanconic rows, all with blank image, patient, and lesion IDs and the source/folder label `malignant`. The audit’s evidence status is `UNVERIFIED_ORIGIN_PENDING`; no image is marked rights-approved.
- The possible Kaggle v4 match is described as a metadata/provenance lead only. The local recovery document records a prior metadata-only query and path/name/size comparison, but there is no authoritative acquisition receipt, verified remote checksum, original image-ID mapping, or contributor-license mapping. The review did not re-fetch Kaggle metadata and does not rely on it as licensing evidence.
- No research, commercial, redistribution, or derivative-use permission is established. The exact upstream source, version, file identity, and applicable terms remain unresolved.

## Claim-by-claim findings

`CLAIM_BY_CLAIM_VERIFICATION.csv` records the report claims and all 79 per-image SIIM checks. The findings use only `VERIFIED`, `PARTIALLY VERIFIED`, `UNVERIFIED`, `CONFLICTING`, and `UNSUPPORTED`. No conflicting official source was found. The material licensing and attribution claims are verified within their stated scopes; local-file rights and identity claims remain partial or unverified as noted.

## Evidence limitations and corrections

No material correction to the report’s dataset-license interpretation is required. The CC license summaries match the official legal text, with scope/applicability and unresolved-use questions kept explicit.

Two statements merit qualification if the original audit is edited later; the original audit files were **not** changed:

1. **Historical no-training assertion.** The report states that no training or evaluation was run. This review ran no training or evaluation, and the protected-file inventories show no protected file changes over their recorded interval. Static files cannot establish whether an execution occurred outside that interval or workspace. Suggested replacement:

   > “No training or model evaluation was performed as part of this source-rights audit. The protected-file hash comparison found no changes over the recorded audit interval; it cannot establish whether execution occurred elsewhere or before that interval.”

2. **Fanconic citation precision.** The evidence-register `FAN-ORIGIN-LEAD` row links to the versioned Kaggle listing, while the local recovery document records the prior `datasets/view` API query. This does not support rights approval and the row remains `UNVERIFIED_ORIGIN_PENDING`, but the exact historical query should be linked if the register is later edited. Suggested wording:

   > “A prior local metadata-only query of `https://www.kaggle.com/api/v1/datasets/view/fanconic/skin-cancer-malignant-vs-benign` (recorded 2026-10-19) reported version 4 and `licenseName=Unknown`. The listing and path/size comparison are provenance leads only; they do not establish local byte identity, image-level licenses, or permission.”

These are traceability/process qualifications, not evidence that the underlying dataset rights are cleared. See `UNSUPPORTED_OR_OVERSTATED_CLAIMS.csv` for the classified entries.

## Remaining researcher decisions

The CSV `REMAINING_RESEARCHER_DECISIONS.csv` lists pending review topics. They include:

- HAM10000 local release/file identity, the scope of the article’s metadata waiver, per-image/source-level terms, and intended research, commercial, redistribution, modification, and model-output uses.
- SIIM aggregate versus individual contributor terms, exact individual license versions, fixed-ZIP byte identity if required, and intended use of model weights, predictions, and public demos.
- Fanconic authoritative origin/version, acquisition evidence and checksums, image-level source/license mapping, permissions, and intended uses.
- Researcher/legal interpretation where the sources do not expressly resolve a proposed use.

No researcher decision is entered in the existing review template.

## Integrity verification

- Before and after protected-file manifests each contain 38,906 paths and agree exactly. An independent current-disk scan matched both manifests: **0 missing, 0 added, 0 changed files**, 9,856,101,469 bytes.
- The frozen split SHA-256 is `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740`; preprocessing configuration SHA-256 is `e5c7a395cbdcdcf21cde75fa6f396b6dcee6bc132217d7053a271ea84cd91918`; approval checklist SHA-256 is `e9597aae3d03e3b1d549da474fc7befaa82ec2d7bf3872d0123d4a44359977be`.
- The existing `best.pt` checkpoint remains SHA-256 `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`.
- The approval checklist remains `NOT_APPROVED`.
- The three-row `RESEARCHER_REVIEW_TEMPLATE.csv` has all researcher/review/decision fields blank.
- All 13 entries in the existing audit’s `GENERATED_FILES_SHA256.csv` were recomputed and matched.
- No training or evaluation was performed during this independent review. This review created only the five requested review deliverables; it did not alter the original audit package, split, preprocessing, images, metadata, labels, checkpoint, or approval status.

## Final status

`AUDIT_EVIDENCE_CONSISTENT_WITH_LIMITATIONS`

The corrected audit’s substantive source-rights conclusions are consistent with the inspected evidence and appropriately qualified. This is **not** dataset approval, legal clearance, or training authorization. File-level identity, source-specific rights, and intended-use decisions remain pending as documented.
