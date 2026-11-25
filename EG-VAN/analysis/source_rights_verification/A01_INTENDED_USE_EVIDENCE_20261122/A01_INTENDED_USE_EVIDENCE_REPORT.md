# A01 — Intended-Use Decision Evidence Pack

Prepared: 2026-11-22  
Purpose: evidence preparation for A01; **not a legal decision, dataset approval, or training authorization**.  
Current project approval status: `NOT_APPROVED`.

## A01 scope and linked decisions

The eligibility action plan's A01 is “Set intended-use boundary.” It links `GLOBAL-REVIEW`, `HAM-INTENDED-USE`, `SIIM-INTENDED-USE`, and `FAN-INTENDED-USE`; all four remain `PENDING_RESEARCHER_REVIEW`.

The question for the researcher is what activities the project will actually conduct for each source. A single project-purpose statement is not a substitute for reviewing the distinct source terms, file provenance, attribution, and third-party rights.

## Evidence table

| Dataset/source | Verified terms and evidence | Relevant restrictions or attribution wording | Intended-use questions for researcher | What cannot currently be concluded |
|---|---|---|---|---|
| **HAM10000** | The original paper's Table 1 lists the collection as CC BY-NC 4.0 (10,015 images). Harvard Dataverse versions 1.0–4.0 report the same CC BY-NC 4.0 terms text. The local metadata CSV is 563,277 bytes and MD5 `70bb67f71bd23dde0bd2eda4bdcc98e5`, matching the Dataverse v1/v2 original-file record; it differs from the v3/v4 metadata record. | Where CC BY-NC 4.0 applies, the legal text limits licensed sharing/adaptations to NonCommercial purposes and specifies attribution, a license link, and indication of modifications when sharing. The paper's separate CC BY 4.0 article notice does not blanket-license the images. Its CC0 waiver covers metadata files made available in the article; the local dataset CSV is not identified as one of them. The 9,310 local image IDs match local metadata IDs, but extracted images have not been compared with the official ZIP contents. | Is each activity primarily noncommercial? Is there commercial sponsorship, product development, monetization, marketing, or another commercial advantage? Will paper figures or public displays reproduce images? Will images/metadata be shared or adapted? Will model weights, predictions, or a hosted demo be distributed? What attribution and source-version evidence will accompany each activity? | The reviewed evidence does not establish local extracted-image byte identity, per-image source/license mapping, applicability of the article's metadata CC0 waiver to the local CSV, or a definitive interpretation for the proposed academic, demo, commercial, model, or output uses. The MD5 match is evidence against an official file record, not proof of acquisition history or separate permission. |
| **SIIM-ISIC 2020 training v2** | The official Challenge page links aggregate CC BY-NC 4.0 and requires citation DOI `10.34970/2020-ds01`. ISIC Terms say contributors select CC0, BY, or BY-NC for individual images, and use is subject to the contributor-selected license. For the 79 records in the exploratory split, API IDs/license codes/attributions were revalidated: 41 `CC-BY`, 38 `CC-BY-NC`; the API codes do not state versions. | The aggregate Challenge citation and aggregate terms are distinct from per-image attribution and contributor terms. The Terms separately scope CC0 for annotations and the Site Database; those statements are not image licenses. The aggregate/per-image interaction is not resolved here. Local image hashes match the local attribution register, but not the fixed Challenge ZIP by a package-byte comparison. A further 121 acquired records are outside the split and remain in the identity-candidate quarantine; all 200 acquired records are unreviewed and not approved. | Is the intended activity noncommercial or commercial? How will aggregate Challenge citation and each image's attribution be carried into publications/demos? Will any image, metadata, adaptation, weights, or predictions be redistributed or publicly hosted? Does the researcher require the fixed Challenge ZIP identity? What evidence/interpretation is required for individual license versions and the aggregate/per-image terms? | The reviewed sources do not settle how the aggregate and contributor terms interact for these particular uses, whether the 41 CC-BY codes change the aggregate conditions, exact versions for individual API codes, fixed-ZIP byte identity, or rights implications for weights, predictions, public demos, or other derivatives. No conclusion that any use is permitted is made. |
| **FANCONIC_LOCAL_UNVERIFIED_VERSION** | The local exploratory split contains 845 files with folder/source label `malignant`. Origin is `UNVERIFIED_ORIGIN_PENDING`. The possible Kaggle v4 listing is only a provenance lead; the prior query reported `licenseName=Unknown`. No authoritative acquisition receipt, verified remote checksums, image-level source identifiers, or contributor-license mapping was found. | No authoritative license, attribution notice, or terms have been established for these local files. The folder label and public listing do not prove source, diagnosis, research rights, commercial rights, redistribution rights, or demo/model-output permissions. | Is the researcher willing to consider this source only after authoritative provenance and rights evidence is supplied? If not, should it be kept excluded from any future approved cohort? If evidence is later found, which research, publication, commercial, hosting, redistribution, modification, and model-output uses will be reviewed? | No research, academic, commercial, publication, hosting, redistribution, modification, model-weight, or prediction permission can be established from the records reviewed. No source-defined label or upstream version is verified. |

