# A06 — Source-Specific Decision and Cohort Review

**Generated:** 2026-11-23  
**Status:** `A06_EVIDENCE_REVIEW_COMPLETE_DECISIONS_PENDING`  
**Approval:** `NOT_APPROVED`; approved images = **0**; `approved_four_way_split=false`  
**Actual-image training authorization:** **NO**

## Scope and safeguards

This is a read-only evidence and decision-preparation stage. It records no researcher approval and does not resolve a legal question. No source image was opened, transformed, or modified. No training, fine-tuning, inference, evaluation, source-image preprocessing/augmentation, external download, new split, or A05 execution occurred. The synthetic `--validate-only` test validates configuration and hashes temporary synthetic bytes; any transform object it constructs is not applied to an image. The review used existing text/CSV/JSON evidence, including image identifiers, paths, and previously generated hashes.

The existing exploratory split remains an unapproved historical artifact. No test partition was used for tuning or selection. Proposed or completed decision drafts were not treated as signed researcher approval.

## Prior-stage and repository verification

- **Git HEAD:** `eb835aa5b33fd788fab60e9634bf2761ceb303f7`.
- **Initial worktree:** no tracked changes; existing untracked A05/source-rights artifacts and other project paths were present before A06.
- **Approval checklist:** `NOT_APPROVED`; 0 approved eligible images; `approved_four_way_split=false`; all 7 checklist gates are `OPEN`.
- **Existing A01–A05 output manifests:** checked against their listed evidence before A06; A01 3/3, A02 evidence 6/6 and decision 2/2, A03 7/7, A04 4/4, and A05 4/4 entries matched.
- **Decision inventory:** 30 unresolved items are carried into the master register: 17 `RESEARCHER_DECISION_REQUIRED`, 9 `PENDING_EXTERNAL_EVIDENCE`, 3 `NOT_ESTABLISHED`, and 1 `CONTRADICTED` (HAM metadata checksum/size conflict). The A02 conservative Fanconic exclusion is recorded separately as one `PARTIALLY_VERIFIED` disposition; it is not an approval.
- **A05 proposed authorization configuration:** has 23 pending IDs (12 HAM-specific decisions and 11 tracker items); the seven open checklist items independently block authorization.
- **Protected baseline:** 67 selected files were fingerprinted before A06, including A01–A05 evidence, the approval checklist, split/manifests, training/model source, and checkpoints. At completion, 66/66 files other than the explicitly permitted safety-test file remain unchanged. The only baseline-file change is the synthetic-only A06 test addition in `tests/test_nine_class_authorized_training.py`. No model/training implementation, image, metadata, split, checkpoint, or prior-stage evidence was changed.

The baseline is a selected-file comparison, not a byte-for-byte scan of every repository file. The initial untracked paths were preserved; A06 added this timestamped directory and the explicitly justified test-only change.

## Decision status meanings

- `VERIFIED`: established only within the stated scope; not broader permission or approval.
- `PARTIALLY_VERIFIED`: a limited disposition or claim is documented, but formal approval or supporting evidence is incomplete.
- `NOT_ESTABLISHED`: required evidence is absent or inconclusive.
- `CONTRADICTED`: relevant records conflict.
- `RESEARCHER_DECISION_REQUIRED`: a researcher choice or confirmation is still pending.
- `PENDING_EXTERNAL_EVIDENCE`: authoritative source, rights-holder, curator, or other external evidence is needed.

These are evidence-workflow states, not legal conclusions. The decision register includes supporting evidence file paths and their SHA-256 values for each item.

## Cross-source decision state

### A01 intended use

A01 records a researcher-declared purpose of **academic research**. Researcher identity, role/institution, funding/commercial relationships, specific source activities, publication plans, public hosting, source-data redistribution/adaptation, attribution details, and sharing of weights or derived artifacts remain pending. The declaration is not dataset permission, legal clearance, or training authorization. Publication or redistribution involving source images, metadata, or derived artifacts requires separate activity-specific review.

### A02 Fanconic disposition

Retain the conservative disposition `EXCLUDE_FROM_APPROVED_COHORT_PENDING_EVIDENCE` for all **845** Fanconic records. The separate A02 draft records this disposition, but researcher name/signature and date were not supplied. It is not a formal source approval or a legal finding that the images cannot be used.

### A03 HAM10000 decisions

All **12** HAM-specific decision responses remain pending. The separate proposed draft is not a completed decision. No response was copied into the original blank template.

## Source-specific evidence assessment

### HAM10000 — 9,310 local records

**VERIFIED, limited scope:** the A03 inventory reports 9,310 readable 600×450 JPEGs; local hashes reconcile with the frozen split and Stage4 manifest. The local image IDs join to the metadata, and the compared metadata content agrees on six common fields (`lesion_id`, `dx`, `dx_type`, `age`, `sex`, `localization`). The seven source-defined `dx` classes are `akiec` 327, `bcc` 514, `bkl` 1,099, `df` 115, `mel` 883, `nv` 6,230, and `vasc` 142. Age is missing for 57 rows.

