# Source-rights research report

Audit directory: `RIGHTS_AUDIT_20261122T071105Z`  
Evidence retrieval date: 2026-11-22 UTC  
Scope: 9,310 HAM10000, 845 FANCONIC_LOCAL_UNVERIFIED_VERSION, and 79 SIIM-ISIC 2020 training v2 rows in the exploratory split.

## Executive finding

The HAM10000 paper, Dataverse v4.0 API, SIIM-ISIC Challenge page, ISIC Terms of Use, Creative Commons legal texts, and 79 individual ISIC API records were independently checked. The exact Dataverse v4.0 `data.dvcore:termsOfUse` field contains the CC BY-NC 4.0 legal text. The 79 SIIM records' image IDs, licenses, and attributions match live API responses. Exact byte identity of local HAM and SIIM images to their packaged releases is not established. Fanconic origin and license remain unresolved. No dataset is approved; the existing checklist remains `NOT_APPROVED`. No training or evaluation was run or authorized.

| Source | Count | Evidence status | Finding |
|---|---:|---|---|
| HAM10000 | 9,310 | `PARTIALLY_VERIFIED` | Paper Table 1 and exact Dataverse v4.0 API field identify CC BY-NC 4.0; local IDs match local metadata, not verified bytes. |
| FANCONIC_LOCAL_UNVERIFIED_VERSION | 845 | `UNVERIFIED_ORIGIN_PENDING` | Kaggle v4 is only a metadata lead; `licenseName=Unknown`; no per-image IDs/rights. |
| SIIM-ISIC 2020 training v2 | 79 | `PARTIALLY_VERIFIED` | Aggregate CC BY-NC 4.0 and individual license codes identified; per-image code versions, package-byte identity, and terms interaction remain open. |

## HAM10000

- **Collection license:** the original paper's Table 1 lists HAM10000 (10,015 images) as **CC BY-NC 4.0**. The official Harvard Dataverse v4.0 API independently returned `status=OK`, `data.schema:version=4.0`, and `data.dvcore:termsOfUse` with exact heading `Creative Commons Attribution-NonCommercial 4.0 International Public License`. This is the actual versioned terms field; no top-level `data.license` key is present. The field contains the full license text.
- **Article and metadata scope:** the paper itself has an article-level CC BY 4.0 notice, subject to third-party credit lines. Its separate CC0 waiver says it applies to “the metadata files made available in this article.” That statement is not evidence that the separate HAM10000 dataset file `HAM10000_metadata.csv` is CC0. The Dataverse API separately returns `data.dvcore:fileTermsOfAccess.dvcore:fileRequestAccess=false`; that is an access-request setting, not a license.
- **Local fit:** all 9,310 unique IDs match the local 10,015-row `HAM10000_metadata.csv`. This is identifier correspondence only; no package receipt or official file checksum comparison establishes local byte identity to v4.0. The cohort is a subset, not the complete release.
- **Source/contributor scope:** the paper describes a multi-source collection and lists license values for component collections, but the local manifest has no per-image contributor-license mapping for the 9,310 records. No claim is made that every local image has been independently rights-verified.
- **Research/commercial:** if the license applies, noncommercial research may fit; “research” is not a blanket exception. CC defines NonCommercial as not primarily intended for commercial advantage or monetary compensation. Commercial use is excluded absent separate permission.
- **Redistribution/modification:** if CC BY-NC applies to the material being shared, it permits sharing and adaptations only for noncommercial purposes, with attribution, license link, and indication of modifications. These conditions apply when sharing licensed material, not only to publications. ISIC 2018 provides a HAM credit line, but this is not a per-image credit/license map.
- **Attribution/access:** retain supplied creator/notices when sharing; Dataverse metadata says no access request is required. No account requirement was identified in the reviewed record.
- **Models/public demos:** no explicit model-weight, prediction-output, hosted-demo, or publication rule was identified. The Nature article's CC BY license is not treated as the underlying image-data license.

## FANCONIC_LOCAL_UNVERIFIED_VERSION

- **Origin:** 845 rows are folder/source-labeled malignant; all 845 lack image, patient, and lesion IDs. A prior local recovery report describes a strong metadata-level match to Kaggle v4 path names/sizes, reports uploader Claudio Fanconi, and `licenseName=Unknown`. It does not provide remote file checksums or exact acquisition evidence. Kaggle is only an origin lead here, not rights evidence.
- **Rights:** research, academic, commercial, redistribution, modification, attribution, access, public demo, model-weight, and output permissions are unknown. Public availability and folder labels do not establish rights or clinical label provenance.
- **Minimum evidence:** versioned official package/acquisition record with hashes, per-image source IDs and contributor terms, applicable official package terms, then researcher review.

## SIIM-ISIC 2020 training v2

