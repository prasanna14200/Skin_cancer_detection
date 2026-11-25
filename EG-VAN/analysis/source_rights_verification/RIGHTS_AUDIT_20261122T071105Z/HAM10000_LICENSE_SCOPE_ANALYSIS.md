# HAM10000 license-scope analysis

Evidence retrieved 2026-11-22. This records source statements and their scope; it is not legal advice or approval.

## Separate the three scopes

| Scope | Official evidence | What it supports | What it does not establish |
|---|---|---|---|
| HAM10000 image collection | The original paper's Table 1 lists `HAM10000`, `CC BY-NC 4.0`, and 10,015 images. The Dataverse v4.0 API field below independently contains the CC BY-NC 4.0 license text. | Dataset/version-level terms are explicitly evidenced. | It does not prove the local files are byte-identical to Dataverse v4.0 or map separate rights to every local image. |
| Article | The paper's open-access notice says the article is under CC BY 4.0 and excludes third-party material when a credit line says otherwise. | The article's own content, subject to that notice. | It does not blanket-license all underlying photographs or dataset files. |
| Article metadata | The paper's notice says the CC0 waiver “applies to the metadata files made available in this article.” | The metadata files within that article scope. | It does not identify the separate HAM10000 dataset file `HAM10000_metadata.csv`; no evidence reviewed establishes that this local CSV is one of those article metadata files. |

## Exact Dataverse v4.0 API evidence

Endpoint: [Harvard Dataverse v4.0 metadata API](https://dataverse.harvard.edu/api/datasets/:persistentId/versions/4.0/metadata?persistentId=doi%3A10.7910%2FDVN%2FDBW86T). The JSON response returned `status=OK` and:

- `data.schema:version` = `4.0`
- `data.schema:datePublished` = `2018-06-04`
- `data.dvcore:termsOfUse` is an HTML string whose exact heading is `Creative Commons Attribution-NonCommercial 4.0 International Public License`. This is the versioned record's terms field and contains the license text; it is not a separate JSON property named `license`.
- `data.dvcore:fileTermsOfAccess.dvcore:fileRequestAccess` = `false`. This is an access-request setting, not a license grant.
- No top-level `data.license` key was present.

The extracted `data.dvcore:termsOfUse` value had 15,662 Unicode characters and SHA-256 `15d4d8a8ada43a901459bc31feed59238d10e39b2e2814e3284e44b25734132a`. Two independent retrievals of the exact API endpoint returned the same field length and hash. The exact extracted fields are preserved in `HAM10000_DATAVERSE_V4_API_EVIDENCE.json`.

The official [versioned dataset landing page](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T) could not be loaded directly in this environment. The version-specific API endpoint did load successfully and its exact response fields are recorded above. The landing-page retrieval failure does not invalidate the successful API response.

## Application to local files

All 9,310 unique HAM10000 image IDs in `analysis/nine_class_exploratory/exploratory_split.csv` match IDs in the local 10,015-row `data/raw/HAM10000_metadata.csv`. This is a local identifier join only. It does not prove byte identity with the official Dataverse v4.0 files, establish that every local image has been independently rights-verified, or demonstrate that the local metadata CSV carries the article-level CC0 waiver.

The paper describes a multi-source collection and lists licenses for source collections in its comparison table. No local image-level contributor/license map was established for the 9,310 rows. Source-level details and provenance are therefore not upgraded to per-image verification.

## License-text limits

The official [CC BY-NC 4.0 legal code](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en) defines NonCommercial as “not primarily intended for or directed towards commercial advantage or monetary compensation.” Its Section 2 permits sharing and adaptations only for NonCommercial purposes; Section 3 requires attribution and indication of modifications when sharing. The license grants only rights the licensor has authority to grant; it does not grant privacy, publicity, moral, patent, or trademark rights, and other rights may still apply.

No categorical conclusion is made about commercial research, model weights, predictions, hosted demos, or other outputs. These require review of exact local file provenance, intended use, and any source-specific conditions.
