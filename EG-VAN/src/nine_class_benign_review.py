#!/usr/bin/env python3
"""Local human pair-review interface for the retained binary BENIGN records.

Only the new recovery ledger is writable. Source images and audit CSVs are read-only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("analysis/nine_class_recovery/benign_review_plan.csv")
QUEUE = Path("analysis/nine_class_overlap_completion/human_review_queue.csv")
LEDGER = Path("analysis/nine_class_recovery/benign_pair_review_ledger.csv")
SUMMARY = Path("analysis/nine_class_recovery/benign_pair_review_summary.json")
GEOMETRY = Path("analysis/nine_class_recovery/geometric_pair_evidence.csv")
STRONG = Path("analysis/nine_class_recovery/stage3g/strong_pair_identity_evidence.csv")
FEEDBACK_FIELDS = ("candidate_pair_id", "disagrees_with_automated_category",
                   "disagreement_reason", "feedback_timestamp_utc")
PAGE = Path(__file__).with_suffix(".html")
DECISIONS = {"SAME_PHOTO", "SAME_LESION", "DISTINCT", "UNCERTAIN"}
BATCHES = ("T1_source_test", "T2_source_train", "T3_source_train",
           "T4_source_train", "T5_source_train")
FIELDS = ("binary_image_path", "candidate_path", "candidate_pair_id",
          "source_split", "review_batch", "candidate_source",
          "candidate_image_identifier", "phash_distance", "dhash_distance",
          "pixel_mae", "pixel_correlation", "coarse_correlation",
          "reviewer_decision", "reviewer_notes", "review_status",
          "review_timestamp_utc", "evidence_reference")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def csv_text(rows: list[dict[str, str]]) -> str:
    import io
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def feedback_csv_text(rows: list[dict[str, str]]) -> str:
    import io
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=FEEDBACK_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def safe_image_path(root: Path, relative: str, allowed: set[str]) -> Path:
    if relative not in allowed:
        raise ValueError("Image is not in the review queue")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Review image is missing or outside the project")
    return path


class ReviewStore:
    def __init__(self, root: Path = ROOT, ledger: Path = LEDGER, summary: Path = SUMMARY,
                 reviewer_id: str = "primary_existing"):
        self.root = root.resolve()
        self.reviewer_id = reviewer_id
        self.ledger = self.root / ledger
        self.summary_path = self.root / summary
        self.lock = RLock()
        self.plan = read_csv(self.root / PLAN)
        self.queue = read_csv(self.root / QUEUE)
        if len(self.plan) != 83 or len({r["image_path"] for r in self.plan}) != 83:
            raise ValueError("Expected 83 unique retained BENIGN records")
        if len(self.queue) != 760:
            raise ValueError("Focused queue cardinality changed; review source evidence")
        if Counter(row["review_batch"] for row in self.plan) != {
            "T1_source_test": 19, "T2_source_train": 16, "T3_source_train": 16,
            "T4_source_train": 16, "T5_source_train": 16}:
            raise ValueError("Review batch plan changed")
        self.rank = {row["image_path"]: i for i, row in enumerate(self.plan)}
        self.records = {row["image_path"]: row for row in self.plan}
        self.expected = self._expected_rows()
        self.related = defaultdict(list)
        for row in self.expected:
            for path in (row["binary_image_path"], row["candidate_path"]):
                if path in self.records:
                    self.related[path].append(row["candidate_pair_id"])
        if set(self.related) != set(self.records):
            raise ValueError("Every retained BENIGN image must have a queued relation")
        self.allowed_images = {p for row in self.expected for p in
                               (row["binary_image_path"], row["candidate_path"])}
        for path in self.allowed_images:
            safe_image_path(self.root, path, self.allowed_images)
        if self.ledger.exists():
            self.rows = read_csv(self.ledger)
            self._validate_existing()
        else:
            self.rows = [dict(row) for row in self.expected]
            atomic_text(self.ledger, csv_text(self.rows))
        self.by_id = {row["candidate_pair_id"]: row for row in self.rows}
        self.strong = {}
        strong_path = self.root / STRONG
        if strong_path.exists():
            strong_rows = read_csv(strong_path)
            if len(strong_rows) != 83 or len({r["candidate_pair_id"] for r in strong_rows}) != 83:
                raise ValueError("Expected 83 unique Stage 3G strong pairs")
            hidden = {"prior_human_decision", "prior_human_timestamp_utc", "human_ledger_reference"}
            self.strong = {r["candidate_pair_id"]: {key: value for key, value in r.items()
                                                   if key not in hidden}
                           for r in strong_rows}
            if not set(self.strong) <= set(self.by_id):
                raise ValueError("Stage 3G strong pairs do not match review ledger")
            outlier = "data/isic/data/train/benign/1169.jpg"
            test = [r for r in self.plan if r["source_split"] == "test"]
            unusual = [self.records[outlier]]
            train = [r for r in self.plan if r["source_split"] == "train" and r["image_path"] != outlier]
            self.strong_records = test + unusual + train
            if len(self.strong_records) != 83:
                raise ValueError("Strong review order changed")
        else:
            self.strong_records = []
        geometry_path = self.root / GEOMETRY
        self.geometry = {}
        if geometry_path.exists():
            geometry_rows = read_csv(geometry_path)
            if len(geometry_rows) != len(self.rows):
                raise ValueError("Geometric evidence pair count differs from review ledger")
            self.geometry = {row["candidate_pair_id"]: row for row in geometry_rows}
            if set(self.geometry) != set(self.by_id) or any(
                    self.geometry[pair_id]["binary_image_path"] != row["binary_image_path"] or
                    self.geometry[pair_id]["candidate_path"] != row["candidate_path"]
                    for pair_id, row in self.by_id.items()):
                raise ValueError("Geometric evidence pair paths differ from review ledger")
        self.feedback_path = (self.ledger.with_name("benign_pair_evidence_feedback.csv")
                              if self.reviewer_id == "primary_existing" else
                              self.ledger.with_name(f"identity_evidence_feedback_{self.reviewer_id}.csv"))
        if self.feedback_path.exists():
            self.feedback_rows = read_csv(self.feedback_path)
            if len(self.feedback_rows) != len(self.rows) or tuple(self.feedback_rows[0]) != FEEDBACK_FIELDS or \
                    [r["candidate_pair_id"] for r in self.feedback_rows] != [r["candidate_pair_id"] for r in self.rows]:
                raise ValueError("Existing feedback ledger differs from pair list")
        else:
            self.feedback_rows = [dict.fromkeys(FEEDBACK_FIELDS, "") | {"candidate_pair_id": row["candidate_pair_id"]}
                                  for row in self.rows]
            atomic_text(self.feedback_path, feedback_csv_text(self.feedback_rows))
        self.feedback_by_id = {row["candidate_pair_id"]: row for row in self.feedback_rows}
        self._write_summary()

    def _expected_rows(self) -> list[dict[str, str]]:
        selected = []
        seen = set()
        for index, pair in enumerate(self.queue, start=2):
            a, b = pair["path_a"], pair["path_b"]
            attached = [path for path in (a, b) if path in self.records]
            if not attached:
                continue
            key = "\n".join(sorted((a, b)))
            pair_id = hashlib.sha256(key.encode("utf-8")).hexdigest()
            if pair_id in seen:
                raise ValueError("Duplicate candidate pair in focused queue")
            seen.add(pair_id)
            binary = min(attached, key=self.rank.__getitem__)
            candidate = b if a == binary else a
            plan_row = self.records[binary]
            source = "HAM10000" if candidate.startswith("data/raw/HAM10000_images_part_") else "binary"
            identifier = Path(candidate).stem if source == "HAM10000" else "local:" + Path(candidate).name
            selected.append({
                "binary_image_path": binary, "candidate_path": candidate,
                "candidate_pair_id": pair_id, "source_split": plan_row["source_split"],
                "review_batch": plan_row["review_batch"], "candidate_source": source,
                "candidate_image_identifier": identifier,
                "phash_distance": pair["phash_distance"],
                "dhash_distance": pair["dhash_distance"],
                "pixel_mae": pair["pixel_mae"],
                "pixel_correlation": pair["pixel_correlation"],
                "coarse_correlation": pair["coarse_correlation"],
                "reviewer_decision": "", "reviewer_notes": "",
                "review_status": "unreviewed", "review_timestamp_utc": "",
                "evidence_reference": f"{QUEUE.as_posix()}#row={index}",
            })
        selected.sort(key=lambda row: (self.rank[row["binary_image_path"]],
                    row["candidate_path"] != self.records[row["binary_image_path"]]["top_candidate_path"],
                    -float(row["pixel_correlation"]), row["candidate_path"]))
        if len(selected) != 429:
            raise ValueError("Expected 429 unique pairs touching retained BENIGN records")
        return selected

    def _validate_existing(self) -> None:
        if len(self.rows) != len(self.expected):
            raise ValueError("Existing ledger has a different pair count; preserve it for inspection")
        if not self.rows or tuple(self.rows[0]) != FIELDS:
            raise ValueError("Existing ledger schema changed; preserve it for inspection")
        frozen = set(FIELDS) - {"reviewer_decision", "reviewer_notes", "review_status", "review_timestamp_utc"}
        for actual, expected in zip(self.rows, self.expected):
            if any(actual[field] != expected[field] for field in frozen):
                raise ValueError("Existing ledger or source queue changed; preserve it for inspection")
            decision = actual["reviewer_decision"]
            status = actual["review_status"]
            if decision not in DECISIONS | {""} or status != ("reviewed" if decision else "unreviewed"):
                raise ValueError("Existing ledger contains an invalid decision or status")
            if bool(decision) != bool(actual["review_timestamp_utc"]):
                raise ValueError("Existing ledger has an inconsistent timestamp")

    def _summary(self) -> dict:
        decisions = Counter(row["reviewer_decision"] for row in self.rows)
        reviewed = sum(bool(row["reviewer_decision"]) for row in self.rows)
        resolved_decisions = DECISIONS - {"UNCERTAIN"}
        complete = {path for path, pair_ids in self.related.items()
                    if all(self.by_id[pair_id]["reviewer_decision"] in resolved_decisions
                           for pair_id in pair_ids)}
        batch_progress = {}
        for batch in BATCHES:
            members = [row["image_path"] for row in self.plan if row["review_batch"] == batch]
            pair_ids = {pair_id for path in members for pair_id in self.related[path]}
            batch_progress[batch] = {
                "records_total": len(members),
                "records_fully_resolved": sum(path in complete for path in members),
                "related_pairs_total": len(pair_ids),
                "related_pairs_reviewed": sum(bool(self.by_id[p]["reviewer_decision"]) for p in pair_ids),
            }
        return {
            "reviewed_pair_count": reviewed,
            "unreviewed_pair_count": len(self.rows) - reviewed,
            "SAME_PHOTO": decisions["SAME_PHOTO"],
            "SAME_LESION": decisions["SAME_LESION"],
            "DISTINCT": decisions["DISTINCT"],
            "UNCERTAIN": decisions["UNCERTAIN"],
            "binary_records_all_relations_resolved": len(complete),
            "source_test_records_total": 19,
            "remaining_source_test_blockers": sum(
                row["image_path"] not in complete for row in self.plan
                if row["source_split"] == "test"),
            "batch_progress": batch_progress,
            "no_exclusions_applied": True,
        }

    def _write_summary(self) -> None:
        atomic_text(self.summary_path, json.dumps(self._summary(), indent=2) + "\n")

    def snapshot(self) -> dict:
        with self.lock:
            return {"reviewer_id": self.reviewer_id,
                    "records": self.plan, "strong_records": self.strong_records,
                    "strong": self.strong, "pairs": self.rows,
                    "geometry": self.geometry, "feedback": self.feedback_by_id,
                    "summary": self._summary()}

    def save_feedback(self, pair_id: str, disagrees: bool, reason: str) -> dict:
        if not isinstance(disagrees, bool) or not isinstance(reason, str) or len(reason) > 4000:
            raise ValueError("Invalid evidence feedback")
        if disagrees and not reason.strip():
            raise ValueError("Explain why you disagree with the automated evidence category")
        with self.lock:
            if pair_id not in self.feedback_by_id:
                raise ValueError("Unknown candidate pair ID")
            row = self.feedback_by_id[pair_id]
            row["disagrees_with_automated_category"] = "true" if disagrees else "false"
            row["disagreement_reason"] = reason if disagrees else ""
            row["feedback_timestamp_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            atomic_text(self.feedback_path, feedback_csv_text(self.feedback_rows))
            return dict(row)

    def save_decision(self, pair_id: str, decision: str, notes: str) -> dict:
        if decision not in DECISIONS:
            raise ValueError("Choose exactly one of the four allowed decisions")
        if not isinstance(notes, str) or len(notes) > 4000:
            raise ValueError("Reviewer notes must be at most 4000 characters")
        if decision in {"SAME_PHOTO", "SAME_LESION"} and len(notes.strip()) < 20:
            raise ValueError("Positive identity judgments require at least 20 characters of visual explanation")
        with self.lock:
            if pair_id not in self.by_id:
                raise ValueError("Unknown candidate pair ID")
            row = self.by_id[pair_id]
            row["reviewer_decision"] = decision
            row["reviewer_notes"] = notes
            row["review_status"] = "reviewed"
            row["review_timestamp_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            atomic_text(self.ledger, csv_text(self.rows))
            self._write_summary()
            return dict(row)


def handler_for(store: ReviewStore):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, data: dict) -> None:
            self._send(status, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/strong"):
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif parsed.path == "/api/review":
                self._json(200, store.snapshot())
            elif parsed.path.startswith("/image/"):
                relative = unquote(parsed.path.removeprefix("/image/"))
                try:
                    path = safe_image_path(store.root, relative, store.allowed_images)
                except ValueError as exc:
                    self._json(404, {"error": str(exc)})
                    return
                self._send(200, path.read_bytes(), "image/jpeg")
            elif parsed.path in ("/sheet/01", "/sheet/02"):
                number = parsed.path[-2:]
                path = store.root / "analysis/nine_class_recovery" / f"review_sheet_{number}.jpg"
                self._send(200, path.read_bytes(), "image/jpeg")
            elif parsed.path.startswith("/landmarks/"):
                pair_id = parsed.path.removeprefix("/landmarks/")
                evidence = store.geometry.get(pair_id)
                if not evidence or evidence["landmark_visualization_available"] != "true":
                    self._json(404, {"error": "No coherent landmark visualization for this pair"})
                    return
                try:
                    from nine_class_geometric_verification import render_landmarks
                    body = render_landmarks(store.root, evidence)
                except ValueError as exc:
                    self._json(409, {"error": str(exc)})
                    return
                self._send(200, body, "image/jpeg")
            elif parsed.path.startswith("/evidence/"):
                parts = parsed.path.split("/")
                if len(parts) != 4 or parts[2] not in {"overlay", "difference", "landmark"} or parts[3] not in store.strong:
                    self._json(404, {"error": "Unknown strong-pair evidence"})
                    return
                row = store.strong[parts[3]]
                field = {"overlay": "overlay_reference", "difference": "difference_reference",
                         "landmark": "landmark_reference"}[parts[2]]
                relative = row[field]
                try:
                    path = safe_image_path(store.root, relative, {relative})
                except ValueError as exc:
                    self._json(404, {"error": str(exc)})
                    return
                self._send(200, path.read_bytes(), "image/jpeg")
            else:
                self._json(404, {"error": "Not found"})

        def do_POST(self) -> None:
            if self.path not in ("/api/decision", "/api/evidence_feedback"):
                self._json(404, {"error": "Not found"})
                return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self._json(415, {"error": "Expected application/json"})
                return
            if self.headers.get("Origin") not in (None, f"http://{self.headers.get('Host')}"):
                self._json(403, {"error": "Cross-origin request rejected"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192:
                    raise ValueError("Invalid request length")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Invalid request body")
                if self.path == "/api/decision":
                    pair_id, decision, notes = data.get("pair_id"), data.get("decision"), data.get("notes", "")
                    if not isinstance(pair_id, str) or not isinstance(decision, str):
                        raise ValueError("Pair ID and decision must be strings")
                    row = store.save_decision(pair_id, decision, notes)
                else:
                    row = store.save_feedback(data.get("pair_id"), data.get("disagrees"), data.get("reason", ""))
            except (ValueError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)})
                return
            self._json(200, {"saved": row, "summary": store.snapshot()["summary"]})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", action="store_true", help="Create or verify the empty ledger, then exit")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--reviewer", help="Independent second reviewer code; uses a separate Stage 3H ledger")
    args = parser.parse_args()
    if args.reviewer:
        if not re.fullmatch(r"[A-Za-z0-9_-]{2,32}", args.reviewer):
            parser.error("Reviewer code must be 2-32 letters, digits, _ or -")
        if args.reviewer.lower() in {"primary", "primary_existing"}:
            parser.error("Choose a distinct independent reviewer code")
        base = Path("analysis/nine_class_recovery/stage3h")
        store = ReviewStore(ledger=base / f"identity_reviews_{args.reviewer}.csv",
                            summary=base / f"identity_summary_{args.reviewer}.json",
                            reviewer_id=args.reviewer)
    else:
        store = ReviewStore()
    print(json.dumps(store.snapshot()["summary"], indent=2))
    if args.init:
        return
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(store))
    print(f"Open http://127.0.0.1:{args.port}/strong for focused review; Ctrl+C stops the server")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
