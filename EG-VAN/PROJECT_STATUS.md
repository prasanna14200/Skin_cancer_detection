# EG-VAN+ Project Status

## Current nine-class reconstruction status (2026-10-13)

Stage N0 is a paper-and-repository audit, separate from all completed seven-class EG-VAN/EG-VAN+ experiments. The paper describes seven HAM10000 diagnoses plus two source-specific benign/malignant categories (Section IV-A, Table 2), but the identity and image IDs of its additional 3,297-image binary dataset remain **unverified**. Consequently, faithful nine-class dataset construction is **BLOCKED**; Stage N1, downloads, splitting, inference and training have not begun. See `docs/NINE_CLASS_PAPER_RECONSTRUCTION_AUDIT.md`, `docs/NINE_CLASS_DATASET_PROTOCOL.md`, and `docs/NINE_CLASS_RECONSTRUCTION_PLAN.md` for the evidence and N0-N11 gates. The paper's reported nine-class accuracy is not a result of this repository's seven-class studies.

The storage audit also found that the formerly approved duplicate `experiments/stage15_single_candidate_exp1/stage15_single_candidate_exp1/run/last_checkpoint.pt` is now absent. Its absence is an **unresolved storage-audit discrepancy**; no Stage 15 recovery artifact was changed or recreated during N0. The canonical `experiments/stage15_single_candidate_exp1/run/last_checkpoint.pt` remains a separate historical artifact. Only regenerable Python caches were removed to recover working space.

The following sections preserve an earlier Experiment #5 status snapshot; their then-current next steps are historical, not instructions for the nine-class reconstruction.

## Completed

- HAM10000 data preparation and frozen lesion-aware split.
- Leakage-aware EfficientNetV2-S baseline.
- Original PH² external evaluation and paired preprocessing diagnostic (historical; no new PH² access in current stage).
- Controlled Experiments #1–#5, including Experiment #5 recovery and final internal model selection.
- Experiment #5 selected internal checkpoint frozen by its pre-registered validation-constrained minimum-loss rule.
- Saved-prediction internal error analysis.
- Explainability and PH² external-validation protocols prepared.

## Historical Experiment #5 status

- HAM10000 internal model: Experiment #5 checkpoint, epoch 15; SHA256 `81d567f533d08286d5e599b90512d96e92c413ad74c7f4f941d81fc7bb46de3a`.
- All three frozen validation criteria passed at the selected checkpoint.
- Model is internally selected only; the selected Experiment #5 checkpoint has not yet undergone its locked PH² external validation.
- No clinical-generalization claim is made.

## Historical next steps

- Execute the planned internal Grad-CAM case review after approval.
- Perform the single locked PH² evaluation after explicit approval; do not tune from it.
- Continue EG-VAN+/dual-branch architecture research as a separate stage after the internal/external evaluation review.
- Complete final model comparison and research documentation.
- Deployment: not started.
