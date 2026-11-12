"""Metadata-only SIIM–ISIC 2020 candidate screen; never approves images."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def screen(metadata: list[dict[str, str]], duplicates: list[dict[str, str]],
           ham: list[dict[str, str]]) -> dict:
    required = {"image_name", "patient_id", "lesion_id", "diagnosis", "benign_malignant", "target"}
    if not metadata or not required <= metadata[0].keys():
        raise ValueError("Official metadata v2 schema incomplete")
    if not ham or "image_id" not in ham[0]:
        raise ValueError("HAM metadata image_id missing")
    rows = {row["image_name"]: row for row in metadata}
    if len(rows) != len(metadata) or "" in rows:
        raise ValueError("Duplicate or blank official image IDs")
    for row in metadata:
        if (row["benign_malignant"], row["target"]) not in {("benign", "0"), ("malignant", "1")}:
            raise ValueError("Unexpected or conflicting official binary labels")
    ham_ids = {row["image_id"] for row in ham}
    if "" in ham_ids or len(ham_ids) != len(ham):
        raise ValueError("Blank or repeated HAM image IDs")
    adjacency: dict[str, set[str]] = defaultdict(set)
    duplicate_label_conflicts = duplicate_patient_conflicts = duplicate_lesion_conflicts = 0
    if duplicates and not {"image_name_1", "image_name_2"} <= duplicates[0].keys():
        raise ValueError("Official duplicate-list schema incomplete")
    for edge in duplicates:
        left, right = edge["image_name_1"], edge["image_name_2"]
        if left not in rows or right not in rows or left == right:
            raise ValueError("Duplicate-list ID absent from metadata or self-linked")
        adjacency[left].add(right)
        adjacency[right].add(left)
        duplicate_label_conflicts += rows[left]["target"] != rows[right]["target"]
        duplicate_patient_conflicts += rows[left]["patient_id"] != rows[right]["patient_id"]
        duplicate_lesion_conflicts += rows[left]["lesion_id"] != rows[right]["lesion_id"]
    direct_overlap = set(rows) & ham_ids
    linked = set(direct_overlap)
    queue = deque(direct_overlap)
    while queue:
        for neighbor in adjacency[queue.popleft()]:
            if neighbor not in linked:
                linked.add(neighbor)
                queue.append(neighbor)
    benign = {image_id for image_id, row in rows.items() if row["target"] == "0"}
    candidate = benign - linked
    parent = {image_id: image_id for image_id in candidate}
    def root(image_id: str) -> str:
        while parent[image_id] != image_id:
            parent[image_id] = parent[parent[image_id]]
            image_id = parent[image_id]
        return image_id
    for edge in duplicates:
        left, right = edge["image_name_1"], edge["image_name_2"]
        if left in parent and right in parent:
            parent[root(left)] = root(right)
    patient_ids = {rows[image_id]["patient_id"] for image_id in candidate if rows[image_id]["patient_id"]}
    lesion_ids = {rows[image_id]["lesion_id"] for image_id in candidate if rows[image_id]["lesion_id"]}
    return {
        "status": "METADATA_ONLY_NOT_ELIGIBILITY_APPROVAL",
        "official_rows": len(rows), "ham_rows": len(ham),
        "official_label_counts": dict(sorted(Counter(row["benign_malignant"] for row in metadata).items())),
        "official_diagnosis_counts": dict(sorted(Counter(row["diagnosis"] for row in metadata).items())),
        "official_duplicate_edges": len(duplicates),
        "official_duplicate_label_conflicts": duplicate_label_conflicts,
        "official_duplicate_patient_id_conflicts": duplicate_patient_conflicts,
        "official_duplicate_lesion_id_conflicts": duplicate_lesion_conflicts,
        "official_missing_patient_ids": sum(not row["patient_id"] for row in metadata),
        "official_missing_lesion_ids": sum(not row["lesion_id"] for row in metadata),
        "direct_ham_image_id_overlap_all_labels": len(direct_overlap),
        "direct_ham_image_id_overlap_benign": len(benign & direct_overlap),
        "ham_id_or_official_duplicate_linked_benign": len(benign & linked),
        "benign_not_ham_id_linked_records_upper_bound": len(candidate),
        "benign_official_duplicate_components_upper_bound": len({root(image_id) for image_id in candidate}),
        "candidate_nonblank_patient_ids": len(patient_ids),
        "candidate_nonblank_lesion_ids": len(lesion_ids),
        "fanconic_image_id_bridge_available": False,
        "photo_overlap_screen_complete": False,
        "approved_eligible_benign": 0,
        "four_way_split_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--duplicates", type=Path, required=True)
    parser.add_argument("--ham-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = screen(read_csv(args.metadata), read_csv(args.duplicates), read_csv(args.ham_metadata))
    report["input_sha256"] = {str(path): sha256(path) for path in
                              (args.metadata, args.duplicates, args.ham_metadata)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
