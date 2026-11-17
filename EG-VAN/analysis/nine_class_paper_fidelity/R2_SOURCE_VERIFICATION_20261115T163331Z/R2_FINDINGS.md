# R2 Findings: Primary-Source Table Verification

## Overall status

`PARTIALLY_VERIFIED`

The paper and its Table 2 were identified confidently, and Table 2 was visually verified from an isolated vector form object. The existing project transcription matches the displayed table except for one literal cell difference and row ordering. The table's `ISIC 2017` source claim conflicts with the official Task 3 release if interpreted as the complete official release and its official labels; the actual source package and label derivation remain unresolved.

## Source identity result

- Paper: *EG-VAN: A Global and Local Attention-Based Dual-Branch Ensemble Network With Advanced Color Balancing for Multi-Class Skin Cancer Recognition*, by Adnan Saeed, Khurram Shehzad, Saim Ahmed, and Ahmad Taher Azar.
- IEEE Access, vol. 13, 2025, pp. 72852-72874; DOI `10.1109/ACCESS.2025.3561240`.
- PDF path: `E:\Cancerdetection\EG-VAN_A_Global_and_Local_Attention-Based_Dual-Branch_Ensemble_Network_With_Advanced_Color_Balancing_for_Multi-Class_Skin_Cancer_Recognition.pdf`
- PDF SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`; 23 pages.
- Table 2 is on printed p. 72863, PDF viewer page 12 (one-based), page index 11 (zero-based). The table body is vector graphics in Form XObject 510, not searchable text.
- Existing transcription path: `E:\Cancerdetection\EG-VAN\analysis\nine_class_research_completion\paper_table2_transcription.csv`; SHA-256 `0bfac8b73d01e7c0abab31272f18b0e9dffe7793444bbc70f65fe639a2dba705`.

## Table 2 verification result

`VERIFIED` for the table's visible headings, nine row labels, source labels, and literal cell values. The actual table form was isolated and visually inspected without rendering the rest of the paper page; it contained no image XObjects or inline images.

Among 54 table data-cell comparisons, 53 are `MATCH` and one is `MISMATCH`: the NV `Augmented Images` source cell prints `00`, while the existing transcription contains `0`. The literal is readable; its intended numeric interpretation is not explained. All nine logical rows and six columns are present. The row order differs, and the table contains no explicit total row or visible footnote.

For all 64 comparison entries, including structural/aggregate checks: 58 `MATCH`, 2 `MISMATCH`, 3 `AMBIGUOUS`, 1 `NOT_PRESENT_IN_SOURCE`, and 0 `NOT_VERIFIABLE`. See `TABLE2_COMPARISON.csv` and `TABLE2_DISCREPANCIES.md` for the counting basis.

## ISIC 2017 primary-source result

The paper's Table 2 literally labels both added rows `ISIC 2017`. The official ISIC Task 3 page defines two separate binaries over melanoma, nevus, and seborrheic keratosis; the official data page lists 2,000 train, 150 validation, and 600 test images. This does not match a complete 3,297-image generic BENIGN/MALIGNANT release. Thus complete-official-release equivalence is `CONTRADICTED`; the specific derivative/package used by EG-VAN is `UNVERIFIED`.

## Nine-class mapping reassessment

Seven HAM10000 diagnostic rows are `VERIFIED` from the paper. Separate `Benign` and `Malignant` outputs are also `VERIFIED` as table labels and the table's source field is `ISIC 2017`; their exact source lineage and per-image label meaning are only `PARTIALLY_VERIFIED`. The paper does not establish that the broad outputs are mutually exclusive clinical diagnoses relative to the seven HAM diagnoses; that claim is `UNVERIFIED`.

## Remaining provenance uncertainties

- Exact binary archive/version, original IDs, and whether it is an official release or a derivative.
- Per-image derivation of the Benign and Malignant labels.
- Meaning of the printed NV `00`.
- Relationship between Table 2 augmentation counts and Section IV-C's reported 37,883 training and 6,686 validation counts.
- Paper split membership, randomization, duplicate/overlap handling, and patient/lesion grouping.

## Not inspected or performed

- No standalone patient/lesion images, contact sheets, review queues, AI outputs, human-review decisions, datasets, model files, or predictions were opened or processed.
- No image package was downloaded; no training, evaluation, or inference was performed.
- No dataset, label, split, source code, notebook, checkpoint, R1 file, or Git state was changed.
- The original PDF page containing other content was not rendered; only the isolated Table 2 vector form was rendered.

## Existing files modified

`NO`. The source PDF and existing transcription hashes were captured and rechecked. R1 files were read-only and their manifest was verified.

## Recommended next evidence task

Request an author-confirmed binary-source name/version, per-image ID/checksum and label manifest, clarification of the Table 2 NV `00`, and the paper's split/augmentation lineage and overlap policy. Do not infer the source or alter the project mapping pending that evidence.