## Intended-use scenarios: evidence boundary

These are prompts for researcher review, not legal conclusions.

| Activity | Verified evidence relevant to review | Required researcher input / unresolved boundary |
|---|---|---|
| **Academic research and publication** | HAM10000 is reported under CC BY-NC 4.0 at collection scope; the article itself has a separate CC BY 4.0 notice. SIIM has aggregate CC BY-NC 4.0, a required dataset citation, and contributor-selected per-image terms. Fanconic rights are unverified. | Describe funding, institutional/commercial relationships, publication figures, image display, attribution, and whether images or metadata will be included. “Academic” or “research” alone does not establish a use as NonCommercial or settle other rights. |
| **Non-commercial demonstrations or portfolio showcases** | CC BY-NC wording is relevant only where it applies to the actual material and use. SIIM has aggregate and per-image terms. Fanconic has no verified terms. | State audience, hosting, portfolio/employer/product promotion, sponsorship, monetization, access, and which images or artifacts are exposed. A non-commercial label on a demo does not itself establish permission. |
| **Commercial research or product development** | CC BY-NC 4.0 text defines and limits NonCommercial use; SIIM's aggregate terms are CC BY-NC 4.0. Some individual SIIM API codes are `CC-BY`, but the aggregate/per-image interaction remains open. Fanconic permissions are unknown. | State whether any activity is directed toward commercial advantage or monetary compensation, and identify any separate permissions or agreements. The evidence pack does not determine whether a specific activity is commercial or permitted. |
| **Hosting or publicly sharing a demo** | ISIC Terms distinguish public site access from image contributor licenses; public access or lack of account requirement is not a license grant for rehosting. No reviewed source explicitly resolves the proposed EG-VAN hosted demo. | Identify whether raw images, thumbnails, metadata, outputs, or only interface/code are public; hosting location, access controls, retention, attribution, and promotion. Seek review of privacy/publicity and other rights not settled by these licenses. |
| **Redistribution or adaptation of images/metadata** | Where CC BY-NC 4.0 applies, its text addresses sharing/adaptations, NonCommercial purpose, attribution, license link, and change indication. SIIM also has individual contributor terms and an aggregate citation. Fanconic has no verified rights evidence. | Specify the exact files, transformations, recipients, repository/access level, attribution, and whether onward redistribution is intended. Do not treat the article's CC BY or narrow CC0 metadata notice as a blanket license for HAM data. |
| **Sharing weights, predictions, or derived artifacts** | The reviewed evidence does not state a categorical rule for EG-VAN model weights, predictions, or hosted outputs. | Describe what artifacts will be shared, their contents, access, intended audience, and whether they reproduce or expose source material. Obtain researcher/legal interpretation under the exact applicable terms; no conclusion is provided here. |

## Verified wording versus unresolved interpretation

Verified statements include the cited license names and scopes, the official SIIM citation requirement, SIIM per-image API code counts for the revalidated 79 records, and the Fanconic provenance gaps. The official CC legal codes describe their own conditions where those licenses apply.

Unresolved questions include how the terms apply to the researcher's actual purpose and funding, whether a given activity is NonCommercial, how SIIM aggregate and per-image terms interact, what permissions cover Fanconic, whether the planned public display or sharing is allowed, and how source terms apply to weights, predictions, and derived outputs. This report does not answer those questions.

**A project-level intended-use declaration does not automatically establish permission under any dataset's terms.** Each source and file scope still requires its own provenance, terms, attribution, and use review. A declaration also cannot supply rights that a source or contributor did not grant.

## What the researcher must decide next

Complete `A01_INTENDED_USE_RESEARCHER_DECISION_TEMPLATE.md` with:

1. Researcher identity, role, date, and project purpose.
2. Academic/publication activities, including image display and funding/relationships relevant to the intended use.
3. Whether activities are non-commercial, commercial, or mixed, with reasons and supporting facts.
4. Public-demo/hosting, image/metadata redistribution or adaptation, and model-weight/prediction-sharing plans.
5. Separate source-specific decision and rationale for HAM10000, SIIM-ISIC 2020, and Fanconic, with evidence references and any request for legal review.

The template is intentionally blank. All four linked A01 decisions remain pending. The approval checklist remains `NOT_APPROVED`; no dataset or record is approved by this pack.

## Evidence references

See `A01_EVIDENCE_REFERENCE_REGISTER.csv` for each source, claim scope, limitations, and local/official references.
