# Table 2 Discrepancies

## Direct visual result

The isolated vector table on printed p. 72863 contains six columns and nine data rows. All rows and cells are legible. The exact printed headings, labels, and values are in `TABLE2_SOURCE_TRANSCRIPTION.csv`; comparisons with the existing CSV are in `TABLE2_COMPARISON.csv`.

## Cell and row comparison

- All nine logical class rows and all six table columns are represented in the existing transcription.
- The seven HAM row labels in the paper include descriptive names and their abbreviations in parentheses; the transcription uses the abbreviations. The paper's `Malignant` and `Benign` labels differ from the transcription only by capitalization. These are treated as matching labels, with the printed wording preserved in the source transcription.
- All source-name and numeric cells match except the `Melanocytic Nevi (NV)` row, `Augmented Images` cell: the paper visibly prints `00`; the CSV stores `0`. This is an exact-string `MISMATCH`. The visual source cell is legible as `00`, but the paper provides no note clarifying whether the doubled zero is a typographical/formal representation of numeric zero. No normalization is applied.
- Row order differs: the paper places VASC before NV, then Malignant before Benign; the transcription places NV before VASC, then BENIGN before MALIGNANT. All nine logical rows are present.
- The existing CSV's normalized header names correspond to the six printed headings. The paper prints `Train images` with a lowercase `i`.
- No footnote or qualification is visible in the isolated Table 2 object. The transcription has no footnote field; no omitted table footnote was found.
- Table 2 has no explicit total row. The CSV also has no total row.

## Totals and paper-text accounting

Summing the printed `Original Images`, `Testing Images`, and `Train images` cells gives 13,312, 1,332, and 11,980, respectively; the corresponding existing CSV values sum to the same totals. These are calculated checks, not totals printed in Table 2.

The printed augmented cells sum to 34,554 only if the literal NV value `00` is interpreted as numeric zero. The source transcription retains `00` and labels this sum conditional.

Section IV-C, printed p. 72863, separately reports 37,883 training and 6,686 validation images including original and augmented images. Table 2 has no validation column and provides no rule reconciling its per-class `Augmented Images` counts with those Section IV-C totals. The accounting relationship is therefore `AMBIGUOUS`, not silently repaired.

## Comparison classification counts

The comparison CSV contains 54 cell-level comparisons plus 10 structural/aggregate checks:

- Cell-level: 53 `MATCH`, 1 `MISMATCH`, 0 `AMBIGUOUS`, 0 `NOT_VERIFIABLE`.
- Structural/aggregate checks: 5 `MATCH`, 1 `MISMATCH` (row order), 3 `AMBIGUOUS` (the literal `00` meaning, Section IV-C accounting, and conditional augmented sum), 1 `NOT_PRESENT_IN_SOURCE` (no explicit total row), 0 `NOT_VERIFIABLE`.
- Overall entries: 58 `MATCH`, 2 `MISMATCH`, 3 `AMBIGUOUS`, 1 `NOT_PRESENT_IN_SOURCE`, 0 `NOT_VERIFIABLE`.

The only cell-level mismatch is the NV augmented value. The row-order mismatch does not imply a missing class or a changed count.