- **Aggregate terms:** the official Challenge page links aggregate CC-BY-NC to **CC BY-NC 4.0**, lists 33,126 training records and metadata v2, and requires the citation International Skin Imaging Collaboration. SIIM-ISIC 2020 Challenge Dataset. International Skin Imaging Collaboration. DOI 10.34970/2020-ds01 (2020).
- **Individual image terms:** the ISIC Terms of Use state contributors select one of CC0, BY, or BY-NC for each uploaded image, and each image may be used only under its contributor license. They separately state annotations are CC0 and the ISIC Site Database is licensed under CC0; those statements are not treated as image licenses and do not resolve how the Challenge aggregate term applies.
- **Exact 79 records:** all 79 local image IDs, `copyright_license` codes, and attribution strings matched live responses from their exact official Archive API URLs. There are 41 `CC-BY` and 38 `CC-BY-NC` codes. The API values do not state a version number for these individual licenses. The API validation is in `SIIM_API_RECORD_REVALIDATION.csv`.
- **Commercial/redistribution:** the Challenge page identifies aggregate CC BY-NC 4.0. Do not infer the 41 CC-BY image records remove or override the aggregate condition. The Challenge requires the dataset citation; per-image attribution/license conditions also apply when sharing the corresponding image/material. The interaction of the two layers and the individual license versions are left for researcher review.
- **File identity:** local images were served through official Archive API/S3 records; the fixed Challenge JPEG ZIP was not acquired, so byte identity to that package is unverified.
- **Models/public demos:** no explicit weight/output/demo clause was identified; the effect of both aggregate and per-image terms for planned use needs researcher review.
- **Access/assent:** the Terms of Use say access, contribution, or use signifies assent; public site access does not require an account, while image upload or annotation requires an account. No separate competition-registration condition is inferred from this evidence.

## License-text interpretation boundaries

The official CC BY-NC 4.0 legal code defines NonCommercial as “not primarily intended for or directed towards commercial advantage or monetary compensation.” It allows sharing and adaptations only for NonCommercial purposes, subject to attribution, license-link, and modification-indication requirements when sharing. CC BY 4.0 does not contain the NonCommercial condition, but its attribution requirements still apply where that license actually governs the material.

Both licenses grant only the rights the licensor has authority to grant. They do not settle other rights, such as privacy, publicity, moral, patent, or trademark rights. The CC0 statements in the HAM article and ISIC Terms have their own narrower scopes; they are not treated as licenses for all underlying images.

No categorical conclusion is made about model weights, predictions, hosted demos, derived datasets, or commercial research. The reviewed source terms do not explicitly resolve those specific artifacts and uses; they remain researcher/legal-review questions.

## Unresolved matters and validation

See `UNRESOLVED_RIGHTS_QUESTIONS.csv`. Priority issues: exact HAM files and image-level rights; Fanconic origin/license; SIIM package identity and aggregate/per-image terms for intended use. The three-row `RESEARCHER_REVIEW_TEMPLATE.csv` has every review/decision field blank.

Validation results: the evidence register has 92 rows, including 79 per-image SIIM API records; the comparison has 3 dataset rows; the unresolved-questions register has 10 rows. All evidence statuses are from the allowed set, every source URL parses as HTTP(S), all 79 live SIIM records match the local ID/license/attribution register (41 CC-BY, 38 CC-BY-NC), and the researcher template has 3 dataset rows with all review/decision fields blank. All seven original deliverables are present.

The protected before/after inventories each contain 38,906 files totaling 9,856,101,469 bytes. Relative-path sets match exactly; **0 files were missing, added, or changed** (including hashes). `GENERATED_FILES_SHA256.csv` hashes every other audit deliverable; its own self-hash is excluded because updating that hash changes the file.

Protected file SHA-256 values before audit generation (must remain unchanged):

| Input | SHA-256 |
|---|---|
| `analysis/nine_class_exploratory/exploratory_split.csv` | `d4bce612e08cf2942cf2aefe45f807ad60e0d9dcc05aef41cf8e2fd560bbe740` |
| `analysis/nine_class_final_cohort/approval_checklist_v1.json` | `e9597aae3d03e3b1d549da474fc7befaa82ec2d7bf3872d0123d4a44359977be` |
| `config/nine_class_preprocessing_raw_v2.json` | `e5c7a395cbdcdcf21cde75fa6f396b6dcee6bc132217d7053a271ea84cd91918` |
| `analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt` | `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08` |

These four directly protected files also match their after-work SHA-256 values.

## Final status

The project remains **NOT_APPROVED** for training under the existing checklist. This audit grants no approval, changes no dataset or label, and authorizes no training. This is an evidence inventory, not legal advice; researcher review and, where needed, rights-holder/legal guidance remain necessary.
