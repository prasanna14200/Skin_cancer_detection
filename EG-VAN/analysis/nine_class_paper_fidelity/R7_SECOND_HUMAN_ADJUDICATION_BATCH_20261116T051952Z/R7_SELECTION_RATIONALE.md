# R7 Selection Rationale

Generated: `2026-11-16T05:19:52Z`

## Selection policy and explicit exception

The original R5E selection rationale defines ordering as stable original-queue order, with no inferred priority score. R7 follows that policy for unreviewed candidates: it selected the next 18 `UNREVIEWED` relationships after R6, queue rows 21–38. AI confidence and recommendations were not used to rank pairs.

The R6 reconciliation records 21 human-reviewed relationships, including two `UNCERTAIN` results. You authorized a targeted second-review exception for both readable uncertain relationships, despite the general no-overlap rule. Therefore exactly two reviewed relationships overlap this batch by explicit authorization; the remaining 18 have no R6-reviewed pair or path overlap. The prior human decisions are not copied into the R7 template or shown in the interface.

## Selected pairs

- `PAIR_0013` (queue row 13): TARGETED_SECOND_REVIEW
- `PAIR_0016` (queue row 16): TARGETED_SECOND_REVIEW
- `PAIR_0021` (queue row 21): UNREVIEWED
- `PAIR_0022` (queue row 22): UNREVIEWED
- `PAIR_0023` (queue row 23): UNREVIEWED
- `PAIR_0024` (queue row 24): UNREVIEWED
- `PAIR_0025` (queue row 25): UNREVIEWED
- `PAIR_0026` (queue row 26): UNREVIEWED
- `PAIR_0027` (queue row 27): UNREVIEWED
- `PAIR_0028` (queue row 28): UNREVIEWED
- `PAIR_0029` (queue row 29): UNREVIEWED
- `PAIR_0030` (queue row 30): UNREVIEWED
- `PAIR_0031` (queue row 31): UNREVIEWED
- `PAIR_0032` (queue row 32): UNREVIEWED
- `PAIR_0033` (queue row 33): UNREVIEWED
- `PAIR_0034` (queue row 34): UNREVIEWED
- `PAIR_0035` (queue row 35): UNREVIEWED
- `PAIR_0036` (queue row 36): UNREVIEWED
- `PAIR_0037` (queue row 37): UNREVIEWED
- `PAIR_0038` (queue row 38): UNREVIEWED

- Targeted second-review exceptions: `PAIR_0013, PAIR_0016`.
- Newly selected, previously unreviewed pairs: 18.
- Selection order among unreviewed candidates is the original queue order, following the original R5E selection rationale.

## Image eligibility and exclusions

All selected images were checked from their original paths and decoded with Pillow. Selected image count: **40/40 decoded**. No image was copied, transformed, or modified.

- None. Both uncertain pairs and the first 18 eligible unreviewed pairs were readable.

Any candidate that could not be decoded would be recorded as `EXCLUDED` in `R7_IMAGE_VALIDATION.csv`, with the next eligible unreviewed queue pair considered instead; there were no such exclusions for the selected 20.

## Source evidence hashes

- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R6_HUMAN_DECISION_LEDGER_RECONCILIATION_20261116T045630Z\R6_DUPLICATE_QUEUE_STATUS.csv` — SHA-256 `8f71b5e3ac176dedb5df5f543b9f1a078515d7b8142cb0abe5c6d70a62bbb7e5`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R6_HUMAN_DECISION_LEDGER_RECONCILIATION_20261116T045630Z\R6_RECONCILED_HUMAN_DECISIONS.csv` — SHA-256 `fd405d1515ffcf292014ded1f26bce9aa5a3fcee70accb2b752c9c00be6b571b`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R6_HUMAN_DECISION_LEDGER_RECONCILIATION_20261116T045630Z\R6_RECONCILIATION_REPORT.md` — SHA-256 `d32bb5ed6cd11308931e417c8bd36f47f0422bf140f37b36c18b77623ff3e4ae`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R6_HUMAN_DECISION_LEDGER_RECONCILIATION_20261116T045630Z\R6_VALIDATION.md` — SHA-256 `bdf77078077390c48e7db4e5b4661a258cca4175c35fe6b295fda404e9bad7e0`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R6_HUMAN_DECISION_LEDGER_RECONCILIATION_20261116T045630Z\R6_MANIFEST.sha256` — SHA-256 `de3ded6778ce4e8341ac3c2323c9f73597bb6e891f8b597a478d57426831a428`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5_COHORT_HUMAN_REVIEW_PREPARATION_20261115T214500Z\R5_DUPLICATE_ADJUDICATION_QUEUE.csv` — SHA-256 `11a286b366ce7b07bc9f88fc69b9404ea47acba6b69a8c4f48a089a71514f7cc`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_HUMAN_REVIEW_WORKFLOW_20261116T041034Z\R5E_REVIEW_INTERFACE.html` — SHA-256 `9bfa36822d911546c83572b1a68c8f13889d4c9fb2c013c10a60c47756b181ca`
- `E:\Cancerdetection\EG-VAN\analysis\nine_class_paper_fidelity\R5E_FIRST_HUMAN_ADJUDICATION_BATCH_20261116T022438Z\R5E_SELECTION_RATIONALE.md` — SHA-256 `0b4b4975f49a2d3949cb6720cdbdc4b003997b6efe4e47716390ab4b8d531351`
