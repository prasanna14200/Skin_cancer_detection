#!/usr/bin/env python3
"""Blind local review of provisional Stage 3G validation nonmatches."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import urlparse

from nine_class_benign_review import ROOT, atomic_text, read_csv, safe_image_path


QUEUE = Path("analysis/nine_class_recovery/stage3g/blinded_validation_queue.csv")
PAGE = Path(__file__).with_suffix(".html")
DECISIONS = {"SAME_PHOTO", "SAME_LESION", "DISTINCT", "UNCERTAIN"}
FIELDS = ("blind_case_id", "reviewer_id", "reviewer_decision", "reviewer_notes",
          "review_status", "review_timestamp_utc")


def write_rows(path: Path, rows: list[dict]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    atomic_text(path, buffer.getvalue())


class BlindStore:
    def __init__(self, reviewer_id: str, root: Path = ROOT, ledger: Path | None = None):
        if not re.fullmatch(r"[A-Za-z0-9_-]{2,32}", reviewer_id):
            raise ValueError("Reviewer ID must be 2–32 letters, digits, _ or -")
        self.reviewer_id = reviewer_id
        self.root = root.resolve()
        self.lock = RLock()
        self.queue = read_csv(self.root / QUEUE)
        if len(self.queue) != 40 or len({r["blind_case_id"] for r in self.queue}) != 40:
            raise ValueError("Expected 40 unique blind validation cases")
        self.by_case = {r["blind_case_id"]: r for r in self.queue}
        self.ledger = (self.root / ledger) if ledger is not None else (
            self.root / "analysis/nine_class_recovery/stage3g" /
            f"blind_decisions_{reviewer_id}.csv")
        for item in self.queue:
            allowed = {item["source_image_path"], item["comparison_image_path"]}
            for path in allowed:
                safe_image_path(self.root, path, allowed)
        if self.ledger.exists():
            self.rows = read_csv(self.ledger)
            if len(self.rows) != 40 or tuple(self.rows[0]) != FIELDS or \
                    [r["blind_case_id"] for r in self.rows] != [r["blind_case_id"] for r in self.queue]:
                raise ValueError("Existing blind ledger differs from the queue")
            if any(r["reviewer_id"] != reviewer_id or
                   r["reviewer_decision"] not in DECISIONS | {""} or
                   r["review_status"] != ("reviewed" if r["reviewer_decision"] else "unreviewed")
                   for r in self.rows):
                raise ValueError("Existing blind ledger has invalid reviewer decisions")
        else:
            self.rows = [{"blind_case_id": r["blind_case_id"], "reviewer_id": reviewer_id,
                          "reviewer_decision": "", "reviewer_notes": "",
                          "review_status": "unreviewed", "review_timestamp_utc": ""}
                         for r in self.queue]
            write_rows(self.ledger, self.rows)
        self.by_id = {r["blind_case_id"]: r for r in self.rows}

    def snapshot(self) -> dict:
        with self.lock:
            return {"reviewer_id": self.reviewer_id,
                    "cases": [dict(self.by_id[q["blind_case_id"]]) for q in self.queue],
                    "total": 40,
                    "reviewed": sum(bool(r["reviewer_decision"]) for r in self.rows)}

    def image(self, case_id: str, side: str) -> Path:
        if case_id not in self.by_case or side not in {"a", "b"}:
            raise ValueError("Unknown blind case or image side")
        item = self.by_case[case_id]
        relative = item["source_image_path"] if side == "a" else item["comparison_image_path"]
        return safe_image_path(self.root, relative, {item["source_image_path"],
                                                     item["comparison_image_path"]})

    def save(self, case_id: str, decision: str, notes: str) -> dict:
        if case_id not in self.by_id or decision not in DECISIONS:
            raise ValueError("Unknown case or invalid decision")
        if not isinstance(notes, str) or len(notes) > 4000:
            raise ValueError("Notes must be at most 4000 characters")
        if decision in {"SAME_PHOTO", "SAME_LESION"} and len(notes.strip()) < 20:
            raise ValueError("Positive identity judgments require at least 20 characters of visual explanation")
        with self.lock:
            row = self.by_id[case_id]
            row["reviewer_decision"] = decision
            row["reviewer_notes"] = notes
            row["review_status"] = "reviewed"
            row["review_timestamp_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            write_rows(self.ledger, self.rows)
            return dict(row)


def handler_for(store: BlindStore):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status: int, data: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def json(self, status: int, data: dict) -> None:
            self.send(status, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/cases":
                self.json(200, store.snapshot())
            elif path.startswith("/image/"):
                parts = path.split("/")
                try:
                    if len(parts) != 4:
                        raise ValueError("Invalid image URL")
                    image = store.image(parts[2], parts[3])
                except ValueError as exc:
                    self.json(404, {"error": str(exc)})
                    return
                self.send(200, image.read_bytes(), "image/jpeg")
            else:
                self.json(404, {"error": "Not found"})

        def do_POST(self) -> None:
            if self.path != "/api/decision":
                self.json(404, {"error": "Not found"})
                return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self.json(415, {"error": "Expected application/json"})
                return
            if self.headers.get("Origin") not in (None, f"http://{self.headers.get('Host')}"):
                self.json(403, {"error": "Cross-origin request rejected"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192:
                    raise ValueError("Invalid request length")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Invalid request body")
                saved = store.save(body.get("case_id"), body.get("decision"), body.get("notes", ""))
            except (ValueError, json.JSONDecodeError) as exc:
                self.json(400, {"error": str(exc)})
                return
            self.json(200, {"saved": saved, "reviewed": store.snapshot()["reviewed"]})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer", required=True, help="Independent reviewer code, e.g. R1 or R2")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    store = BlindStore(args.reviewer)
    print(f"Blind review for {args.reviewer}: {store.snapshot()['reviewed']}/40 saved")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(store))
    print(f"Open http://127.0.0.1:{args.port}/; Ctrl+C stops the server")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
