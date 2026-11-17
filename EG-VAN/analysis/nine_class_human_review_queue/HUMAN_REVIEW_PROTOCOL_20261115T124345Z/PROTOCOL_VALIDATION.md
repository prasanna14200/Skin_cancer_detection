# Protocol Preparation and Validation

## Scope and input files inspected

This protocol was drafted from text and tabular records only. The following existing project files were inspected read-only:

- `analysis/nine_class_human_review_queue/QUEUE_ENRICHED_20261115T123152Z/human_review_queue_enriched.csv`
- `analysis/nine_class_human_review_queue/QUEUE_ENRICHED_20261115T123152Z/metadata_value_provenance.csv`
- `analysis/nine_class_human_review_queue/QUEUE_ENRICHED_20261115T123152Z/metadata_conflicts.csv`
- `analysis/nine_class_human_review_queue/QUEUE_ENRICHED_20261115T123152Z/enrichment_summary.json`
- `analysis/nine_class_human_review_queue/QUEUE_ENRICHED_20261115T123152Z/ENRICHMENT_FINDINGS.md`
- `analysis/nine_class_human_review_queue/QUEUE_CORRECTED_20261115T152000Z/HUMAN_REVIEW_GUIDE.md`
- `analysis/nine_class_human_review_queue/QUEUE_PREPARATION_20261115T091320Z/HUMAN_REVIEW_GUIDE.md`
- `docs/NINE_CLASS_BENIGN_REVIEW_WORKFLOW.md`
- `docs/NINE_CLASS_STAGE3H_DECISION.md`
- `docs/NINE_CLASS_STAGE3I_AI_REVIEW.md`
- `docs/NINE_CLASS_STAGE11A_REVIEW_GUIDE.md`
- `docs/NINE_CLASS_STAGE11B_AUTOMATED_REVIEW.md`
- `docs/NINE_CLASS_STAGE12_REPRODUCTION_READINESS.md`
- `docs/NINE_CLASS_DATASET_RECOVERY_DECISION.md`
- `analysis/nine_class_stage12/readiness_snapshot.json`
- `analysis/nine_class_stage12/reviewer_ledger_validation.json`

No image evidence, source code, notebook, model, or image file was used to define a relationship decision. The reviewed documentation describes existing evidence and procedures; it does not establish human outcomes for this queue.

## Actual enriched queue schema

The queue has 1,258 rows and includes:

- Pair/image locators: `review_item_id`, `canonical_pair_id`, `canonical_path_a`, `canonical_path_b`.
- Side metadata: `source_a`, `source_b`, `source_split_a`, `source_split_b`, `image_id_a`, `image_id_b`, `patient_id_a`, `patient_id_b`, `lesion_id_a`, `lesion_id_b`.
- Evidence/provenance: `evidence_sources`, `evidence_row_references`, `evidence_occurrence_count`.
- Automated/priority information: `ai_assessments`, `priority_categories`, `priority_reason`.
- Review fields: `human_decision`, `review_status`, `reviewer_notes`.

The queue's canonical path order is sorted, not original evidence orientation. The enrichment provenance explicitly records original source paths and canonical side mappings; a future coordinator must use that provenance rather than treating A/B order as source-side history.

From `enrichment_summary.json`, available queue metadata is partial: `source_a` 25 rows, `source_b` 404, `source_split_a` 765, `source_split_b` 172, and `lesion_id_b` 83. Both `image_id_*`, both `patient_id_*`, and `lesion_id_a` are blank throughout. `metadata_conflicts.csv` contains zero rows in this queue version. These values document availability only; they do not prove patient identity, cross-source identity, lesion independence, diagnosis, or dataset provenance.

`human_decision` is blank and `review_status` is `UNREVIEWED` on all rows. The queue has no populated reviewer IDs, confidence, independent rationale, disagreement, adjudicator, or final adjudication fields. Its automated/AI and priority fields are not human decisions. No queue schema change is proposed here.

## Protocol output checks

| Check | Result | Basis |
| --- | --- | --- |
| All five required protocol artifacts plus manifest are present and non-empty | VERIFIED | Checked after writing the new directory. |
| Five decision categories have distinct definitions and evidence thresholds | VERIFIED | `DECISION_RUBRIC.csv` contains one row for each requested category. |
| Same photograph is distinguished from same lesion in a separate capture | VERIFIED | Separate definitions and evidence requirements in protocol and rubric. |
| Initial reviews are independent and blinded to AI/automated outputs | VERIFIED | Reviewer view requirements and lock-before-reveal workflow are explicit. |
| Disagreements preserve both original decisions and rationales | VERIFIED | Adjudication is separate and append-only; no overwrite is allowed. |
| No diagnosis, relabeling, patient inference, or split approval is authorized | VERIFIED | Scope and handling restrictions are stated throughout. |
| No queue records or pair decisions were created or changed | VERIFIED | Only the new protocol output directory was written; the template contains a header only. |
| Manifest hashes and exact output file set | VERIFIED | Checked after creation; manifest covers every output except itself, including this validation report. |
| No image pixels were opened or inspected | PARTIALLY_VERIFIED | One existing contact sheet, `analysis/nine_class_recovery/review_sheet_01.jpg`, was accidentally opened earlier in the session. It was not used as evidence; no pair decisions were made. This incident is disclosed, not represented as a successful noninspection check. |

## Existing project status and terminology

The inspected Stage 3H and Stage 12 text reports human review as pending, 0 of 19 primary pairs reviewed, no approved cohort, and no production split. Stage 3I and Stage 11B describe AI/automated categories as triage evidence rather than human ground truth. Existing guides use some different decision terms, including `SAME_LESION`, `DISTINCT_PHOTO`, and `CANNOT_ASSESS`; this protocol defines the requested categories for prospective use and does not translate or overwrite any historical values.

## Limitations

This is a written protocol, not an implemented blinded viewer, assigned reviewer roster, review batch, completed human review, or adjudication. No independent calibration set or reviewer-consistency result was established. No patient-level split is supported by this protocol or by missing identifiers. Dataset source identity, licensing, label compatibility, eligibility, and approval remain separate unresolved gates.

**Overall protocol-preparation status: PARTIALLY_VERIFIED**, because the prior accidental contact-sheet opening means the strict noninspection condition cannot be reported as fully met. It was not used as evidence and no pair decisions were made.
