# R5EC Known Pair Trace

- Known pair A: data/isic/data/test/benign/802.jpg
- Known pair B: data/raw/HAM10000_images_part_1/ISIC_0028399.jpg
- Expected decision: SAME_PHOTO
- Expected timestamp: 2026-10-19T12:25:44+00:00

## Match results in source files
- Ledger match count: 1
- Queue match count: 1
- Selected-batch match count: 0

## Queue mapping
- Queue pair id: PAIR_0124
- Queue source row number: 124
- Queue review_status: NOT_HUMAN_REVIEWED
- Queue human_decision: 

## Why the previous audit failed
- The canonical human decision is stored in the separate review ledger, not in the queue.
- The queue row for this pair is present and correctly maps to PAIR_0124 / source row 124, but its queue-level `review_status` is `NOT_HUMAN_REVIEWED`.
- A queue row with a valid path match is not itself a human adjudication. The human decision must be identified from the ledger and must satisfy the actual ledger semantics (`review_status == "reviewed"` and non-empty `reviewer_decision`).
- Therefore, the old R5E-B failure was a logic bug caused by conflating queue status with genuine human review evidence.
