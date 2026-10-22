#!/usr/bin/env python3
"""Reconcile two completed blind reviews without changing their original ledgers."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path

from nine_class_benign_review import ROOT, atomic_text, read_csv, sha256
from nine_class_blinded_validation_review import DECISIONS, FIELDS as REVIEW_FIELDS, QUEUE


OUTPUT = Path("analysis/nine_class_recovery/stage3h")
RESULT_FIELDS = ("blind_case_id", "reviewer_a_id", "reviewer_a_decision",
                 "reviewer_a_notes", "reviewer_a_timestamp_utc", "reviewer_b_id",
                 "reviewer_b_decision", "reviewer_b_notes", "reviewer_b_timestamp_utc",
                 "initial_agreement", "reconciliation_status")
ADJUDICATION_FIELDS = ("blind_case_id", "adjudicator_id", "final_adjudication",
                       "adjudication_explanation", "adjudication_timestamp_utc")


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    atomic_text(path, buffer.getvalue())


def read_complete(path: Path, case_ids: list[str]) -> tuple[str, dict[str, dict]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows = read_csv(path)
    if len(rows) != 40 or tuple(rows[0]) != REVIEW_FIELDS or \
            [r["blind_case_id"] for r in rows] != case_ids:
        raise ValueError(f"Blind ledger pair list or schema changed: {path}")
    reviewers = {r["reviewer_id"] for r in rows}
    if len(reviewers) != 1:
        raise ValueError(f"Blind ledger has multiple reviewer IDs: {path}")
    if any(r["review_status"] != "reviewed" or r["reviewer_decision"] not in DECISIONS or
           not r["review_timestamp_utc"] for r in rows):
        raise ValueError(f"Blind review is incomplete: {path}")
    if any(r["reviewer_decision"] in {"SAME_PHOTO", "SAME_LESION"} and
           len(r["reviewer_notes"].strip()) < 20 for r in rows):
        raise ValueError(f"Positive identity judgment lacks an explanation: {path}")
    return next(iter(reviewers)), {r["blind_case_id"]: r for r in rows}


def reconcile(queue_path: Path, ledger_a: Path, ledger_b: Path, output: Path) -> dict:
    queue = read_csv(queue_path)
    if len(queue) != 40 or len({r["blind_case_id"] for r in queue}) != 40:
        raise ValueError("Expected 40 unique blind cases")
    case_ids = [r["blind_case_id"] for r in queue]
    reviewer_a, a = read_complete(ledger_a, case_ids)
    reviewer_b, b = read_complete(ledger_b, case_ids)
    if reviewer_a == reviewer_b or ledger_a.resolve() == ledger_b.resolve():
        raise ValueError("Two distinct reviewers and ledgers are required")
    result_path = output / "validation_reconciliation.csv"
    adjudication_path = output / "validation_adjudication.csv"
    summary_path = output / "validation_reconciliation_summary.json"
    if any(path.exists() for path in (result_path, adjudication_path, summary_path)):
        raise FileExistsError("Preserving an existing reconciliation or adjudication record")
    source_hashes = {str(path): sha256(path) for path in (queue_path, ledger_a, ledger_b)}
    rows = []
    for case_id in case_ids:
        first, second = a[case_id], b[case_id]
        same = first["reviewer_decision"] == second["reviewer_decision"]
        if not same:
            status = "UNRESOLVED_DISAGREEMENT"
        elif first["reviewer_decision"] == "UNCERTAIN":
            status = "UNRESOLVED_UNCERTAIN"
        else:
            status = "AGREEMENT_REQUIRES_SOURCE_CHECK"
        rows.append({"blind_case_id": case_id,
                     "reviewer_a_id": reviewer_a, "reviewer_a_decision": first["reviewer_decision"],
                     "reviewer_a_notes": first["reviewer_notes"],
                     "reviewer_a_timestamp_utc": first["review_timestamp_utc"],
                     "reviewer_b_id": reviewer_b, "reviewer_b_decision": second["reviewer_decision"],
                     "reviewer_b_notes": second["reviewer_notes"],
                     "reviewer_b_timestamp_utc": second["review_timestamp_utc"],
                     "initial_agreement": "yes" if same else "no",
                     "reconciliation_status": status})
    summary = {"reviewer_a": reviewer_a, "reviewer_b": reviewer_b,
               "cases": len(rows), "status_counts": dict(Counter(r["reconciliation_status"] for r in rows)),
               "source_sha256": source_hashes,
               "final_adjudications_recorded": 0,
               "detector_error_metrics_available": False}
    output.mkdir(parents=True, exist_ok=True)
    write_csv(result_path, RESULT_FIELDS, rows)
    write_csv(adjudication_path, ADJUDICATION_FIELDS,
              [{"blind_case_id": case_id} for case_id in case_ids])
    atomic_text(summary_path, json.dumps(summary, indent=2) + "\n")
    if any(sha256(Path(path)) != value for path, value in source_hashes.items()):
        raise ValueError("Source review files changed during reconciliation")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-a", required=True)
    parser.add_argument("--reviewer-b", required=True)
    args = parser.parse_args()
    base = ROOT / "analysis/nine_class_recovery/stage3g"
    first = base / f"blind_decisions_{args.reviewer_a}.csv"
    second = base / f"blind_decisions_{args.reviewer_b}.csv"
    print(json.dumps(reconcile(ROOT / QUEUE, first, second, ROOT / OUTPUT), indent=2))


if __name__ == "__main__":
    main()
