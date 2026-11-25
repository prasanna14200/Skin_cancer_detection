# A03 HAM10000 Researcher Decision Preparation — Proposed Draft

**Status:** `PROPOSED_FOR_RESEARCHER_REVIEW`; no researcher decisions are recorded in this draft.  
**Evidence package:** A03 passed technical validation as `A03_VALIDATION_PASS_NOT_APPROVED`.  
**Dataset state:** `NOT_APPROVED`; 0 approved eligible images; `approved_four_way_split=false`; no training authorization.

This is a separate decision-preparation document. It does not change the blank A03 template, the evidence package, the approval checklist, or any dataset record. It does not approve any image, establish legal clearance, establish patient independence, or claim external validation. No training, evaluation, inference, or A04 work is authorized or performed.

## Scope and prior researcher declarations

- A03 investigates the **9,310 HAM10000 records** in the frozen EG-VAN exploratory split. This draft concerns researcher decisions about those HAM10000 records only.
- A01 records the researcher's declared intended use as **academic research only**. This does not establish dataset permission, copyright clearance, permission to publish or redistribute third-party data, or model-training authorization. Journal/conference publication, hosting, redistribution, and model-artifact sharing were not separately approved in A01.
- A02's disposition excludes **845 Fanconic records** from approved-cohort consideration pending evidence. That disposition applies to Fanconic only; it is not a HAM10000 decision and is not a legal determination.
- The A03 blank researcher template remains blank. All response fields below are `PENDING RESEARCHER DECISION`.

## Evidence status key

- `VERIFIED`: supported in the specific scope stated; does not imply broader rights or identity.
- `PARTIALLY_VERIFIED`: evidence supports only part of the claim or a limited scope.
- `NOT_ESTABLISHED`: required evidence is absent or inconclusive.
- `CONTRADICTED`: relevant records conflict.
- `RESEARCHER_DECISION_REQUIRED`: a researcher choice or confirmation has not been supplied.

These are evidence and workflow labels, not legal conclusions.

## Evidence summary for researcher review

| Topic | Evidence status | Supporting evidence | Unresolved limitation |
|---|---|---|---|
| Public dataset origin and version history | `VERIFIED` for the public Harvard Dataverse collection and its seven published versions; `NOT_ESTABLISHED` for the acquisition history and exact version of the local images | A03 report §§3, 8; `A03_UPSTREAM_VERSION_AND_FILE_CROSSWALK.csv`; register references `A03-DV-VERSION-HISTORY`, `A03-DV-10-METADATA` through `A03-DV-40-METADATA` | No local acquisition receipt, download log, source archive, or authoritative local-to-upstream per-image byte crosswalk was found. |
| Local image integrity and upstream identity | `VERIFIED` for local consistency; `NOT_ESTABLISHED` for upstream byte identity | `A03_LOCAL_IMAGE_HASH_INVENTORY.csv`: 9,310 readable 600×450 JPEGs; local hashes match both the frozen split and Stage4 manifest. The crosswalk and register reference `A03-IMAGE-BYTE-IDENTITY` report 9,310 identifier-only matches and 0 upstream byte matches. | Matching a filename/ID to metadata does not prove which archive/version supplied the image. No image archive was downloaded; the report records a combined archive size of 2,770,088,655 bytes. |
| Metadata row correspondence | `VERIFIED` for the compared metadata content | `A03_METADATA_AND_LABEL_PROVENANCE.csv`: all 9,310 IDs and the six common fields (`lesion_id`, `dx`, `dx_type`, `age`, `sex`, `localization`) match the recorded v1/v4 metadata contents. Register references include `A03-LOCAL-METADATA-PROVENANCE` and `A03-DV-METADATA-DATAFILE-V1` / `A03-DV-METADATA-DATAFILE-V4`. | Content correspondence does not prove raw-file identity. |
| Metadata raw-byte identity | `CONTRADICTED` among the available checksum/size records; local-to-release identity remains `NOT_ESTABLISHED` | A03 report §3 and `A03-METADATA-CHECKSUM-CONFLICT`: local file 563,277 bytes, MD5 `70bb67f71bd23dde0bd2eda4bdcc98e5`; v1/v2 listing says 683,457 bytes with that MD5, while the retrieved v1/v2 body is 683,457 bytes with MD5 `e623d553b413b94c0d85936de49d50dc`. The v3/v4 listing MD5 is `8f85fb1aa29d80a2797247e434deb79d`; the retrieved body MD5 is `1d13fed99da9c3e925fb523df87d527e`. | The discrepancy's cause and canonical metadata-file bytes are unresolved. The local metadata's raw-byte identity to a specific release must not be claimed. |
| Original HAM diagnoses | `VERIFIED` as metadata-content correspondence; any additional EG-VAN diagnosis remapping is `NOT_ESTABLISHED` | A03 report §5 and `A03_METADATA_AND_LABEL_PROVENANCE.csv`: the original `dx` labels match upstream for all 9,310 records. Counts are `akiec` 327, `bcc` 514, `bkl` 1,099, `df` 115, `mel` 883, `nv` 6,230, and `vasc` 142. | The evidence supports preserving the seven source-defined HAM classes. It does not establish equivalence to `BENIGN` or `MALIGNANT`; no such mapping is recorded. Age is missing for 57 records. |
| Collection-level terms | `VERIFIED` as collection/version-level evidence; per-image coverage is `NOT_ESTABLISHED` | A03 report §7; crosswalk and `A03-DV-10-METADATA` through `A03-DV-40-METADATA`; register reference `A03-ARTICLE-XML`. All seven Dataverse terms fields have the same recorded SHA-256, `15d4d8a8ada43a901459bc31feed59238d10e39b2e2814e3284e44b25734132a`, and identify CC BY-NC 4.0 at collection level. The article's Table 1 separately reports CC BY-NC 4.0 for HAM10000. | The article's own CC BY 4.0 license and its article-scoped CC0 metadata wording are not permissions for the separate images or local metadata file. No per-image rights/attribution map establishes coverage of these local files. |
| Lesion, patient, and duplicate identity | `PARTIALLY_VERIFIED` for recorded lesion/photo evidence; patient independence is `NOT_ESTABLISHED` | A03 report §6 and `A03_LESION_IDENTITY_AND_DUPLICATE_SUMMARY.csv`: 6,979 source lesion IDs; 1,779 repeated-ID groups involving 4,110 images; 2,951 pairwise co-memberships; two exact local duplicate pairs. There are 13 recorded R6 photo decisions (6 `SAME_PHOTO`, 7 `DISTINCT`) and 210 unreviewed candidates involving 181 frozen HAM IDs. | No patient IDs are available. All 13 R6 reviewer IDs are blank. Automated evidence is not human adjudication; a `DISTINCT` photo decision does not establish distinct lesions or patients. |
| A01 intended-use scope | `VERIFIED` as a project-level researcher declaration; HAM-specific activities and boundaries are `RESEARCHER_DECISION_REQUIRED` | A01 completed draft and A03 register reference `A03-A01-INTENDED-USE` | Academic intent alone is not permission. Publication, public hosting, source-data redistribution, adaptation, and sharing of weights or derived artifacts are not separately approved. |
| Approval status | `VERIFIED` as current workflow state | A03 report §9; `A03-APPROVAL-CHECKLIST`; current checklist | `NOT_APPROVED`; zero approved images; no approved four-way split. This decision-preparation draft does not change that status. |

