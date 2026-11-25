# A04 — Cohort Eligibility Feasibility Assessment

**Assessment scope:** Read-only feasibility review of the 10,234 records in `analysis/nine_class_exploratory/exploratory_split.csv` and the currently documented HAM10000, Fanconic, and SIIM-ISIC 2020 sources.  
**Status:** `A04_FEASIBILITY_COMPLETE_NOT_APPROVED`.  
**Approval state:** `NOT_APPROVED`; 0 approved eligible images; `approved_four_way_split=false`.

This assessment does not approve any source, image, class, label mapping, or partition. The A03 technical validation status is not a dataset decision. A01/A02/A03 decision drafts remain evidence for review; pending fields have not been treated as researcher approvals. No source data, split, label, checkpoint, or existing evidence was modified. No training, inference, evaluation, preprocessing, augmentation, external download, or A05 work occurred.

## Executive findings

- The frozen exploratory split contains **10,234 rows**: 9,310 HAM10000, 845 Fanconic, and 79 SIIM-ISIC 2020 training v2 records. The eligibility matrix contains 10,355 rows because it also records **121 SIIM records outside the frozen split**; those 121 are not added to this cohort analysis.
- All 10,234 split rows have `approval_status=NOT_APPROVED` and `research_status=EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION`. The approval checklist remains `NOT_APPROVED`, with zero approved images and no approved four-way split.
- Under the required conservative assumptions, the **currently approved/eligible count is zero for all nine target classes**:
  - All 845 Fanconic rows are `NOT_ELIGIBLE_UNDER_CURRENT_ASSUMPTIONS`, consistent with the separate A02 exclusion disposition pending origin, rights, and label evidence.
  - All 9,310 HAM10000 rows remain `RESEARCHER_DECISION_REQUIRED`. A03 verifies local hash consistency and metadata-content correspondence, but not the local image archive/version, per-image rights, or patient independence.
  - The 79 SIIM rows retain only their existing `PRELIMINARY_NO_CANDIDATE_NOT_APPROVED` status. Their current exploratory `BENIGN` mapping is not treated as an approved nine-class label or as evidence of patient independence.
- A defensible nine-class cohort **cannot be constructed from the current evidence**. The class names are present in the exploratory mapping, but no class has a currently rights-cleared, approved, independently reviewable source under these assumptions. In particular, Fanconic is excluded for `MALIGNANT`; HAM `mel` is not assumed equivalent to a general `MALIGNANT` label.
- A seven-class research scope using HAM10000 source-defined `dx` classes is **potentially feasible only conditionally**. It is not currently approved or cleared; acquisition/version identity, applicable rights, researcher decisions, and identity/duplicate review remain unresolved. No minimum per-class sample sufficiency threshold is established here.
- No legitimate alternative source is verified in the currently documented evidence to fill any gap. A future alternative could be considered only after its provenance, source-defined diagnostic labels, applicable rights, attribution, and patient/lesion identity evidence are independently established. No alternative dataset was downloaded or approved.
- The existing train/validation/calibration/test assignments are retained **only as an unchanged exploratory artifact**. They cannot be treated as an approved four-way split. The test partition was counted for inventory reconciliation only; it was not used for tuning or selection. No replacement split was created.

## Evidence status labels

- `VERIFIED`: established only within the stated evidence scope.
- `PARTIALLY_VERIFIED`: some supporting evidence exists, but material scope or identity remains unresolved.
- `NOT_ESTABLISHED`: required evidence is absent or inconclusive.
- `NOT_ELIGIBLE_UNDER_CURRENT_ASSUMPTIONS`: excluded by the explicit conservative assumptions for this assessment; this is not a legal determination.
- `RESEARCHER_DECISION_REQUIRED`: a researcher decision remains pending; no decision is inferred from a proposal or evidence report.

These are workflow/evidence classifications, not legal conclusions or dataset approvals.

## Source and current-status counts

| Source in frozen split | Frozen records | Existing matrix eligibility classification | Conservative A04 treatment | Approved eligible now |
|---|---:|---|---|---:|
| HAM10000 | 9,310 | `POTENTIALLY_ELIGIBLE_PENDING_REVIEW` (9,310) | Keep pending A03 researcher decisions; do not approve | 0 |
| Fanconic local unverified version | 845 | `PROVENANCE_UNVERIFIED` (845) | `NOT_ELIGIBLE_UNDER_CURRENT_ASSUMPTIONS`; retain A02 pending-evidence exclusion | 0 |
| SIIM-ISIC 2020 training v2 | 79 | `POTENTIALLY_ELIGIBLE_PENDING_REVIEW` (79) | Retain provisional, not-approved status; no label or patient-independence inference | 0 |
| **Frozen split total** | **10,234** | — | — | **0** |

The eligibility matrix separately contains 121 SIIM records marked `IDENTITY_REVIEW_PENDING`, `NO_UNTIL_ADJUDICATED`, and `ACQUIRED_OUTSIDE_FROZEN_SPLIT`. They are not included in the 10,234 frozen split counts or in the partition summaries.

## Existing nine-class mapping and feasibility

