# Correction changelog

Date: 2026-11-22

## Changes

- Corrected HAM10000 scope: the original paper's dataset-table entry, article-level CC BY 4.0 notice, and article-metadata CC0 waiver are recorded separately. The CC0 notice is not attributed to the dataset's local metadata CSV.
- Independently queried Harvard Dataverse v4.0 metadata. Recorded exact `data.dvcore:termsOfUse` field and heading/value, `schema:version=4.0`, publication date, `fileRequestAccess=false`, absence of a separate `license` key, and a hash of the extracted full terms-field value.
- Repeated the Dataverse API retrieval independently; both responses had 15,662 Unicode characters and SHA-256 `15d4d8a8ada43a901459bc31feed59238d10e39b2e2814e3284e44b25734132a`. This replaces the earlier unconfirmed digest.
- Expanded SIIM-ISIC into aggregate Challenge CC BY-NC 4.0 terms, ISIC Site Terms, per-image contributor-license codes, and local Challenge-package byte identity. The API does not state versions for the per-image codes; the aggregate/per-image terms interaction remains a researcher-review question.
- Re-fetched all 79 individual official ISIC API records. All 79 image IDs, contributor-license values, and attribution strings matched the local acquisition register.
- Preserved Fanconic as `UNVERIFIED_ORIGIN_PENDING`; no Kaggle filename/size match is treated as proof of origin or permission.
- Added before/after SHA-256 inventories for protected data, metadata, partitions, checkpoints, model/training outputs, configuration, and prior Colab outputs. The current audit directory is excluded because this task updates it.
- Updated the evidence register to include exact URLs, supported claims, limitations, object scope, status, and 79 separate SIIM image API records. Updated the dataset comparison and unresolved-question registers.
- Added the verbatim Dataverse v4.0 `data.dvcore:termsOfUse` field in `HAM10000_DATAVERSE_V4_API_EVIDENCE.json`; left `RESEARCHER_REVIEW_TEMPLATE.csv` unchanged and blank.
- Updated the report and official references with license-scope distinctions and the verification results. Added the after-work protected-file inventory.

## Retrieval outcomes

- HAM10000 paper at PMC: fetched successfully; Table 1 and article notice inspected.
- Harvard Dataverse v4.0 metadata API: returned JSON `status=OK`; the requested version and exact terms field were extracted. The dataset landing page could not be opened directly in the browser/web fetch.
- SIIM-ISIC Challenge data page: opened through the official dataset DOI redirect; direct web fetch of the challenge host was blocked in this environment.
- ISIC Terms of Use: opened by browser navigation from the official Challenge page; direct web fetch was blocked.
- CC BY-NC 4.0 and CC BY 4.0 legal texts: fetched successfully from Creative Commons.
- ISIC image API: all 79 exact record endpoints returned matching live record data.
- Kaggle: no current rights or provenance conclusion was derived; the possible version-4 match remains a prior local metadata lead only.

## Protection and status

Pre-work and after-work protected inventories each contain 38,906 files and 9,856,101,469 bytes. Their relative-path sets match exactly; 0 files are missing, added, or changed by size or SHA-256. See `PROTECTED_FILE_HASHES_BEFORE.csv` and `PROTECTED_FILE_HASHES_AFTER.csv`.

Validation: evidence register 92 rows (79 per-image SIIM API records); dataset comparison 3 rows; unresolved questions 10 rows; all evidence statuses are allowed; all source URL fields parse as HTTP(S); live SIIM API data matched local ID/license/attribution for 79/79 (41 CC-BY, 38 CC-BY-NC); all seven original deliverables remain present; researcher template decisions remain blank.

No researcher decision was filled. The approval checklist remains `NOT_APPROVED`. No training or model evaluation occurred. The audit is not legal advice or dataset approval.