## Decisions for the researcher

No choice is selected in this table. The researcher should complete each response, including any rationale and evidence references, after review.

| ID | Decision required | Evidence and limitation to consider | Researcher response |
|---|---|---|---|
| HAM-D01 | Decide whether the 9,310 HAM10000 records should remain pending, be excluded from future approved-cohort consideration, or be proposed for further consideration after specified evidence is obtained. | A03 found 0 upstream byte matches, no local acquisition receipt, a metadata checksum conflict, and no per-image rights mapping. Current checklist has 0 approved images. | `PENDING RESEARCHER DECISION` |
| HAM-D02 | Confirm the specific HAM10000 activities intended under the A01 academic-research declaration, including whether any training, evaluation, inference, or other activity is planned. | A01 states academic research only at project level; it does not authorize an activity or dataset. No training authorization exists. | `PENDING RESEARCHER DECISION` |
| HAM-D03 | Decide what provenance evidence is required before reconsidering these records, including acquisition URL/date/receipt, authoritative version, and local-to-upstream image identity. | Official IDs match metadata, but all 9,310 images are identifier-only matches; no upstream image-byte match or local acquisition trail was established. See A03 report §§1, 3–4 and register references `A03-LOCAL-ACQUISITION-TRAIL` and `A03-IMAGE-BYTE-IDENTITY`. | `PENDING RESEARCHER DECISION` |
| HAM-D04 | Decide whether to seek Dataverse/data-curator confirmation or other independent evidence to resolve the metadata checksum and size conflict before relying on a particular release. | A03 classifies the metadata listing/body conflict as `CONTRADICTED`; exact local metadata raw-file identity is not established. See `A03-METADATA-CHECKSUM-CONFLICT`. | `PENDING RESEARCHER DECISION` |
| HAM-D05 | Decide whether the intended label use is limited to the seven original HAM `dx` classes, and whether any separate, evidence-backed label mapping is proposed. | The original labels match upstream metadata. No mapping from HAM diagnoses to EG-VAN `BENIGN` or `MALIGNANT` is established. | `PENDING RESEARCHER DECISION` |
| HAM-D06 | Decide whether to obtain rights-holder or institutional guidance on the applicable terms for the local images and metadata, including non-commercial boundaries and required attribution. | CC BY-NC 4.0 is verified only at collection/version level; per-image rights and attribution remain `NOT_ESTABLISHED`. The article's license and article-scoped metadata statement have different scopes. | `PENDING RESEARCHER DECISION` |
| HAM-D07 | State whether journal, conference, thesis, or other publication is planned, and whether any source image or metadata would appear in figures, supplements, presentations, or repositories. | A01 left publication and public-artifact decisions pending. The evidence does not establish source-image publication or redistribution permissions. | `PENDING RESEARCHER DECISION` |
| HAM-D08 | Decide whether any public website, hosted demo, application, or service is planned; specify audience, access, retention, and whether users could see source images, metadata, predictions, or other outputs. | A01 left hosting/demo decisions pending. Per-image rights and permissions for hosted outputs are not established. | `PENDING RESEARCHER DECISION` |
| HAM-D09 | Decide whether images, metadata, annotations, or derived datasets will be redistributed, mirrored, adapted, or provided to others, and specify recipients and attribution plans. | A01 left redistribution/adaptation decisions pending. No per-image rights map or permission for these activities is established. | `PENDING RESEARCHER DECISION` |
| HAM-D10 | Decide whether weights/checkpoints, predictions, probabilities, embeddings, or other derived artifacts will be shared, hosted, or used in a demo or service. | A01 left model-artifact decisions pending. A03 does not establish categorical permissions for weights or derived artifacts. | `PENDING RESEARCHER DECISION` |
| HAM-D11 | Decide what independent identity review is required before any future cohort consideration, and how the unreviewed candidates and recorded R6 decisions should be handled. | A03 reports no patient IDs, 210 unreviewed candidates involving 181 frozen HAM IDs, and 13 R6 decisions with blank reviewer IDs. Automated similarity is not adjudication. | `PENDING RESEARCHER DECISION` |
| HAM-D12 | Confirm attribution/citation approach for the dataset and each image/source component if any use is later proposed. | The collection-level terms and article citation are recorded, but image-to-contributor attribution and per-image rights are not established. | `PENDING RESEARCHER DECISION` |

