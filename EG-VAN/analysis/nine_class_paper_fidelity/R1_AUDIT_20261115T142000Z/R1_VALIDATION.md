# R1 Validation

## Validation outcome

Overall: `PARTIALLY_VERIFIED`

The requested evidence inventory, class mapping comparison, ambiguity analysis, findings, and manifest were created in the new directory `analysis/nine_class_paper_fidelity/R1_AUDIT_20261115T142000Z/`. Hash and exact-file-set checks are reported after manifest generation below.

## Checks

| Check | Result | Evidence / limitation |
|---|---|---|
| Primary paper identified | VERIFIED | Local PDF title/DOI and first-page dates; Crossref metadata confirms title, DOI, volume, year, and page range. |
| Relevant paper locations recorded | VERIFIED | Printed pp. 72862-72864, Sections IV-A, IV-C, IV-D; Table 2 title on p. 72863. |
| Supplementary material located | PARTIALLY_VERIFIED | No supplementary filename was found in the repository search. This does not establish that no external supplement or author artifact exists. |
| Nine-class names and high-level construction assessed | VERIFIED | Main-text sections describe seven HAM diagnoses and two binary outputs; results text discusses nine labels. |
| Table 2 cell-level source and counts verified from primary evidence | PARTIALLY_VERIFIED | Table body is not present in the searchable text layer and was not visually inspected. The existing CSV transcription is secondary evidence. |
| Official ISIC 2017 release compared | VERIFIED | Official challenge Task 3 and data pages state task labels and release counts. This confirms only the official challenge definition, not EG-VAN's actual source package. |
| No undocumented mapping inferred | VERIFIED | No source label was translated into another diagnosis; the Table 2 source identity is left unresolved. |
| Split, duplicate, or patient/lesion policy verified | UNVERIFIED | Paper text reports aggregate counts but no image-level split, seed, duplicate, overlap, or patient/lesion grouping rule. |
| Existing project mapping compared | VERIFIED | Read-only inspection of the named protocol/recovery docs, Stage 4 mapping code, and Stage 4 audit JSON. |
| Protected Task 6A/6B/6C files modified | VERIFIED (not modified by this task) | No write action targeted those files. No claim is made about unrelated concurrent processes. |
| Source code, datasets, labels, notebooks, splits, checkpoints modified | VERIFIED (not modified by this task) | Only the seven files in this new R1 output directory were created. |
| Images, queue data, predictions, or model files accessed | VERIFIED (not accessed) | No image or contact sheet was opened, rendered, processed, or hashed; no queue, prediction, or model data was read. The paper was inspected through its text layer only. |
| Git state modified | VERIFIED (not modified by this task) | No Git write or Git state-changing operation was performed. |
| Manifest file set and hashes | VERIFIED | Manifest contains every other R1 output exactly once; all listed SHA-256 values were recalculated and matched. |

## Output set

Exactly seven files are expected:

1. `PAPER_SOURCE_INVENTORY.md`
2. `NINE_CLASS_MAPPING_EVIDENCE.csv`
3. `PAPER_VS_PROJECT_COMPARISON.csv`
4. `LABEL_SEMANTIC_AMBIGUITIES.md`
5. `R1_FINDINGS.md`
6. `R1_VALIDATION.md`
7. `R1_MANIFEST.sha256`

The manifest excludes itself by design. All six non-manifest deliverables are non-empty, and the exact manifest set and hashes were verified.

## Final decision

`PROTOCOL_PARTIALLY_SUPPORTED`

This is not dataset approval, split approval, training authorization, or an exact-reproduction claim.
