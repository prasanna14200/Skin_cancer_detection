# R5E Selection Rationale

## Selection rule
- Source queue: `R5_DUPLICATE_ADJUDICATION_QUEUE.csv`
- Candidate pool: rows where `review_status` is `NOT_HUMAN_REVIEWED` and `human_decision` is blank.
- Exclusion: any queue row whose paired image paths already appear in a reviewed human-decision ledger was removed before batching.
- Ordering: the candidate rows were kept in stable queue order; no inferred priority score was added.
- Result: the first 20 unresolved, unique pairs were selected for the first batch.

## Human decision status
- All selected rows remain blank for `human_decision` and were not adjudicated by AI or by this script.
- The batch is strictly for review preparation and does not approve the cohort, split, or training pipeline.
