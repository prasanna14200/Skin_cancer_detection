#!/usr/bin/env python3
"""Stage 3 image-overlap evidence review. Never changes source images or audit CSVs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FINGERPRINTS = Path("analysis/nine_class_similarity/fingerprints.csv")
CANDIDATES = Path("analysis/nine_class_similarity/candidates.csv")
HAM_METADATA = Path("data/raw/HAM10000_metadata.csv")
OUTPUT = Path("analysis/nine_class_overlap_review")
FINGERPRINT_FIELDS = ("image_path", "phash64", "dhash64")
CANDIDATE_FIELDS = ("path_a", "path_b", "scope", "phash_distance", "dhash_distance")
LABEL_ORDER = ("akiec", "bcc", "bkl", "df", "mel", "nv", "vasc", "benign", "malignant")

# Inclusive thresholds. p/d <= 6 on both hashes is a priority queue, not a
# duplicate decision. Pixel confirmation also requires direct decoded-image
# evidence at a common 224x224 size. Thresholds are recorded in the summary.
PRIORITY_HASH_DISTANCE = 6
PIXEL_MAX_MAE = 2.0  # 8-bit RGB units, out of 255
PIXEL_MIN_CORRELATION = 0.999

# Direct visual comparison in this audit, independently backed by p/d and
# pixel metrics. These are assistant visual reviews, never human adjudications.
VISUAL_PAIRS = {
    frozenset(("data/isic/data/test/benign/1003.jpg", "data/raw/HAM10000_images_part_1/ISIC_0028716.jpg")),
    frozenset(("data/isic/data/test/malignant/1003.jpg", "data/raw/HAM10000_images_part_1/ISIC_0026847.jpg")),
    frozenset(("data/isic/data/test/benign/335.jpg", "data/isic/data/train/benign/1593.jpg")),
    frozenset(("data/isic/data/test/malignant/507.jpg", "data/isic/data/train/malignant/439.jpg")),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def source_record(path: str, ham: dict[str, dict]) -> dict[str, str]:
    parts = Path(path).parts
    if len(parts) == 4 and parts[:2] == ("data", "raw") and parts[2] in (
        "HAM10000_images_part_1", "HAM10000_images_part_2"
    ) and parts[3].startswith("ISIC_") and parts[3].endswith(".jpg"):
        image_id = Path(path).stem
        if image_id not in ham:
            raise ValueError(f"HAM image not in metadata: {path}")
        return {"path": path, "source": "HAM10000", "label": ham[image_id]["dx"],
                "source_split": "", "image_id": image_id,
                "lesion_id": ham[image_id]["lesion_id"]}
    if len(parts) == 5 and parts[:3] == ("data", "isic", "data") and parts[3] in ("train", "test"):
        # Binary paths have six components, including their label directory.
        raise ValueError(f"Malformed binary path: {path}")
    if len(parts) == 6 and parts[:3] == ("data", "isic", "data") and parts[3] in ("train", "test") and parts[4] in ("benign", "malignant") and parts[5].endswith(".jpg"):
        return {"path": path, "source": "binary", "label": parts[4],
                "source_split": parts[3], "image_id": "", "lesion_id": ""}
    raise ValueError(f"Unexpected or unsafe source path: {path}")


def read_inputs(root: Path) -> tuple[dict[str, dict], list[dict], dict[str, dict], dict]:
    with (root / HAM_METADATA).open(newline="", encoding="utf-8") as handle:
        ham_rows = list(csv.DictReader(handle))
    ham = {row["image_id"]: row for row in ham_rows}
    if len(ham) != len(ham_rows):
        raise ValueError("Repeated HAM metadata image_id")
    with (root / FINGERPRINTS).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FINGERPRINT_FIELDS:
            raise ValueError("Unexpected fingerprint schema")
        fingerprint_rows = list(reader)
    records: dict[str, dict] = {}
    for row in fingerprint_rows:
        path = row["image_path"]
        if path in records or any(not row.get(key) for key in FINGERPRINT_FIELDS):
            raise ValueError(f"Duplicate/incomplete fingerprint: {path}")
        for key in ("phash64", "dhash64"):
            if len(row[key]) != 16 or any(ch not in "0123456789abcdef" for ch in row[key]):
                raise ValueError(f"Malformed {key}: {path}")
        info = source_record(path, ham)
        if info["label"] not in LABEL_ORDER or not (root / path).is_file():
            raise ValueError(f"Unknown label or missing image: {path}")
        records[path] = {**info, **row}
    with (root / CANDIDATES).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CANDIDATE_FIELDS:
            raise ValueError("Unexpected candidate schema")
        candidates = list(reader)
    seen = set()
    for row in candidates:
        a, b = row["path_a"], row["path_b"]
        if not a or not b or a == b or a not in records or b not in records:
            raise ValueError(f"Invalid candidate paths: {a}, {b}")
        pair = tuple(sorted((a, b)))
        if pair in seen:
            raise ValueError(f"Repeated candidate pair: {pair}")
        seen.add(pair)
        expected_scope = "binary_ham" if records[b]["source"] == "HAM10000" else "binary_binary"
        if records[a]["source"] != "binary" or row["scope"] != expected_scope:
            raise ValueError(f"Invalid source scope: {pair}")
        for kind, key in (("phash64", "phash_distance"), ("dhash64", "dhash_distance")):
            try:
                distance = int(row[key])
            except (TypeError, ValueError):
                raise ValueError(f"Invalid {key}: {pair}") from None
            actual = (int(records[a][kind], 16) ^ int(records[b][kind], 16)).bit_count()
            if distance != actual or not 0 <= distance <= 64:
                raise ValueError(f"Fingerprint distance mismatch: {pair}")
    stats = {
        "fingerprint_rows": len(records), "candidate_rows": len(candidates),
        "source_counts": dict(Counter(r["source"] for r in records.values())),
        "candidate_scopes": dict(Counter(r["scope"] for r in candidates)),
    }
    return records, candidates, ham, stats


@lru_cache(maxsize=96)
def decoded(path: str, root_text: str) -> np.ndarray:
    image = cv2.imread(str(Path(root_text) / path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot decode image: {path}")
    return image


def pixel_evidence(root: Path, a: str, b: str) -> dict:
    left = decoded(a, str(root))
    right = decoded(b, str(root))
    left_size = f"{left.shape[1]}x{left.shape[0]}"
    right_size = f"{right.shape[1]}x{right.shape[0]}"
    # Candidate path_a is always binary. Preserve its native resolution and
    # resize the HAM or other binary view only for the comparison.
    if right.shape[:2] != left.shape[:2]:
        right = cv2.resize(right, (left.shape[1], left.shape[0]), interpolation=cv2.INTER_AREA)
    x, y = left.astype(np.float32), right.astype(np.float32)
    mae = float(np.mean(np.abs(x - y)))
    correlation = float(np.corrcoef(x.ravel(), y.ravel())[0, 1])
    if not np.isfinite(correlation):
        correlation = 0.0
    return {"size_a": left_size, "size_b": right_size,
            "pixel_mae": round(mae, 6), "pixel_correlation": round(correlation, 8)}


def decision_for_pair(row: dict, sha_a: str, sha_b: str, pixels: dict) -> tuple[str, str]:
    if sha_a == sha_b:
        return "confirmed_exact_sha256", "byte_identity"
    if frozenset((row["path_a"], row["path_b"])) in VISUAL_PAIRS:
        if pixels["pixel_correlation"] < 0.995:
            raise ValueError("Visual review pair failed pixel sanity check")
        return "confirmed_visual_assistant", "visual_inspection_and_pixel_evidence"
    if (pixels["pixel_mae"] <= PIXEL_MAX_MAE and
            pixels["pixel_correlation"] >= PIXEL_MIN_CORRELATION):
        return "confirmed_direct_pixel_automated", "strict_pixel_evidence"
    return "unresolved_human_review", "candidate_only"


def duplicate_groups(paths: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    parent = {p: p for p in paths}

    def find(p: str) -> str:
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    for a, b in edges:
        if a not in parent or b not in parent:
            raise ValueError("Unknown duplicate-group member")
        x, y = find(a), find(b)
        if x != y:
            parent[max(x, y)] = min(x, y)
    buckets: dict[str, list[str]] = defaultdict(list)
    for p in paths:
        buckets[find(p)].append(p)
    return sorted((sorted(v) for v in buckets.values() if len(v) > 1), key=lambda v: v[0])


def exclusion_reasons(group: list[str], records: dict[str, dict]) -> dict[str, str]:
    """Only confirmed groups enter here. Conflicting binary labels are held."""
    binary = sorted(p for p in group if records[p]["source"] == "binary")
    if not binary:
        return {}
    ham = [p for p in group if records[p]["source"] == "HAM10000"]
    if ham:
        return {p: "same_photograph_as_HAM" for p in binary}
    if len({records[p]["label"] for p in binary}) > 1:
        return {}
    test = [p for p in binary if records[p]["source_split"] == "test"]
    retained = min(test or binary)
    return {p: "binary_duplicate_keep_source_test" if test else "binary_duplicate_keep_lexical"
            for p in binary if p != retained}


def render(root: Path, output: Path, replace_existing: bool = False) -> dict:
    root = root.resolve()
    output = output.resolve()
    if output == (root / FINGERPRINTS).resolve().parent or output == root:
        raise ValueError("Review output must not overwrite original audit files")
    expected_outputs = {
        "review_decisions.csv", "confirmed_duplicate_groups.csv",
        "proposed_binary_exclusions.csv", "unresolved_priority_pairs.csv",
        "source_test_boundary_conflicts.csv", "binary_eligibility_review.csv",
        "review_summary.json", "REVIEW_SUMMARY.md",
    }
    if output.exists() and any(output.iterdir()):
        existing = {p.name for p in output.iterdir()}
        if not replace_existing or existing != expected_outputs:
            raise FileExistsError(f"Review output is not empty or has unexpected files: {output}")
    records, candidates, ham, input_stats = read_inputs(root)
    paths = sorted(records)
    hashes = {path: sha256(root / path) for path in paths}
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for path, value in hashes.items():
        hash_groups[value].append(path)
    exact_groups = [sorted(v) for v in hash_groups.values() if len(v) > 1]
    exact_edges = [(v[0], p) for v in exact_groups for p in v[1:]]
    reviewed = []
    confirmed_edges = list(exact_edges)
    pair_lookup: dict[frozenset[str], dict] = {}
    priority = [r for r in candidates if max(int(r["phash_distance"]), int(r["dhash_distance"])) <= PRIORITY_HASH_DISTANCE]
    for candidate in priority:
        a, b = candidate["path_a"], candidate["path_b"]
        pixels = pixel_evidence(root, a, b)
        status, method = decision_for_pair(candidate, hashes[a], hashes[b], pixels)
        if status.startswith("confirmed"):
            confirmed_edges.append((a, b))
        row = {**candidate, "label_a": records[a]["label"], "label_b": records[b]["label"],
               "source_split_a": records[a]["source_split"], "source_split_b": records[b]["source_split"],
               "sha256_a": hashes[a], "sha256_b": hashes[b], **pixels,
               "nine_class_target_conflict": int(records[a]["label"] != records[b]["label"]),
               "decision": status, "decision_method": method,
               "human_review_status": "not_human_reviewed"}
        reviewed.append(row)
        pair_lookup[frozenset((a, b))] = row
    groups = duplicate_groups(paths, confirmed_edges)
    group_id = {}
    for group in groups:
        digest = hashlib.sha256("\n".join(group).encode()).hexdigest()[:16]
        for path in group:
            group_id[path] = f"DG-{digest}"
    group_rows = []
    exclusions: dict[str, dict] = {}
    conflicts = []
    for group in groups:
        gid = group_id[group[0]]
        labels = {records[p]["label"] for p in group}
        binary_labels = {records[p]["label"] for p in group if records[p]["source"] == "binary"}
        binary_splits = {records[p]["source_split"] for p in group if records[p]["source"] == "binary"}
        matching_ham = sorted(p for p in group if records[p]["source"] == "HAM10000")
        reasons = exclusion_reasons(group, records)
        for path in group:
            info = records[path]
            group_rows.append({"duplicate_group": gid, "image_path": path, "source_dataset": info["source"],
                               "original_label": info["label"], "source_split": info["source_split"],
                               "sha256": hashes[path], "ham_lesion_id_if_verified": info["lesion_id"],
                               "group_size": len(group), "nine_class_target_conflict": int(len(labels) > 1)})
        for path, reason in reasons.items():
            other = matching_ham if matching_ham else sorted(p for p in group if p != path)
            evidence_rows = [pair_lookup[frozenset((path, p))] for p in other
                             if frozenset((path, p)) in pair_lookup and
                             pair_lookup[frozenset((path, p))]["decision"].startswith("confirmed")]
            evidence = min(evidence_rows, key=lambda r: (r["pixel_mae"], r["path_b"])) if evidence_rows else None
            matching_path = (evidence["path_b"] if evidence and evidence["path_a"] == path
                             else evidence["path_a"] if evidence else other[0])
            exclusions[path] = {"image_path": path, "source_dataset": "binary",
                                "original_label": records[path]["label"],
                                "source_split": records[path]["source_split"],
                                "duplicate_group": gid, "reason": reason,
                                "matching_image_path": matching_path,
                                "matching_image_sha256": hashes[matching_path], "sha256": hashes[path],
                                "decision_method": evidence["decision_method"] if evidence else "byte_identity",
                                "review_status": evidence["decision"] if evidence else "confirmed_exact_sha256"}
        if len(binary_labels) > 1 or binary_splits == {"train", "test"}:
            conflicts.append({"duplicate_group": gid, "conflict_type": "binary_label_conflict" if len(binary_labels) > 1 else "binary_train_test",
                              "binary_paths": ";".join(sorted(p for p in group if records[p]["source"] == "binary")),
                              "ham_paths": ";".join(matching_ham),
                              "recommended_action": ("quarantine" if len(binary_labels) > 1 else
                                                     "exclude_binary_keep_HAM" if matching_ham else
                                                     "keep_test_exclude_train")})
    # A binary source-test image confirmed to be a HAM photograph is an
    # independent boundary issue even when no binary train image shares it.
    for path in sorted(group_id):
        if records[path]["source"] == "binary" and records[path]["source_split"] == "test":
            related_ham = sorted(p for p in next(g for g in groups if path in g) if records[p]["source"] == "HAM10000")
            if related_ham:
                conflicts.append({"duplicate_group": group_id[path], "conflict_type": "binary_test_HAM",
                                  "binary_paths": path, "ham_paths": ";".join(related_ham),
                                  "recommended_action": "exclude_binary_if_confirmed_keep_HAM"})
    unresolved = sorted((r for r in reviewed if r["decision"] == "unresolved_human_review"),
                        key=lambda r: (max(int(r["phash_distance"]), int(r["dhash_distance"])),
                                       int(r["phash_distance"]) + int(r["dhash_distance"]),
                                       -float(r["pixel_correlation"]), float(r["pixel_mae"]),
                                       r["path_a"], r["path_b"]))
    for rank, row in enumerate(unresolved, 1):
        row["review_priority_rank"] = rank
    unresolved_paths = {r["path_a"] for r in unresolved} | {r["path_b"] for r in unresolved if records[r["path_b"]]["source"] == "binary"}
    broad_unscored_binary = {r["path_a"] for r in candidates if max(int(r["phash_distance"]), int(r["dhash_distance"])) > PRIORITY_HASH_DISTANCE}
    binary_rows = []
    for path in paths:
        info = records[path]
        if info["source"] != "binary":
            continue
        state = ("proposed_exclude_confirmed" if path in exclusions else
                 "unresolved_priority_candidate" if path in unresolved_paths else
                 "unreviewed_broad_candidate" if path in broad_unscored_binary else
                 "potentially_eligible")
        binary_rows.append({"image_path": path, "source_split": info["source_split"],
                            "original_label": info["label"], "sha256": hashes[path],
                            "duplicate_group": group_id.get(path, ""),
                            "eligibility_status": state,
                            "exclusion_reason": exclusions.get(path, {}).get("reason", "")})
    counts = {
        **input_stats, "exact_sha256_groups": len(exact_groups),
        "exact_sha256_group_members": sum(map(len, exact_groups)),
        "exact_cross_source_groups": sum(any(records[p]["source"] == "HAM10000" for p in g) and any(records[p]["source"] == "binary" for p in g) for g in exact_groups),
        "strong_phash_dhash_zero_cross_source_pairs": sum(r["scope"] == "binary_ham" and r["phash_distance"] == "0" and r["dhash_distance"] == "0" for r in candidates),
        "strong_phash_dhash_zero_binary_pairs": sum(r["scope"] == "binary_binary" and r["phash_distance"] == "0" and r["dhash_distance"] == "0" for r in candidates),
        "priority_pairs_scored": len(reviewed), "confirmed_pairs_by_status": dict(Counter(r["decision"] for r in reviewed if r["decision"].startswith("confirmed"))),
        "confirmed_cross_source_pairs": sum(r["scope"] == "binary_ham" and r["decision"].startswith("confirmed") for r in reviewed),
        "confirmed_binary_pairs": sum(r["scope"] == "binary_binary" and r["decision"].startswith("confirmed") for r in reviewed),
        "unresolved_priority_pairs": len(unresolved), "broad_candidates_not_pixel_scored": len(candidates) - len(priority),
        "confirmed_duplicate_groups": len(groups), "proposed_binary_exclusions": len(exclusions),
        "binary_records_not_proposed_for_exclusion": len(binary_rows) - len(exclusions),
        "binary_eligibility_states": dict(Counter(r["eligibility_status"] for r in binary_rows)),
        "source_test_conflict_rows": len(conflicts),
    }
    output.mkdir(parents=True, exist_ok=replace_existing)
    decision_columns = (*CANDIDATE_FIELDS, "label_a", "label_b", "source_split_a", "source_split_b",
                        "sha256_a", "sha256_b", "size_a", "size_b", "pixel_mae", "pixel_correlation",
                        "nine_class_target_conflict", "decision", "decision_method", "human_review_status")
    write_csv(output / "review_decisions.csv", decision_columns, reviewed)
    write_csv(output / "confirmed_duplicate_groups.csv",
              ("duplicate_group", "image_path", "source_dataset", "original_label", "source_split",
               "sha256", "ham_lesion_id_if_verified", "group_size", "nine_class_target_conflict"), group_rows)
    write_csv(output / "proposed_binary_exclusions.csv",
              ("image_path", "source_dataset", "original_label", "source_split", "duplicate_group",
               "reason", "matching_image_path", "matching_image_sha256", "sha256",
               "decision_method", "review_status"), [exclusions[p] for p in sorted(exclusions)])
    write_csv(output / "unresolved_priority_pairs.csv",
              ("review_priority_rank", *decision_columns), unresolved)
    write_csv(output / "source_test_boundary_conflicts.csv",
              ("duplicate_group", "conflict_type", "binary_paths", "ham_paths", "recommended_action"), sorted(conflicts, key=lambda r: (r["conflict_type"], r["binary_paths"])))
    write_csv(output / "binary_eligibility_review.csv",
              ("image_path", "source_split", "original_label", "sha256", "duplicate_group",
               "eligibility_status", "exclusion_reason"), binary_rows)
    summary = {
        "stage": "overlap_review_not_final_manifest",
        "method": {
            "priority_pair_rule": "both 64-bit pHash and dHash Hamming distance <= 6",
            "direct_pixel_confirmation": "after resizing path_b to binary path_a dimensions with OpenCV INTER_AREA: RGB/BGR-equivalent MAE <= 2/255 and Pearson correlation >= 0.999",
            "visual_review": "four explicitly listed pairs inspected by assistant; no human adjudication claimed",
            "limitations": "non-priority candidate pairs are unscored; perceptual search can miss crops/transformations; binary patient/lesion IDs absent",
            "thresholds": {"priority_hash_distance": PRIORITY_HASH_DISTANCE, "max_mae_8bit": PIXEL_MAX_MAE,
                           "min_pixel_correlation": PIXEL_MIN_CORRELATION},
        },
        "input_sha256": {str(FINGERPRINTS): sha256(root / FINGERPRINTS),
                         str(CANDIDATES): sha256(root / CANDIDATES),
                         str(HAM_METADATA): sha256(root / HAM_METADATA)},
        "counts": counts,
    }
    (output / "review_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "REVIEW_SUMMARY.md").write_text(
        "# Nine-class overlap review — Stage 3\n\n"
        "All paths and original labels are source-derived. This is an eligibility review, not a final dataset manifest or split.\n\n"
        f"Inputs: {len(records):,} images; {len(candidates):,} candidate pairs. SHA-256 exact groups: {len(exact_groups):,}; cross-source exact groups: {counts['exact_cross_source_groups']}.\n\n"
        f"Pixel-scored priority pairs: {len(reviewed):,}; confirmed cross-source pairs: {counts['confirmed_cross_source_pairs']:,}; confirmed binary pairs: {counts['confirmed_binary_pairs']:,}; unresolved priority pairs: {len(unresolved):,}.\n\n"
        f"Proposed binary exclusions: {len(exclusions):,}. Binary records not proposed for exclusion: {len(binary_rows)-len(exclusions):,}; this is only a provisional upper bound, not the final eligible count. Potential combined source-entry upper bound: {len(records)-len(exclusions):,}.\n\n"
        f"Broad candidates not pixel-scored: {counts['broad_candidates_not_pixel_scored']:,}; they remain unadjudicated, and no patient independence can be claimed. Source-test conflicts: {len(conflicts):,} rows.\n\n"
        "Confirmed statuses distinguish SHA byte identity, strict direct pixel evidence produced automatically, and four assistant visual inspections. No row is marked human-reviewed. Unresolved pairs are candidates only; the broad unscored set remains in the original candidate CSV without copying it.\n\n"
        "Do not build a nine-class manifest or split until unresolved high-risk pairs and provenance/label issues are reviewed. Keep the canonical binary source-test boundary intact.\n",
        encoding="utf-8")
    summary["output_sha256"] = {p.name: sha256(p) for p in sorted(output.iterdir())}
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replace-review-output", action="store_true",
                        help="Replace only this tool's eight generated files; original audit CSVs remain protected")
    args = parser.parse_args()
    result = render(args.root, args.output or args.root / OUTPUT, args.replace_review_output)
    print(json.dumps(result["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
