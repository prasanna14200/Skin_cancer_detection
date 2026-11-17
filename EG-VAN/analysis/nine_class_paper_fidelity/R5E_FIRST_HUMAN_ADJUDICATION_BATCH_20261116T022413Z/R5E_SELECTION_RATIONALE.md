# R5E Selection Rationale

## Selection rule
- Source: `R5_DUPLICATE_ADJUDICATION_QUEUE.csv`
- Criteria: only rows with `review_status` equal to `NOT_HUMAN_REVIEWED` and blank `human_decision` were considered.
- Exclusion: rows already recorded in the existing human-review ledgers were removed before batching.
- Ordering: the queue was processed in its stable row order; this is a transparent batch selection rather than a fabricated priority score.
- Result: the first 20 unresolved, unique, image-readable pairs were selected for the first batch.

## Why this is a safe batch definition
- The queue does not provide a documentable priority score, so row order is used only as a deterministic tie-breaker.
- No AI, similarity, or model-based ranking was introduced.
- Human decisions remain blank and must be filled by a reviewer only.
- The batch is limited to the queue?s unresolved pairs and does not touch the original source data or frozen split.