The class/index mapping below is the current **exploratory** mapping in the frozen split and Stage4 code. It is not an approval or a finding that labels from different sources are clinically equivalent. `A04_SOURCE_CLASS_ELIGIBILITY_MATRIX.csv` contains the per-class status and blockers.

| Target class | Index | Existing source and source-defined label | Frozen records | Exploratory train / validation / calibration / test | Conservative A04 status | Approved eligible now |
|---|---:|---|---:|---|---|---:|
| AKIEC | 0 | HAM10000 / `akiec` | 327 | 223 / 42 / 30 / 32 | `RESEARCHER_DECISION_REQUIRED` | 0 |
| BCC | 1 | HAM10000 / `bcc` | 514 | 371 / 49 / 44 / 50 | `RESEARCHER_DECISION_REQUIRED` | 0 |
| BKL | 2 | HAM10000 / `bkl` | 1,099 | 754 / 108 / 122 / 115 | `RESEARCHER_DECISION_REQUIRED` | 0 |
| DF | 3 | HAM10000 / `df` | 115 | 86 / 9 / 10 / 10 | `RESEARCHER_DECISION_REQUIRED` | 0 |
| MEL | 4 | HAM10000 / `mel` | 883 | 629 / 84 / 85 / 85 | `RESEARCHER_DECISION_REQUIRED` | 0 |
| NV | 5 | HAM10000 / `nv` | 6,230 | 4,347 / 629 / 627 / 627 | `RESEARCHER_DECISION_REQUIRED` | 0 |
| VASC | 6 | HAM10000 / `vasc` | 142 | 103 / 15 / 13 / 11 | `RESEARCHER_DECISION_REQUIRED` | 0 |
| BENIGN | 7 | SIIM-ISIC 2020 / `benign` | 79 | 55 / 8 / 8 / 8 | `RESEARCHER_DECISION_REQUIRED` (provisional only) | 0 |
| MALIGNANT | 8 | Fanconic local unverified version / local folder label `malignant` | 845 | 512 / 84 / 84 / 165 | `NOT_ELIGIBLE_UNDER_CURRENT_ASSUMPTIONS` | 0 |

### Per-class evidence assessment

- **HAM10000 classes (AKIEC, BCC, BKL, DF, MEL, NV, VASC):** A03 reports all 9,310 source `dx` values match the recorded upstream metadata content, with seven source-defined diagnoses preserved. It also reports zero verified upstream image-byte matches, no patient IDs, unresolved metadata raw-byte checksums, no per-image rights map, and outstanding identity review. Thus these are potential source-defined classes, not currently rights-cleared or patient-independent classes.
- **BENIGN:** 79 SIIM records appear in the split with the existing source label `benign` and exploratory class name `BENIGN`. A01 records aggregate Challenge CC BY-NC 4.0 terms and revalidated API license codes/attribution for these 79 (41 `CC-BY`, 38 `CC-BY-NC`), but the individual license versions and aggregate/per-image terms interaction are unresolved. The 79 records remain preliminary and not approved; neither nine-class eligibility nor patient independence is inferred.
- **MALIGNANT:** The only currently mapped source is the 845-record Fanconic folder label. A02 reports zero verified upstream byte matches, unknown license, unverified clinical label provenance, missing patient/lesion IDs, and unadjudicated candidates. Under the required assumption all 845 are excluded pending evidence. HAM `mel` is not silently mapped to general `MALIGNANT`.

## Partition reconciliation

| Source | Train | Validation | Calibration | Test | Total |
|---|---:|---:|---:|---:|---:|
| HAM10000 | 6,513 | 936 | 931 | 930 | 9,310 |
| Fanconic local unverified version | 512 | 84 | 84 | 165 | 845 |
| SIIM-ISIC 2020 training v2 | 55 | 8 | 8 | 8 | 79 |
| **Total** | **7,080** | **1,028** | **1,023** | **1,103** | **10,234** |

The detailed 36-row grouping by source, original label, existing class/index, matrix eligibility, source split, partition, and current status is in `A04_CLASS_COUNT_AND_PARTITION_SUMMARY.csv`.

### Can the existing four-way split be retained?

Not as an approved or final research split on the current evidence. It may remain unchanged as the historical exploratory assignment for auditability, but:

1. every record is currently `NOT_APPROVED`;
2. applying the conservative assumptions leaves no approved eligible records in any class;
3. 845 Fanconic rows, including 165 in the exploratory test partition, are excluded under the A02 pending-evidence disposition;
4. HAM identity/right decisions and SIIM terms/package/identity review are unresolved; and
5. future evidence or researcher decisions may change cohort membership or group constraints.

No partition was changed or rebuilt. The test partition was not used for tuning, selection, or feasibility-driven record choice. Any later approved-cohort split would require its own documented review and freeze; this assessment does not authorize one.

## Seven-class potential and alternative sources

A seven-class scope can be considered **potentially feasible** only if the researcher decides to pursue it and the HAM10000 acquisition/version, file identity, applicable rights/attribution, label policy, and required identity review are resolved. Existing counts range from 115 DF to 6,230 NV, but these counts alone do not prove adequacy, rights, patient independence, or generalizability. No class is currently approved.

