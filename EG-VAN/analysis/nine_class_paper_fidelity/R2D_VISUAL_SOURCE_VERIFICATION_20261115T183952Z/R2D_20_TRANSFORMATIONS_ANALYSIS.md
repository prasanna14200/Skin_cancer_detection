# R2D: Analysis of the 20 Symbolic Transformations

## Locator and source wording

Section B, “DATA AUGMENTATION,” is on printed page 72857 (viewer page 6; zero-based index 5), page object 47, content stream 122 (`FlateDecode`). The recoverable definition reads:

> “Data augmentation is a technique that creates new data from existing data by applying random transformations.”

The surrounding Section B text discusses augmentation in the HAM-10000 context and a mathematical construction with 20 transformations represented as \(T_j\), indexed from 1 through 20. The paper says each \(T_j\) represents a specific transformation, but the available passage does not identify those operations by name.

The notation establishes a count/indexed set in the formula, not a reproducible operation inventory. No individual transformation name, probability, parameter, or per-class generation rule could be verified from the inspected text. The visual review of p. 72857 did not reveal a separate named list.

## What this reference does and does not establish

| Question | Finding |
|---|---|
| Does “20” count symbolic transformations? | Yes; it is the range of the \(T_j\) set in Section B. |
| Are the 20 operations individually identifiable? | No, not from the source evidence inspected. |
| Is HAM-10000 named? | Yes, in the surrounding discussion. |
| Is a specific train/validation/test assignment supplied for every operation? | Not stated in this passage. |
| Are operation parameters or probabilities supplied? | Not stated in the inspected passage. |
| Is this set explicitly equated with Section G's 13 techniques? | No explicit cross-reference found in the prior complete-paper text search or inspected context. |
| Is this set explicitly equated with the conclusion's 20 alternative methods? | No explicit cross-reference found. |
| Is it tied to Table 2's augmented counts? | No. |

## Reproducibility assessment

The notation is insufficient to reconstruct the transformations or reproduce their application. It must remain distinct from the conclusion's “twenty alternative data augmentation methods”: shared numerical count alone is not evidence that the two references denote the same set. The exact relation remains unresolved/possibly related, not established.

No undocumented transformations are supplied from general machine-learning knowledge.
