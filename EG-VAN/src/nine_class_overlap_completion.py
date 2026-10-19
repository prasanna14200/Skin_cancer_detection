#!/usr/bin/env python3
"""Checkpointed second-pass overlap screening; never edits the source audit."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from nine_class_overlap_review import (ROOT, CANDIDATES, FINGERPRINTS, HAM_METADATA,
    PIXEL_MAX_MAE, PIXEL_MIN_CORRELATION, PRIORITY_HASH_DISTANCE,
    duplicate_groups, exclusion_reasons, pixel_evidence, read_inputs, sha256)

PREVIOUS = Path("analysis/nine_class_overlap_review")
OUTPUT = Path("analysis/nine_class_overlap_completion")
BATCH_SIZE = 2000
FIELDS = ("candidate_index", "path_a", "path_b", "scope", "phash_distance",
          "dhash_distance", "coarse_mae_8bit", "coarse_correlation", "gradient_correlation",
          "pixel_mae", "pixel_correlation", "decision", "human_review_status")


def csv_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


@lru_cache(maxsize=14000)
def thumb(root_text: str, rel: str) -> np.ndarray:
    image = cv2.imread(str(Path(root_text) / rel), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Cannot decode {rel}")
    return cv2.resize(image, (64, 64), interpolation=cv2.INTER_AREA)


def corr(x: np.ndarray, y: np.ndarray) -> float:
    x = x.astype(np.float32).ravel()
    y = y.astype(np.float32).ravel()
    x -= x.mean()
    y -= y.mean()
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(np.dot(x, y) / denominator) if denominator > 0 else 0.0


def coarse_evidence(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    mae = float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))
    edge_a = cv2.Laplacian(a, cv2.CV_32F)
    edge_b = cv2.Laplacian(b, cv2.CV_32F)
    return round(mae, 6), round(corr(a, b), 8), round(corr(edge_a, edge_b), 8)


def full_review_needed(candidate: dict, mae: float, correlation: float, gradient: float) -> bool:
    p, d = int(candidate["phash_distance"]), int(candidate["dhash_distance"])
    return min(p, d) <= 2 or max(p, d) <= 8 or mae <= 10 or correlation >= .96 or gradient >= .85


def classify_full(pixels: dict) -> str:
    if (pixels["pixel_mae"] <= PIXEL_MAX_MAE and
            pixels["pixel_correlation"] >= PIXEL_MIN_CORRELATION):
        return "confirmed_direct_pixel_automated"
    return "unresolved_human_review"


def contact_sheets(root: Path, output: Path, rows: list[dict], max_pairs: int = 24) -> None:
    """Small review aids only; creating a sheet does not adjudicate a pair."""
    for page_start in range(0, min(max_pairs, len(rows)), 12):
        sheet = np.full((4 * 215, 3 * 360, 3), 255, dtype=np.uint8)
        for local_index, row in enumerate(rows[page_start:page_start+12]):
            y, x = divmod(local_index, 3)
            top, left = y * 215, x * 360
            for offset, path in ((0, row["path_a"]), (174, row["path_b"])):
                image = cv2.imread(str(root / path), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError(f"Cannot decode contact-sheet image {path}")
                image = cv2.resize(image, (170, 170), interpolation=cv2.INTER_AREA)
                sheet[top:top+170, left+offset:left+offset+170] = image
            label = f"#{page_start+local_index+1} corr={float(row['pixel_correlation']):.6f}"
            cv2.putText(sheet, label, (left+3, top+184), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 0, 0), 1)
            cv2.putText(sheet, Path(row["path_a"]).name + " / " + Path(row["path_b"]).name,
                        (left+3, top+202), cv2.FONT_HERSHEY_SIMPLEX, .36, (0, 0, 0), 1)
        if not cv2.imwrite(str(output / f"review_sheet_{page_start//12+1:02d}.jpg"), sheet):
            raise ValueError("Cannot write contact sheet")


def run(root: Path = ROOT, output: Path = OUTPUT) -> dict:
    root, output = root.resolve(), (root / output).resolve()
    if output == (root / CANDIDATES).resolve().parent or output == (root / PREVIOUS).resolve():
        raise ValueError("Cannot overwrite original audits")
    records, candidates, _, _ = read_inputs(root)
    broad = [(i, row) for i, row in enumerate(candidates) if
             max(int(row["phash_distance"]), int(row["dhash_distance"])) > PRIORITY_HASH_DISTANCE]
    previous = csv_rows(root / PREVIOUS / "review_decisions.csv")
    unresolved = [row for row in previous if row["decision"] == "unresolved_human_review"]
    if len(broad) != 38584 or len(unresolved) != 449:
        raise ValueError("Stage 3 input cardinality changed; review protocol before rerun")
    inputs = {str(path): sha256(root / path) for path in
              (CANDIDATES, FINGERPRINTS, HAM_METADATA, PREVIOUS / "review_decisions.csv")}
    output.mkdir(parents=True, exist_ok=True)
    config_path = output / "screen_config.json"
    config = {"input_sha256": inputs, "batch_size": BATCH_SIZE,
              "full_review_rule": "min(pHash,dHash)<=2 OR max<=8 OR coarse_MAE<=10/255 OR grayscale_correlation>=0.96 OR Laplacian_correlation>=0.85",
              "confirmation_rule": "full native-binary-pixel MAE<=2/255 AND correlation>=0.999",
              "coarse_rule": "64x64 grayscale INTER_AREA; all broad pairs scored",
              "unresolved_rule": "never infer nonmatch from low similarity; no human adjudication"}
    if config_path.exists() and json.loads(config_path.read_text(encoding="utf-8")) != config:
        raise ValueError("Screen inputs or rules changed; use a new output directory")
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    root_text = str(root)
    batch_paths = []
    for start in range(0, len(broad), BATCH_SIZE):
        batch = broad[start:start+BATCH_SIZE]
        destination = output / f"broad_batch_{start//BATCH_SIZE:03d}.csv"
        batch_paths.append(destination)
        if destination.exists():
            rows = csv_rows(destination)
            if len(rows) != len(batch) or tuple(rows[0]) != FIELDS or any(
                    int(saved["candidate_index"]) != index for saved, (index, _) in zip(rows, batch)):
                raise ValueError(f"Invalid checkpoint: {destination}")
            continue
        rows = []
        for index, candidate in batch:
            a, b = candidate["path_a"], candidate["path_b"]
            mae, correlation, gradient = coarse_evidence(thumb(root_text, a), thumb(root_text, b))
            full = full_review_needed(candidate, mae, correlation, gradient)
            pixels = pixel_evidence(root, a, b) if full else {}
            decision = classify_full(pixels) if full else "screened_low_priority_unresolved"
            rows.append({"candidate_index": index, **candidate, "coarse_mae_8bit": mae,
                         "coarse_correlation": correlation, "gradient_correlation": gradient,
                         "pixel_mae": pixels.get("pixel_mae", ""),
                         "pixel_correlation": pixels.get("pixel_correlation", ""),
                         "decision": decision, "human_review_status": "not_human_reviewed"})
        temp = destination.with_suffix(".tmp")
        write_rows(temp, FIELDS, rows)
        temp.replace(destination)
        print(f"screened broad batch {start//BATCH_SIZE+1}/{len(range(0,len(broad),BATCH_SIZE))}", flush=True)
    broad_rows = [r for path in batch_paths for r in csv_rows(path)]
    if len(broad_rows) != len(broad):
        raise ValueError("Incomplete broad screening")
    second_pass = []
    for row in unresolved:
        a, b = row["path_a"], row["path_b"]
        mae, correlation, gradient = coarse_evidence(thumb(root_text, a), thumb(root_text, b))
        second_pass.append({**row, "coarse_mae_8bit": mae,
                            "coarse_correlation": correlation, "gradient_correlation": gradient,
                            "second_pass_decision": "unresolved_human_review",
                            "human_review_status": "not_human_reviewed"})
    second_pass.sort(key=lambda r: (-float(r["pixel_correlation"]), float(r["pixel_mae"]), r["path_a"], r["path_b"]))
    visual_path = output / "assistant_visual_reviews.csv"
    visual = csv_rows(visual_path) if visual_path.exists() else []
    unresolved_pairs = {(r["path_a"], r["path_b"]): r for r in second_pass}
    if len(visual) != len({(r["path_a"], r["path_b"]) for r in visual}):
        raise ValueError("Repeated assistant visual review pair")
    for row in visual:
        key = (row["path_a"], row["path_b"])
        if (key not in unresolved_pairs or row["decision"] != "confirmed_visual_assistant" or
                row["human_review_status"] != "not_human_reviewed" or
                row["pixel_mae"] != unresolved_pairs[key]["pixel_mae"] or
                row["pixel_correlation"] != unresolved_pairs[key]["pixel_correlation"] or
                not (output / row["contact_sheet"]).is_file()):
            raise ValueError(f"Invalid assistant visual review evidence: {key}")
        unresolved_pairs[key]["second_pass_decision"] = "confirmed_visual_assistant"
        unresolved_pairs[key]["decision"] = "confirmed_visual_assistant"
    write_rows(output / "priority_second_pass.csv", tuple(second_pass[0]), second_pass)
    confirmed = [r for r in previous + broad_rows if r["decision"].startswith("confirmed")] + visual
    exact = csv_rows(root / PREVIOUS / "confirmed_duplicate_groups.csv")
    sha_groups: dict[str, list[str]] = defaultdict(list)
    for row in exact:
        if row["sha256"]:
            sha_groups[row["sha256"]].append(row["image_path"])
    edges = [(r["path_a"], r["path_b"]) for r in confirmed]
    edges.extend((paths[0], p) for paths in sha_groups.values() for p in paths[1:])
    groups = duplicate_groups(sorted(records), edges)
    group_rows, exclusion_rows = [], []
    for group in groups:
        gid = "DG-" + hashlib.sha256("\n".join(group).encode()).hexdigest()[:16]
        reasons = exclusion_reasons(group, records)
        for p in group:
            group_rows.append({"duplicate_group": gid, "image_path": p,
                               "source_dataset": records[p]["source"], "original_label": records[p]["label"],
                               "source_split": records[p]["source_split"], "group_size": len(group)})
        for p, reason in reasons.items():
            exclusion_rows.append({"image_path": p, "original_label": records[p]["label"],
                                   "source_split": records[p]["source_split"],
                                   "duplicate_group": gid, "reason": reason,
                                   "confirmed_group_members": "|".join(group)})
    exclusion_rows.sort(key=lambda r: r["image_path"])
    write_rows(output / "confirmed_groups.csv", tuple(group_rows[0]), group_rows)
    write_rows(output / "proposed_binary_exclusions.csv", tuple(exclusion_rows[0]), exclusion_rows)
    excluded = {r["image_path"] for r in exclusion_rows}
    pending = [r for r in second_pass + broad_rows if not r["decision"].startswith("confirmed") and
               (r["path_a"] not in excluded or (records[r["path_b"]]["source"] == "binary" and r["path_b"] not in excluded))]
    pending_paths = {p for r in pending for p in (r["path_a"], r["path_b"]) if records[p]["source"] == "binary" and p not in excluded}
    # The remaining low-priority pairs stay in their checkpoint CSVs; putting
    # all of them in a human queue would bury the cases with full pixel evidence.
    review_queue = [r for r in pending if r["decision"] == "unresolved_human_review"]
    review_queue.sort(key=lambda r: (0 if r.get("decision") == "unresolved_human_review" else 1,
                               -float(r.get("pixel_correlation") or 0),
                               -float(r["coarse_correlation"]), r["path_a"], r["path_b"]))
    queue_fields = ("path_a", "path_b", "scope", "phash_distance", "dhash_distance",
                    "coarse_mae_8bit", "coarse_correlation", "gradient_correlation",
                    "pixel_mae", "pixel_correlation", "decision", "human_review_status")
    write_rows(output / "human_review_queue.csv", queue_fields, review_queue)
    if not (output / "review_sheet_01.jpg").exists():
        contact_sheets(root, output, review_queue)
    retained = [r for r in records.values() if r["source"] == "binary" and r["path"] not in excluded]
    summary = {"stage": "proposed_protocol_not_manifest_or_split",
               "broad_pairs_screened": len(broad_rows),
               "broad_full_pixel_scored": sum(bool(r["pixel_mae"]) for r in broad_rows),
               "broad_new_confirmed_pairs": sum(r["decision"].startswith("confirmed") for r in broad_rows),
               "priority_pairs_second_pass": len(second_pass),
               "priority_assistant_visual_confirmed": len(visual),
               "assistant_visual_review_sha256": sha256(visual_path) if visual_path.exists() else "",
               "priority_still_unresolved": len(second_pass) - len(visual),
               "broad_still_unresolved": sum(not r["decision"].startswith("confirmed") for r in broad_rows),
               "human_review_queue_pairs_touching_retained_binary": len(review_queue),
               "low_priority_unresolved_pairs_touching_retained_binary": len(pending) - len(review_queue),
               "retained_binary_records_with_unresolved_candidate": len(pending_paths),
               "confirmed_duplicate_groups": len(groups),
               "proposed_binary_exclusions": len(exclusion_rows),
               "retained_binary_by_label_split": {f"{label}/{split}": sum(r["label"] == label and r["source_split"] == split for r in retained)
                                                   for label in ("benign", "malignant") for split in ("train", "test")},
               "retained_binary_total": len(retained),
               "ham_class_counts": dict(sorted(Counter(r["label"] for r in records.values() if r["source"] == "HAM10000").items())),
               "potential_source_entry_upper_bound": 10015 + len(retained),
               "source_test_confirmed_ham_overlap": sum(r["decision"].startswith("confirmed") and r["scope"] == "binary_ham" and records[r["path_a"]]["source_split"] == "test" for r in confirmed),
               "input_sha256": inputs}
    (output / "completion_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
