# EG-VAN Cohort Feasibility Report

Assessment date: 2026-11-22  
Approval checklist: `NOT_APPROVED`  
No training, evaluation, prediction, split edit, or dataset approval was performed.

## Scope and reconciliation

- Frozen `exploratory_split.csv`: **10,234** records.
- Split sources: HAM10000 **9,310**; FANCONIC_LOCAL_UNVERIFIED_VERSION **845**; SIIM-ISIC 2020 training v2 **79**.
- Locally acquired SIIM records in the source-attribution/decision manifests: **200**. Of these, 79 are in the frozen split and 121 are outside it with automated candidate relations. The 121 are not added to the split.
- Total unique local images considered for eligibility planning: **10,355** (9,310 + 845 + 200).
- Four-way planning inventory: 10,234 records; its report says planning-only, zero approved rows, and `training_gate_accepts_preview=false`.

## Class availability

Counts are source-defined labels as currently represented by local manifests. They do not imply that different datasets' labels have equivalent clinical meaning.

| Existing class | HAM in split | Fanconic in split | SIIM in split | SIIM acquired outside split | Total local | Potentially eligible pending review in split | Currently approved |
|---|---:|---:|---:|---:|---:|---:|---:|
| AKIEC | 327 | 0 | 0 | 0 | 327 | 327 | 0 |
| BCC | 514 | 0 | 0 | 0 | 514 | 514 | 0 |
| BENIGN | 0 | 0 | 79 | 121 | 200 | 79 | 0 |
| BKL | 1,099 | 0 | 0 | 0 | 1,099 | 1,099 | 0 |
| DF | 115 | 0 | 0 | 0 | 115 | 115 | 0 |
| MALIGNANT | 0 | 845 | 0 | 0 | 845 | 0 | 0 |
| MEL | 883 | 0 | 0 | 0 | 883 | 883 | 0 |
| NV | 6,230 | 0 | 0 | 0 | 6,230 | 6,230 | 0 |
| VASC | 142 | 0 | 0 | 0 | 142 | 142 | 0 |
| **Total** | **9,310** | **845** | **79** | **121** | **10,355** | **9,389** | **0** |

`MALIGNANT` is the unverified Fanconic source/folder label, not a confirmed diagnosis or an equivalent of HAM `MEL`. `BENIGN` is the SIIM challenge target label; it is not asserted equivalent to any HAM diagnosis. The 121 SIIM records outside the split have source label `benign` in the candidate manifest, but no new class mapping is assigned here.

## Eligibility and blocker counts

The classification is one status per local record:

| Current plan status | Count | Interpretation |
|---|---:|---|
| `POTENTIALLY_ELIGIBLE_PENDING_REVIEW` | 9,389 | HAM 9,310 + split SIIM 79; still blocked by unresolved file identity/rights and researcher decisions. |
| `PROVENANCE_UNVERIFIED` | 845 | Fanconic; keep excluded from an approved cohort unless authoritative evidence resolves origin, terms, and label provenance. |
| `IDENTITY_REVIEW_PENDING` | 121 | SIIM acquired outside the split with automated candidate relations; no human decision is recorded. |
| **Approved now** | **0** | Approval checklist remains `NOT_APPROVED`. |

Additional overlapping blocker counts:

- Rights/intended-use decision open: **10,355** local records.
- Exact file/package identity not established: **10,355** records (HAM extracted-image comparison 9,310; SIIM fixed-package comparison 200; Fanconic source identity 845). For the 79 split SIIM records, API IDs/license/attribution were revalidated, but that is not fixed-ZIP byte identity.
- SIIM identity screening not human-adjudicated: **200** (121 candidate-relation + 79 no-candidate; both sets have `human_review_status=UNREVIEWED`).
- Patient IDs absent: **10,155** (HAM 9,310 + Fanconic 845). HAM has lesion IDs for all 9,310; Fanconic has no lesion IDs.
- Image, patient, and lesion IDs absent: **845** Fanconic records.
- Label-policy/provenance questions: **1,045** locally acquired SIIM/Fanconic records (SIIM 200 source-label policy; Fanconic 845 source-label provenance); **924** are within the frozen split.
- Recommended exclusion under current evidence: **845** Fanconic records. This is not permanent deletion or a researcher rejection.

Blocker counts overlap; do not sum them to estimate unique records. The record-level matrix gives each record its primary status, explicit overlapping blockers, and evidence references.

## Is a balanced nine-class cohort realistic now?

**No, not as an approved or training-ready cohort using the currently documented records.** No rows are approved. The entire `MALIGNANT` class depends on the unverified Fanconic source; excluding that source leaves zero records in that source-defined class. The split contains only 79 source-defined SIIM `BENIGN` examples, while the largest class, HAM `NV`, has 6,230. The largest-to-smallest potentially reviewable split count is about **78.9:1** (6,230:79). The 121 additional SIIM records are held outside the split pending identity review and cannot be counted as eligible.

The preview happens to show numeric representation across the four partitions, but it remains planning-only, has zero approved rows, and is rejected by the training gate. No downsampling, relabeling, partition change, or source substitution is authorized by this report. A future cohort would require either resolving Fanconic or sourcing a separately approved replacement for that source-defined class, resolving SIIM and HAM rights/identity questions, obtaining researcher label-policy decisions, and producing a separately authorized frozen cohort.

## Highest-priority actions

1. Resolve the 845 Fanconic records' authoritative origin, version, per-file checksums, contributor terms, and label provenance; otherwise exclude them from approval consideration.
2. Resolve local HAM image provenance against the official Dataverse image archives. The local metadata CSV matches the v1/v2 original-file MD5, not the v3/v4 original-file metadata.
3. Obtain a meaningful official SIIM fixed-package checksum/manifest and compare local bytes if package identity is required; the observed multipart ETag is not a verified SHA-256.
4. Obtain independent human adjudication of all 121 SIIM candidate-relation records and document that the other 79 no-candidate records remain unapproved pending identity review.
5. Record researcher decisions on intended use, aggregate/per-image terms interaction, exact label policy, attribution, redistribution, model artifacts, and demos. Do not change the approval checklist without that review.

## Decision

`ELIGIBILITY_PLAN_COMPLETE_NOT_APPROVED` means only that this eligibility plan and its evidence/action tables are complete. It does not establish rights, approve any dataset, authorize training, or validate the exploratory split as a clinical cohort.
