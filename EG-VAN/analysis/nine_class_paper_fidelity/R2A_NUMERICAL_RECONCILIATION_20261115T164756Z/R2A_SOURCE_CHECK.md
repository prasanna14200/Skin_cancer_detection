# R2A Source Check

## Primary paper

- Title: *EG-VAN: A Global and Local Attention-Based Dual-Branch Ensemble Network With Advanced Color Balancing for Multi-Class Skin Cancer Recognition*
- Authors: Adnan Saeed, Khurram Shehzad, Saim Ahmed, and Ahmad Taher Azar
- Publication: IEEE Access, volume 13 (2025), pages 72852-72874
- DOI: `10.1109/ACCESS.2025.3561240`
- Exact local path: `E:\Cancerdetection\EG-VAN_A_Global_and_Local_Attention-Based_Dual-Branch_Ensemble_Network_With_Advanced_Color_Balancing_for_Multi-Class_Skin_Cancer_Recognition.pdf`
- SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`
- PDF page count: 23

## Table 2 evidence

- Table caption: "Complete detail of 9-class skin cancer dataset."
- Printed page: 72863
- PDF viewer page: 12 (one-based); page index 11 (zero-based)
- Table body: vector Form XObject 510, identified in the PDF as `Table2.pdf`; the R2 source record reports that this isolated form has no image XObjects or inline images.
- Exact per-cell transcription: `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R2_SOURCE_VERIFICATION_20261115T163331Z\TABLE2_SOURCE_TRANSCRIPTION.csv`
- R2 source transcription SHA-256: `b0ce85fa775095e15c07a834b09f81f33935a23230f73538b40cc1dc3b098777`
- R2's visual source verification was retained as the primary cell-level evidence. R2A independently recalculated the values from those literal cell strings and preserved the NV augmented literal `00`.

## Existing project transcription

- Exact path: `E:\Cancerdetection\EG-VAN\analysis\nine_class_research_completion\paper_table2_transcription.csv`
- SHA-256: `0bfac8b73d01e7c0abab31272f18b0e9dffe7793444bbc70f65fe639a2dba705`
- The file remains unchanged. Its NV augmented value is `0`, unlike the paper's literal `00`; R2 recorded this as a source-cell mismatch. R2A does not normalize or repair it.

## Section IV-C source location and method

- Exact heading: `C. IMPLEMENTATION DETAIL`
- Printed page: 72863
- PDF viewer page: 12 (one-based); page index 11 (zero-based)
- PDF page count: 23
- The source's text content stream was extracted without rendering the page. R2A uses the directly extracted count statements and surrounding stage description recorded in the preceding source audit. The relevant text reports 1,332 original testing images, 37,883 training images including original and augmentation images, and 6,686 validation images including original and augmentation images.
- Section IV-C describes a HAM-10000 train/test division, augmentation for the nine-class dataset, and a subsequent training/validation division. It does not specify how Table 2's columns reconcile to those later totals.

## Scope and limitations

No datasets, image archives, patient/lesion images, review queues, predictions, checkpoints, or model files were opened or processed. No training, evaluation, inference, or download was performed. No source code, notebook, label, split, paper, transcription, R1/R2 artifact, or Git state was changed. The printed `00` remains unresolved as a numeric quantity.