## Unresolved blockers before any approval consideration

1. Establish local acquisition history, exact upstream version, and authoritative image-level identity; the 9,310 local files have no verified upstream byte matches.
2. Resolve the Dataverse metadata listing/body checksum and size discrepancy with an authoritative source; do not claim exact raw-file identity in the meantime.
3. Establish rights and attribution applicable to the local images and metadata; collection-level CC BY-NC 4.0 evidence alone does not establish per-image coverage or permission for a particular activity.
4. Record the researcher's activity-specific decisions, including publication, hosting, redistribution/adaptation, and model/derived-artifact sharing.
5. Patient IDs are unavailable; patient independence must not be inferred. Determine whether additional independent identity review is required. Reviewer identity for the 13 R6 decisions remains unverified because reviewer IDs are blank.
6. External raw-response verification remains a limitation: A03 records URLs, statuses, and response hashes, but this decision preparation did not re-fetch those sources or validate external response bodies.
7. The approval checklist remains `NOT_APPROVED`, with zero approved images and `approved_four_way_split=false`.

## Researcher record

- Researcher name and role: `PENDING RESEARCHER CONFIRMATION`
- Institution: `PENDING RESEARCHER CONFIRMATION`
- Decision date: `PENDING RESEARCHER CONFIRMATION`
- HAM-D01 through HAM-D12 responses and rationale: `PENDING RESEARCHER DECISION`
- Supporting researcher/rights-holder/institutional references: `PENDING RESEARCHER CONFIRMATION`
- Researcher signature or approval record: `PENDING RESEARCHER CONFIRMATION`

This draft records questions and evidence for researcher review; it is not a completed researcher decision, legal clearance, dataset approval, training authorization, patient-independence finding, or external validation. **Do not proceed to A04 until the researcher has reviewed and recorded the required decisions.**

## Evidence references

- A03 report: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_HAM10000_PROVENANCE_REPORT.md`
- A03 image inventory: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_LOCAL_IMAGE_HASH_INVENTORY.csv`
- A03 version/file crosswalk: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_UPSTREAM_VERSION_AND_FILE_CROSSWALK.csv`
- A03 metadata/label provenance: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_METADATA_AND_LABEL_PROVENANCE.csv`
- A03 lesion/duplicate summary: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_LESION_IDENTITY_AND_DUPLICATE_SUMMARY.csv`
- A03 evidence register: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_EVIDENCE_REFERENCE_REGISTER.csv`
- A03 blank template, preserved unchanged: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_RESEARCHER_DECISION_TEMPLATE.md`
- A03 output hash manifest: `./A03_HAM10000_PROVENANCE_EVIDENCE/A03_OUTPUT_SHA256.csv`
- A01 completed intended-use draft: `./A01_INTENDED_USE_EVIDENCE_20261122/A01_INTENDED_USE_RESEARCHER_DECISION_COMPLETED_DRAFT.md`
- A02 completed Fanconic disposition: `./A02_FANCONIC_PROVENANCE_EVIDENCE/A02_RESEARCHER_DECISION_COMPLETED_DRAFT.md`
- Current approval checklist: `../nine_class_final_cohort/approval_checklist_v1.json`
