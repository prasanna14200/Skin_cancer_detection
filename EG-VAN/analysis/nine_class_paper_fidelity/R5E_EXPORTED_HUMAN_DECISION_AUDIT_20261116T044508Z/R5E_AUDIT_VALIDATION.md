# R5E Exported Decision Audit Validation

Validation UTC: 2026-11-16T04:45:08.036194+00:00

## Computed checks
| Check | Result |
|---|---|
| single download csv candidate identified | PASS |
| export read stable and raw schema matches template | PASS |
| exactly 20 expected unique pair ids | PASS |
| queue row numbers 1 through 20 unique | PASS |
| pair1 decision and latest timestamp preserved | PASS |
| 20 explicit decisions and zero pending | PASS |
| all values valid under original r5e documented schema | PASS |
| task allowlist schema conflict reported without normalization | PASS |
| 20 of 20 pair queue image mappings match | PASS |
| supplied decision list matches raw csv | PASS |
| no duplicate pair conflicts | PASS |
| timestamps occupy timestamp field and reviewer ids are blank | PASS |
| ui export code serializes by header without column shift | PASS |

## Counts
- Decisions: SAME_PHOTO=8; DISTINCT_PHOTOS=10; DISTINCT=0; UNCERTAIN=2.
- Explicit nonblank decisions: 20; pending blanks: 0.
- Invalid under original R5E guide/UI: 0.
- Conflict with exact task allowlist: 10 DISTINCT_PHOTOS records.
- Missing reviewer IDs: 20; missing timestamps: 0.
- Duplicate IDs: 0; missing IDs: 0; unexpected IDs: 0.
- Conflicting decisions: 0; queue/image mapping failures: 0.
- PAIR_0001 matches latest final/workflow and prior recovery copies: YES.
- PAIR_0001 timestamp differs from the older first-batch copy: YES; retained export value exactly.
- Browser state comparison: no persistent state exists; the accessible separate tab is not the user's saved tab and is not treated as an authoritative decision source.

## Result interpretation
All 20 rows contain explicit decisions and validate under the original R5E guide and interface. The current task's exact allowlist conflicts with the original workflow over the token `DISTINCT_PHOTOS`; 10 such values are preserved verbatim and flagged. This is a label-schema discrepancy, not an inferred or AI-derived decision. No source was modified.
