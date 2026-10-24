"""Mechanical gates for an externally approved nine-class cohort.

Approval JSON is a recorded research decision, not evidence that software can
independently verify clinical identity or rights. No such approval exists now.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from nine_class_stage4 import CLASS_NAMES

LOCKED_FIELDS = (
    "image_path", "source_dataset", "original_label", "class_name", "class_index",
    "image_id", "lesion_id", "patient_id", "source_split", "sha256",
    "overlap_group", "duplicate_overlap_evidence_tier",
)
REQUIRED_APPROVAL_FIELDS = (
    "approved_by", "approval_date_utc", "adjudication_reference",
    "source_rights_reference", "protected_test_policy_reference",
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_approved_split(root: Path, split_path: Path, approval_path: Path,
                            inventory_path: Path, *,
                            allow_synthetic_fixture: bool = False) -> tuple[list[dict[str, str]], dict]:
    """Reject altered labels, unapproved entries, protected tests and leakage.

    Paths may be outside root (e.g. a mounted approved manifest), but image
    paths within the CSV must be project-relative and cannot escape root.
    """
    root = root.resolve()
    split_path, approval_path, inventory_path = map(Path, (split_path, approval_path, inventory_path))
    for path in (split_path, approval_path, inventory_path):
        if not path.is_file():
            raise FileNotFoundError(f"Approved cohort input missing: {path}")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if approval.get("synthetic_fixture") and not allow_synthetic_fixture:
        raise ValueError("Synthetic test approval cannot authorize a real training run")
    if approval.get("approval_status") != "APPROVED_BY_RESEARCHER":
        raise ValueError("Researcher approval record is missing")
    if any(not str(approval.get(key, "")).strip() for key in REQUIRED_APPROVAL_FIELDS):
        raise ValueError("Approval record lacks reviewer, date or evidence references")
    if approval.get("approved_split_sha256") != file_sha256(split_path):
        raise ValueError("Approved split hash mismatch")
    if approval.get("source_inventory_sha256") != file_sha256(inventory_path):
        raise ValueError("Source inventory hash mismatch")
    inventory = read_rows(inventory_path)
    rows = read_rows(split_path)
    if not rows or not inventory:
        raise ValueError("Empty cohort or source inventory")
    required = set(LOCKED_FIELDS) | {"provisional_eligibility_status", "split"}
    if not required <= rows[0].keys() or not set(LOCKED_FIELDS) <= inventory[0].keys():
        raise ValueError("Approved split or inventory schema incomplete")
    source = {r["image_path"]: r for r in inventory}
    if len(source) != len(inventory):
        raise ValueError("Duplicate source inventory paths")
    if len({r["image_path"] for r in rows}) != len(rows):
        raise ValueError("Duplicate approved split paths")
    partitions = defaultdict(set)
    content_partitions = defaultdict(set)
    lesion_partitions = defaultdict(set)
    patient_partitions = defaultdict(set)
    protected = {r["overlap_group"] for r in inventory if r["source_split"] == "test"}
    for row in rows:
        image_path = row["image_path"]
        if image_path not in source:
            raise ValueError(f"Approved row absent from source inventory: {image_path}")
        if any(row[key] != source[image_path][key] for key in LOCKED_FIELDS):
            raise ValueError(f"Source label, hash, ID or overlap group changed: {image_path}")
        resolved = (root / image_path).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f"Missing image or path outside root: {image_path}")
        if file_sha256(resolved) != row["sha256"]:
            raise ValueError(f"Image bytes differ from the approved source inventory: {image_path}")
        if row["provisional_eligibility_status"] != "APPROVED_ELIGIBLE":
            raise ValueError(f"Unapproved image in split: {image_path}")
        if row["class_name"] not in CLASS_NAMES or int(row["class_index"]) != CLASS_NAMES.index(row["class_name"]):
            raise ValueError(f"Nine-class mapping mismatch: {image_path}")
        split = row["split"]
        if split not in ("train", "validation", "test"):
            raise ValueError(f"Invalid split: {split}")
        if row["source_split"] == "test" and split != "test":
            raise ValueError("Publisher source-test image used for training or validation")
        if split != "test" and row["overlap_group"] in protected:
            raise ValueError("Known or suspected group linked to publisher source test")
        partitions[row["overlap_group"]].add(split)
        content_partitions[row["sha256"]].add(split)
        if row["lesion_id"]:
            lesion_partitions[(row["source_dataset"], row["lesion_id"])].add(split)
        if row["patient_id"]:
            patient_partitions[(row["source_dataset"], row["patient_id"])].add(split)
    for name, groups in (("overlap", partitions), ("exact content", content_partitions),
                         ("lesion", lesion_partitions), ("patient", patient_partitions)):
        if any(len(parts) > 1 for parts in groups.values()):
            raise ValueError(f"Cross-split {name} group")
    counts = {split: Counter(r["class_name"] for r in rows if r["split"] == split)
              for split in ("train", "validation", "test")}
    for split in ("train", "validation"):
        if any(counts[split][name] < 1 for name in CLASS_NAMES):
            raise ValueError(f"Approved {split} lacks one or more nine-class labels")
    return rows, {"approval": approval, "counts": {s: dict(counts[s]) for s in counts},
                  "split_sha256": file_sha256(split_path),
                  "inventory_sha256": file_sha256(inventory_path),
                  "approval_sha256": file_sha256(approval_path),
                  "test_has_all_classes": all(counts["test"][name] > 0 for name in CLASS_NAMES)}
