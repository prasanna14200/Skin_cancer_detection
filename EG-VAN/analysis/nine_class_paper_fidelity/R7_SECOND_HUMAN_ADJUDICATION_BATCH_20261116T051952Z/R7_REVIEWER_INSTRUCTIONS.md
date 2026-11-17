# R7 Reviewer Instructions

This package prepares 20 relationships for human duplicate adjudication. It does not record decisions, approve the cohort or split, or start training/inference.

## How to review

1. Keep the package in its project location and open `R7_REVIEW_INTERFACE.html` in a browser. Images are referenced by relative paths into the project’s existing `data` directory.
2. Review Image A and Image B side by side. Confirm the pair ID, original queue row, and source paths before assessing.
3. Choose exactly one human label: `SAME_PHOTO`, `DISTINCT_PHOTOS`, or `UNCERTAIN`. No label is preselected.
4. Add reviewer ID, visual evidence notes, and rationale as appropriate. On **Save this human decision**, the browser records the actual UTC timestamp. A human choice is required before Save.
5. Use **Download decision CSV** to export the current decisions using the template columns. Download regularly; saved decisions exist only in the current browser tab and are not written to a server, the R6 ledger, or the source queue.

The two targeted second-review pairs are included because their R6 outcome was unresolved. Their prior human decisions are intentionally not displayed, to keep the second review independent. The other 18 pairs are first-time reviews selected by stable original queue order.

## AI and automated information

Any assessment/status, method, or confidence from the source queue is displayed under **AI ADVISORY — NOT A HUMAN DECISION**. It is not a decision, is not copied into the human-decision CSV, and must not substitute for visual review. Empty advisory fields mean “not recorded.”

## Data handling

Do not alter, rename, crop, or replace the original source images. Do not copy decisions into the R6 ledger or change the dataset/split as part of this review. A saved CSV is an export for later audit; it is not automatically reconciled or approved.