**NOT_ESTABLISHED:** A03 reports **0** upstream image-byte matches and no local acquisition receipt or authoritative local-to-upstream per-image byte crosswalk. Public Dataverse version history is not proof of which archive/version supplied the local files. The collection/version-level CC BY-NC 4.0 evidence does not establish per-image coverage, attribution, or permission for the planned activity.

**CONTRADICTED:** the metadata checksum/size evidence conflicts. The local CSV is 563,277 bytes with MD5 `70bb67f71bd23dde0bd2eda4bdcc98e5`; the v1/v2 listing reports 683,457 bytes with that MD5, while the retrieved v1/v2 body reports 683,457 bytes with MD5 `e623d553b413b94c0d85936de49d50dc`. The v3/v4 listing and retrieved body also have different recorded MD5 values. The discrepancy and canonical file bytes require authoritative resolution; exact raw-file identity must not be claimed.

**Identity limits:** 6,979 lesion IDs include 1,779 repeated-ID groups involving 4,110 images. These are lesion IDs, not patient IDs. No patient IDs are available, so patient independence is `NOT_ESTABLISHED`. There are two verified exact local duplicate pairs, 210 unreviewed candidate pairs involving 181 frozen HAM IDs, and 13 recorded R6 photo decisions (6 `SAME_PHOTO`, 7 `DISTINCT`) with blank reviewer IDs. Automated matches and reviewer-unattributed decisions are not treated as human adjudication; a photo decision does not establish patient independence.

**Required next evidence/decisions:** acquisition record and exact archive/version; authoritative local-to-upstream identity evidence; curator resolution of metadata checksum/size conflict; applicable image and metadata rights/attribution; activity-specific researcher decisions; label-policy confirmation retaining source-defined HAM diagnoses unless separately supported; and independent review of duplicate candidates and reviewer identity. Do not equate `mel` with a general `MALIGNANT` class.

### Fanconic — 845 local records

**NOT_ELIGIBLE_UNDER_CURRENT_ASSUMPTIONS:** continue excluding all 845 from approved-cohort consideration. A02 reports 0 upstream byte matches. The 845 path/size matches to a possible listing do not prove archive identity or acquisition. The listing reports `Unknown` license; no contributor-license/attribution map, authoritative original label source, or patient/lesion identifiers is established. The local `malignant` folder label is not verified clinical label provenance.

There are **127 unadjudicated cross-source perceptual candidate pairs involving 51 Fanconic files** (33 with PH2 and 94 with SIIM-ISIC 2020 in the A02 evidence). These are candidates, not confirmed duplicate findings or identity decisions.

**Required next evidence:** authoritative publisher/source/version and acquisition receipt; per-file package/record identity; applicable rights, attribution and use conditions; original per-image labels and definitions; patient/lesion identity evidence; and independent review of candidate relationships. Until these are supplied and reviewed, retain the exclusion. No Fanconic image is approved.

### SIIM-ISIC 2020 training v2 — 200 documented records

The eligibility matrix contains **79 records in the frozen exploratory split** and **121 outside it**. All 200 remain `NOT_APPROVED`. The 79 preserve their provisional status only; the 121 are not added to the split.

For the 79 previously revalidated API records, local evidence records 41 `CC-BY` and 38 `CC-BY-NC` codes and corresponding attribution entries; the codes do not state exact license versions, and the local hashes are not a byte comparison to the fixed Challenge ZIP. The remaining 121 records were not live-revalidated in the earlier A01 pass. Current ISIC terms pages distinguish contributor-selected per-image image licenses from the separate Site Database terms; the 2020 Challenge page records aggregate CC BY-NC terms and DOI `10.34970/2020-ds01`. Those pages do not establish exact local package identity or rights for every local record/use. Aggregate/per-image interaction and intended-use interpretation remain unresolved.

The source taxonomy is binary `benign`/`malignant`; all **200 records currently documented in the local eligibility matrix are labeled `benign`**. No evidence reviewed approves mapping either SIIM label to HAM diagnoses or a nine-class clinical taxonomy. No equivalence is inferred.

The acquired overlap evidence contains **3,268 unreviewed candidate pairs** involving 117 SIIM image IDs: 3,031 cross-source transformed-perceptual, 121 within-SIIM transformed-perceptual, and 116 cross-source perceptual pairs. Four are marked `PROBABLE_PHOTO_RELATION` by machine-generated evidence and 3,264 are `UNCERTAIN`; all remain unreviewed. These machine classifications do not determine whether images depict the same lesion or patient.

**Required next evidence:** exact Challenge package/version and authoritative file hashes; individual versioned terms and attribution for each considered record; written researcher/legal interpretation of aggregate versus contributor terms for each planned activity; source-defined label policy; and independent identity/duplicate review. Retain all 121 outside-split records outside the cohort unless separately reviewed.

### Current external-source check and limits

