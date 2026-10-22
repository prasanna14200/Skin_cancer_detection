"""Stage 4 source manifest and conservative nine-label split gate.

This module records evidence; it does not approve proposed exclusions or create a
final evaluation partition. Run ``python src/nine_class_stage4.py`` once in a
new output directory. Raw photographs and previous audit files are read-only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "nine_class_stage4"
CLASS_NAMES = ("AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT")
CLASS_TO_INDEX = {name: i for i, name in enumerate(CLASS_NAMES)}
MANIFEST_COLUMNS = (
    "image_path", "source_dataset", "original_label", "class_name", "class_index",
    "image_id", "lesion_id", "patient_id", "source_split", "sha256",
    "overlap_group", "duplicate_overlap_evidence_tier", "provisional_eligibility_status",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Groups:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, first: str, second: str) -> None:
        a, b = self.find(first), self.find(second)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def discover_records(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    metadata = read_csv(root / "data/raw/HAM10000_metadata.csv")
    ham_paths = {}
    for directory in ("HAM10000_images_part_1", "HAM10000_images_part_2"):
        for path in (root / "data/raw" / directory).glob("*.jpg"):
            if path.stem in ham_paths:
                raise ValueError(f"Duplicate HAM image ID: {path.stem}")
            ham_paths[path.stem] = path.relative_to(root).as_posix()
    if len(metadata) != len(ham_paths) or {r["image_id"] for r in metadata} != set(ham_paths):
        raise ValueError("HAM metadata and original images differ")
    records = []
    for meta in metadata:
        label = meta["dx"].upper()
        if label not in CLASS_TO_INDEX or label in ("BENIGN", "MALIGNANT"):
            raise ValueError(f"Unexpected HAM diagnosis {label}")
        records.append(dict(image_path=ham_paths[meta["image_id"]], source_dataset="HAM10000",
                            original_label=meta["dx"], class_name=label,
                            class_index=str(CLASS_TO_INDEX[label]), image_id=meta["image_id"],
                            lesion_id=meta["lesion_id"], patient_id="", source_split=""))
    binary_root = root / "data/isic/data"
    for split in ("train", "test"):
        for label in ("benign", "malignant"):
            for path in sorted((binary_root / split / label).glob("*.jpg")):
                name = label.upper()
                records.append(dict(image_path=path.relative_to(root).as_posix(),
                                    source_dataset="FANCONIC_LOCAL_UNVERIFIED_VERSION",
                                    original_label=label, class_name=name,
                                    class_index=str(CLASS_TO_INDEX[name]), image_id="",
                                    lesion_id="", patient_id="", source_split=split))
    if len(records) != 13312 or len({r["image_path"] for r in records}) != len(records):
        raise ValueError(f"Expected 13,312 unique canonical paths, found {len(records)}")
    if Counter(r["class_name"] for r in records) != Counter({
        "AKIEC": 327, "BCC": 514, "BKL": 1099, "DF": 115, "MEL": 1113,
        "NV": 6705, "VASC": 142, "BENIGN": 1800, "MALIGNANT": 1497}):
        raise ValueError("Source class counts changed")
    return records, metadata


def build_manifest(root: Path = ROOT) -> tuple[list[dict[str, str]], dict]:
    records, _ = discover_records(root)
    by_path = {r["image_path"]: r for r in records}
    excluded = {r["image_path"]: r for r in read_csv(root / "analysis/nine_class_overlap_completion/proposed_binary_exclusions.csv")}
    edges = read_csv(root / "analysis/nine_class_recovery/stage3i/proposed_overlap_edges.csv")
    ai = read_csv(root / "analysis/nine_class_recovery/stage3i/ai_pair_review.csv")
    if len(excluded) != 2369 or len(ai) != 429:
        raise ValueError("Frozen overlap evidence has changed")
    groups = Groups()
    lesion_first = {}
    for row in records:
        groups.find(row["image_path"])
        if row["lesion_id"]:
            lesion = row["lesion_id"]
            if lesion in lesion_first:
                groups.union(row["image_path"], lesion_first[lesion])
            else:
                lesion_first[lesion] = row["image_path"]
    tiers = defaultdict(set)
    for edge in edges:
        a, b = edge["path_a"], edge["path_b"]
        if a not in by_path or b not in by_path:
            raise ValueError(f"Unknown overlap path: {a} / {b}")
        groups.union(a, b)
        tiers[a].add(edge["evidence_tier"])
        tiers[b].add(edge["evidence_tier"])
    ai_same = {r["binary_image_path"] for r in ai if r["ai_assessment"] == "AI_SAME_PHOTO"}
    ai_uncertain = {r["binary_image_path"] for r in ai if r["ai_assessment"] == "AI_UNCERTAIN"}
    if len(ai_same) != 83:
        raise ValueError("Stage 3I 83-pair evidence changed")
    members = defaultdict(list)
    for row in records:
        members[groups.find(row["image_path"])].append(row)
    group_ids = {}
    for member_rows in members.values():
        paths = sorted(r["image_path"] for r in member_rows)
        group_id = "G-" + hashlib.sha256("\n".join(paths).encode()).hexdigest()[:16]
        for path in paths:
            group_ids[path] = group_id
    protected_groups = {
        group_ids[r["image_path"]] for r in records
        if r["source_dataset"] != "HAM10000" and r["source_split"] == "test"
    }
    for row in records:
        path = row["image_path"]
        source = root / path
        if not source.is_file():
            raise FileNotFoundError(source)
        row["sha256"] = sha256(source)
        row["overlap_group"] = group_ids[path]
        row["duplicate_overlap_evidence_tier"] = "|".join(sorted(tiers[path])) or "NONE_RECORDED"
        if path in excluded:
            status = "PRIOR_PROPOSED_EXCLUSION_NOT_APPROVED"
        elif path in ai_same:
            status = "AI_SAME_PHOTO_QUARANTINE"
        elif path in ai_uncertain:
            status = "AI_UNCERTAIN_QUARANTINE"
        elif row["source_split"] == "test":
            status = "PROTECTED_SOURCE_TEST_UNADJUDICATED"
        elif row["overlap_group"] in protected_groups:
            status = "PROTECTED_TEST_LINK_QUARANTINE"
        elif row["source_dataset"] == "HAM10000":
            status = "HAM_AVAILABLE_NOT_FINAL_ELIGIBLE"
        else:
            status = "BINARY_PROVISIONAL_SOURCE_TRAIN"
        row["provisional_eligibility_status"] = status
    # Hash equality is a photographic relation even if an earlier edge missed it.
    hash_groups = defaultdict(list)
    for row in records:
        hash_groups[row["sha256"]].append(row)
    for same_hash_rows in hash_groups.values():
        if len(same_hash_rows) > 1 and len({r["overlap_group"] for r in same_hash_rows}) > 1:
            raise ValueError("Exact duplicate spans unlinked overlap groups")
    summary = {
        "source_counts": dict(sorted(Counter(r["class_name"] for r in records).items())),
        "eligibility_status_counts": dict(sorted(Counter(r["provisional_eligibility_status"] for r in records).items())),
        "evidence_tier_counts": dict(sorted(Counter(t for ts in tiers.values() for t in ts).items())),
        "exact_duplicate_sha_groups": sum(len(rows) > 1 for rows in hash_groups.values()),
        "protected_source_test_records": sum(r["source_split"] == "test" for r in records),
        "protected_test_link_groups": len(protected_groups),
        "known_group_crossings_in_output": 0,
        "train_counts": {name: 0 for name in CLASS_NAMES},
        "validation_counts": {name: 0 for name in CLASS_NAMES},
        "test_counts": {name: 0 for name in CLASS_NAMES},
        "final_split_created": False,
        "split_gate": "BLOCKED: BENIGN source-test upper bound 19; all 83 retained BENIGN have AI-supported HAM same-photo candidates, without independent adjudication",
        "source_evidence_sha256": {
            "proposed_exclusions": sha256(root / "analysis/nine_class_overlap_completion/proposed_binary_exclusions.csv"),
            "stage3i_edges": sha256(root / "analysis/nine_class_recovery/stage3i/proposed_overlap_edges.csv"),
            "stage3i_ai_review": sha256(root / "analysis/nine_class_recovery/stage3i/ai_pair_review.csv"),
        },
    }
    return records, summary


def guarded_group_split(rows: list[dict[str, str]], seed: int = 42) -> list[dict[str, str]]:
    """Create an exploratory train/validation assignment only if all nine classes qualify.

    The caller must supply adjudicated eligible rows with overlap_group and
    source_split. Protected source-test images are never assigned by this API.
    """
    import random

    if any(r.get("provisional_eligibility_status") != "APPROVED_ELIGIBLE" for r in rows):
        raise ValueError("Split input must have an explicit APPROVED_ELIGIBLE decision for every row")
    if any(r["source_split"] == "test" for r in rows):
        raise ValueError("Publisher source-test records require a separate approved protocol")
    counts = Counter(r["class_name"] for r in rows)
    if any(counts[name] < 2 for name in CLASS_NAMES):
        raise ValueError("All nine classes need at least two independently eligible examples")
    group_rows = defaultdict(list)
    for row in rows:
        group_rows[row["overlap_group"]].append(row)
    class_groups = defaultdict(set)
    for group_id, members in group_rows.items():
        for row in members:
            class_groups[row["class_name"]].add(group_id)
    if any(len(class_groups[name]) < 2 for name in CLASS_NAMES):
        raise ValueError("Each class needs at least two independent groups")
    rng = random.Random(seed)
    ordered = sorted(group_rows)
    rng.shuffle(ordered)
    val_groups = set()
    for name in CLASS_NAMES:
        candidates = [g for g in ordered if g in class_groups[name] and g not in val_groups]
        if len(candidates) > 1:
            val_groups.add(candidates[0])
    assigned = [dict(row, split="validation" if row["overlap_group"] in val_groups else "train") for row in rows]
    if any(not any(r["class_name"] == name and r["split"] == split for r in assigned)
           for name in CLASS_NAMES for split in ("train", "validation")):
        raise ValueError("Group constraints prevent nine-class train/validation coverage")
    return assigned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    records, summary = build_manifest(args.root)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = args.output / "nine_class_source_manifest.csv"
    audit = args.output / "split_eligibility_audit.json"
    if manifest.exists() or audit.exists():
        raise FileExistsError("Stage 4 output exists; refusing to overwrite")
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    audit.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
