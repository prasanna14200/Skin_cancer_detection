# R5E Recovery Validation

Validation UTC: 2026-11-16T04:20:21.343829+00:00

## Computed checks
| Check | Result |
|---|---|
| zip inventory complete and extraction hashes match | PASS |
| archived internal manifest entries validate | PASS |
| all 20 expected pair ids unique | PASS |
| all selected pairs map to unique original queue rows and paths | PASS |
| all lineage fields match queue and visual evidence | PASS |
| only explicit supported decision recovered and valid label | PASS |
| ai only recommendations not misclassified as human | PASS |
| pair1 user decision and required timestamp preserved | PASS |
| pairs2 to20 remain blank and pending | PASS |
| source decision conflicts absent | PASS |
| selected pairs have no ledger review match | PASS |
| missing and ambiguous evidence counts reported | PASS |

## Counts
- ZIP entries inventoried and extracted-byte hashes matched: 4/4.
- Internal archived manifest entries matched: 3/3.
- Expected/unique selected pairs: 20/20.
- Queue mappings validated: 20/20.
- Human decisions preserved: 1; new PAIR_0002–PAIR_0020 decisions recovered: 0.
- AI-only/pending pairs: 19; ambiguous: 0; not found: 0.
- Invalid human decision labels: 0.
- Label vocabulary: only `SAME_PHOTO` was recovered; no `DISTINCT`/`DISTINCT_PHOTOS` conversion was made.
- Selected-pair prior-review ledger matches: 0.
- Decision conflicts: 0. Pair 0001 timestamp discrepancy is separately recorded and is not a decision-label conflict.

The recovery output was built from inspected source rows and status fields. The output manifest is generated after the eight deliverables and is independently verified in a separate command. No source package, queue, image, or review ledger was changed.