No currently documented source supplies a verified alternative for the excluded Fanconic `MALIGNANT` records. A future source could potentially fill a class only if its original labels support that target without inference, and authoritative version/provenance, intended-use rights, attribution, and independently reviewable identity information are available. No particular alternative source is endorsed here; none was downloaded or licensed as part of A04.

## Blocking researcher decisions and evidence needed

`A04_BLOCKER_AND_EVIDENCE_ACTION_PLAN.csv` enumerates the 12 pending A03 HAM decisions, the 11 decision-tracker items, and the seven open approval checklist gates. Key items include:

- **HAM:** acquisition/version and image identity; metadata checksum discrepancy; per-image rights and attribution; precise research/publication/hosting/redistribution/model-output scope; source-label policy; independent identity review; and researcher sign-off.
- **Fanconic:** the A02 draft records exclusion pending evidence, but origin/version, rights, and source label evidence remain unresolved. The draft is not legal clearance or a change to the approval checklist.
- **SIIM:** aggregate versus contributor terms, exact individual license versions, fixed-ZIP byte identity, label policy, identity candidates, and specific intended uses. The 121 SIIM records outside the split remain outside the cohort.
- **Global gates:** researcher decisions, identity review, screening validation, eligible class counts, calibration freeze, and formal approval remain open.

The A03 proposed decision draft contains 12 pending HAM-specific decisions; none was treated as approval. A01's academic-research declaration remains project-level only and does not resolve source permissions or publication/redistribution/model-artifact decisions.

## Reproducible checks and limitations

Read-only checks used the actual files:

1. Loaded the frozen split and grouped by `source_dataset`, `original_label`, `class_name`, `class_index`, and `proposed_partition`.
2. Joined HAM10000 and SIIM records by `source_dataset + image_id`, and Fanconic records by `source_dataset + image_path + local SHA-256` because the 845 Fanconic split rows have blank `image_id` values. Compared those Fanconic keys with the eligibility matrix's `image_path` and `local_manifest_sha256`/`record_key`. All 10,234 split records join exactly once to rows marked `IN_FROZEN_EXPLORATORY_SPLIT`. Kept the 121 `ACQUIRED_OUTSIDE_FROZEN_SPLIT` SIIM rows out of split counts.
3. Grouped the 10,234 rows by source/label/current matrix eligibility/source split/partition/current approval/research/automated status. The 36 grouped counts sum to 10,234.
4. Reconciled source totals (9,310 + 845 + 79), class totals, and four partition totals (7,080 + 1,028 + 1,023 + 1,103).
5. Read the nine-class ordering in `src/nine_class_stage4.py`, exploratory source-label guards in `src/nine_class_exploratory.py`, A01/A02/A03 decision/evidence documents, the eligibility matrix, tracker, and checklist.
6. Confirmed the approval checklist is still `NOT_APPROVED`, `approved_eligible_images=0`, and `approved_four_way_split=false`.

The assessment relies on the scoped evidence in A01/A02/A03; it does not re-fetch upstream records or independently verify external raw response bodies. Key limitations remain: local HAM upstream archive identity and exact version are not established; the metadata checksum conflict is unresolved; per-image rights and patient identity are not established; A03 R6 reviewer identities are unverified; and SIIM individual/aggregate terms and package identity remain unresolved. The A02 Fanconic disposition and A03 proposed decisions remain distinct from researcher approvals.

## Evidence references

- Frozen split and class assignments: `analysis/nine_class_exploratory/exploratory_split.csv`; mapping/guards: `src/nine_class_stage4.py`, `src/nine_class_exploratory.py`.
- Current source eligibility and pending decisions: `analysis/source_rights_verification/DATASET_ELIGIBILITY_PLAN_20261122/DATASET_SOURCE_ELIGIBILITY_MATRIX.csv` and `ELEVEN_RESEARCHER_DECISIONS_TRACKER.csv`.
- Approval gate: `analysis/nine_class_final_cohort/approval_checklist_v1.json`.
- A01 academic-use draft: `analysis/source_rights_verification/A01_INTENDED_USE_EVIDENCE_20261122/A01_INTENDED_USE_RESEARCHER_DECISION_COMPLETED_DRAFT.md`.
- A02 evidence and disposition: `analysis/source_rights_verification/A02_FANCONIC_PROVENANCE_EVIDENCE/A02_FANCONIC_PROVENANCE_REPORT.md` and `A02_RESEARCHER_DECISION_COMPLETED_DRAFT.md`.
- A03 provenance and pending decisions: `analysis/source_rights_verification/A03_HAM10000_PROVENANCE_EVIDENCE/A03_HAM10000_PROVENANCE_REPORT.md` and `analysis/source_rights_verification/A03_HAM10000_RESEARCHER_DECISION_PROPOSED_DRAFT.md`.
- A04 generated counts, class assessment, and action plan: the companion CSVs in this directory.

**Final state:** feasibility assessment complete as evidence only; the cohort, classes, sources, and split remain `NOT_APPROVED`. Stop here and wait for researcher review; do not proceed to A05 or training.
