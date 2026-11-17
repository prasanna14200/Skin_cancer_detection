# R1 Findings: EG-VAN Paper Fidelity and Nine-Class Label Audit

## Final decision

`PROTOCOL_PARTIALLY_SUPPORTED`

The paper text supports the broad nine-output construction: seven HAM10000 diagnostic classes plus two outputs named BENIGN and MALIGNANT from a second two-class skin-cancer collection. It does not support a fully reproducible source-to-label protocol for the proposed project mapping. In particular, the binary source/version and the Table 2 source-column cells are unresolved, and the paper provides no reproducible per-image mapping or split/overlap manifest in the inspected text.

This decision does not approve any dataset, cohort, split, or training run.

## Verified from primary sources

1. The local original article is the IEEE Access 2025 paper identified by DOI `10.1109/ACCESS.2025.3561240`, volume 13, pages 72852-72874. Its first page gives the article title, authors, and publication dates; Crossref independently confirms the DOI metadata.
2. Section IV-A (printed p. 72862) describes combining seven HAM10000 diagnoses with a two-class collection labeled benign and malignant, yielding a nine-class task. Section IV-D (printed p. 72864) discusses the nine output names.
3. Section IV-C (printed p. 72863) reports an original test count of 1,332 and enlarged training and validation totals of 37,883 and 6,686, respectively. It describes augmentation and further division of training data, but these aggregate counts do not identify image membership.
4. The official ISIC 2017 Task 3 page describes two separate binary tasks over three diagnoses, with 2,000 training images; the official data page lists 2,000 train, 150 validation, and 600 test images. This is evidence about the official challenge release only.

## Partially verified or unresolved

- The existing project transcription says Table 2's binary source column reads “ISIC 2017” and records 1,800 BENIGN plus 1,497 MALIGNANT images. The table body is non-searchable in the local PDF text layer and was not visually inspected. These cells therefore remain unverified from primary evidence.
- The official ISIC 2017 Task 3 release's three diagnoses and two task-specific binary targets do not match a complete 3,297-image generic BENIGN/MALIGNANT release. Thus equating the transcribed binary subset with the official Task 3 release and its labels is contradicted. This does not establish what source package EG-VAN actually used.
- Existing project documents describe a structural match between the local 3,297-image tree and a Fanconic collection, while Stage 4 explicitly marks the local version unverified. No evidence ties that exact local package to EG-VAN's experiment.
- Exact per-image source IDs, binary label derivation, package version, split membership, augmentation lineage, overlap/deduplication handling, and patient/lesion grouping are not established by the available primary text.
- The paper does not provide output index order. The project's fixed numeric order is a local implementation choice, not a paper-recovered encoding.

## Semantic conclusion

HAM diagnoses remain their own source-defined output classes. BENIGN and MALIGNANT are separate source labels in the paper's high-level construction, but the paper does not establish that they are mutually exclusive clinical categories relative to the HAM diagnoses. This audit creates no medical equivalence and does not relabel any source record.

## Project comparison and limits

The Stage 4 code uppercases and preserves HAM `dx` labels and maps local binary folder labels directly to BENIGN/MALIGNANT under the explicit source marker `FANCONIC_LOCAL_UNVERIFIED_VERSION`. That behavior is visible in `src/nine_class_stage4.py` lines 24-25 and 74-90. The Stage 4 eligibility audit records no final split and a blocked gate. Existing research-completion documentation likewise identifies the unresolved source-name conflict and split/augmentation gaps.

No source code, dataset, labels, notebook, split, checkpoint, or Git state was changed. No patient image, contact sheet, queue record, or model prediction was opened or used. No human-review activity, training, or evaluation was performed.

## Evidence references

- Primary paper: printed pp. 72862-72864, Sections IV-A, IV-C, IV-D; Table 2 on p. 72863 (body not text-extractable in this audit).
- Official ISIC: Task 3 page headings “Goal,” “Definitions,” and “Data”; official data page 2017 release table.
- Project comparison: `docs/NINE_CLASS_RESEARCH_COMPLETION_PLAN.md`, `docs/NINE_CLASS_DATASET_SUITABILITY_DECISION.md`, `docs/NINE_CLASS_DATASET_RECOVERY_DECISION.md`, `src/nine_class_stage4.py`, and `analysis/nine_class_stage4/split_eligibility_audit.json`.

No training authorization or dataset/split approval follows from understanding the paper's high-level mapping.