The official [ISIC Terms of Use](https://www.isic-archive.com/terms) and [2020 Challenge data page](https://challenge.isic-archive.com/data/#2020) were reviewed read-only on 2026-11-23. The terms distinguish contributor-selected per-image image licenses from separate Site Database/annotation terms; the 2020 Challenge page records aggregate CC BY-NC terms and the dataset DOI. These pages do not establish which exact package produced the local files, a license version for every local record, or permission for the specific intended use.

The human-readable Harvard Dataverse page was unavailable/returned 404 during this review, and A06 did not re-fetch or independently validate the archived Dataverse API response bodies. A03's saved URLs, status codes, and response hashes remain prior evidence only; external raw-response authenticity and the checksum discrepancy remain open. No external page snapshot or legal opinion is claimed as a retained, independently hashed deliverable.

## Human-review queue shape

The queue contains **13,974** unique review IDs: 10,355 record-level provenance/rights/label/identity tasks, 3,617 unique candidate-pair tasks after merging repeated path pairs across existing evidence, and 2 exact-local-duplicate disposition tasks. The pair rows preserve machine evidence and unattributed prior decision status only. All reviewer decision, reviewer identity, review-date, and evidence/comment fields are blank. Queue inclusion is not a decision, duplicate finding, or approval.

## Cohort feasibility comparison

| Scope | Documented records | Currently verified eligible | Current disposition | Feasibility now |
|---|---:|---:|---|---|
| HAM10000 seven source-defined classes | 9,310 | 0 | All pending researcher/source evidence | Not approved; potentially reviewable only after provenance, rights, identity, and decisions |
| SIIM-ISIC-supported scope | 200 (79 in split; 121 outside) | 0 | Provisional / identity review pending | No approved scope; binary labels and rights/package evidence unresolved |
| Combined nine-class scope | 10,355 across sources; 10,234 in frozen split | 0 | Fanconic 845 excluded; HAM/SIIM pending | Not feasible under current evidence; no approved source for any target class |
| Synthetic-only engineering validation | 0 real records | 0 | Synthetic tensors/labels only | Feasible for software checks only; it is not data validation or model performance |

The seven-class HAM scope is only **potentially** reviewable; no class is rights-cleared or approved now. The existing four-way assignments may be preserved as exploratory history but cannot be retained as an approved split. Future decisions/evidence can change cohort membership and identity groupings. Any later approved split requires a separate reviewed and frozen inventory; the exploratory split must not be reused as approval evidence.

No legitimate alternative source is established by this review. A new source would require authoritative provenance, original source-defined labels, applicable rights and attribution, and independently reviewable identity evidence. No alternative was downloaded or assumed licensed. There is no eligible independent external cohort for external validation.

## Approval-gate audit summary

The A05 central launcher was inspected and the authorization tests were expanded using synthetic fixtures only. The project-environment focused run passed **12 tests**. This includes checks for a `NOT_APPROVED` checklist, zero approved count, absent source/partition IDs, unresolved decisions/rights, identity overlap, calibration/test contamination, and approval/inventory hash mismatch.

**Important technical gap:** `src/nine_class_training.py` remains directly callable and does not invoke the central A05 source-eligibility and researcher-decision checks. A synthetic-only `--validate-only` test demonstrates that its legacy approved-split validator can accept a synthetic split with a synthetic approval JSON without consulting the central checklist/source/decision registers. No model or image loader was run by this test, and it does not represent actual approval. The production training code was not changed; this bypass must be closed before any future training authorization is relied upon.

The A05 report also records a prior focused suite result of 17 passes and one failure because `matplotlib` was unavailable. That earlier unrelated exploratory-checkpoint test issue was not changed or masked in A06.

## Research/legal questions still requiring human resolution

1. Who is the named researcher and institution, what is the exact activity scope, and are funding/commercial relationships involved?
2. Which publication, conference, public-demo, hosting, source-image display, redistribution/adaptation, and model-output sharing activities are actually planned?
3. What authoritative source establishes rights, attribution, provenance and version for each local HAM/Fanconic/SIIM record?
4. What permission covers the local HAM images/metadata and the SIIM per-image versus aggregate terms for each proposed activity?
5. Who will independently review the duplicate candidates, with identity, date, and evidence recorded? How will missing HAM patient identity be handled without treating lesion IDs as patient IDs?
6. What original labels are acceptable for each source, without equating HAM diagnoses with SIIM binary labels or the Fanconic folder label?
7. Is any text-only publication allowed absent source-data/derived-artifact release? No general conclusion is made here; the researcher and appropriate rights/legal reviewers must decide the actual use.

## Exact next action

The researcher should review and complete the A01 activity-scope decisions, A02 exclusion/evidence requirements, all HAM-D01–HAM-D12 responses, and the applicable SIIM/tracker items. Obtain the listed authoritative external records and independent human review, preserving reviewer identity/date/evidence. Keep the checklist `NOT_APPROVED` until a complete, hash-bound formal review exists. Before any future training, separately close the direct Stage 6 entry-point bypass and create a newly reviewed cohort/split; do not use the current exploratory split as an approved cohort.

**Stop condition:** researcher judgment and external evidence are required. No image, source, class, split, or use is approved by A06.
