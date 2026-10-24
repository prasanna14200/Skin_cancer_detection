"""External nine-label manifest, read-only overlap screen and approval gate."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from nine_class_protocol import file_sha256
from nine_class_similarity_audit import fingerprint
from nine_class_stage4 import CLASS_NAMES, ROOT

SCHEMA_VERSION = "nine_class_external_v1"
MANIFEST_FIELDS = (
    "source_dataset", "source_version", "image_path", "source_image_id",
    "patient_id", "lesion_id", "identifier_namespace", "original_clinical_label",
    "target_label", "mapping_status", "mapping_justification", "sha256",
    "source_license", "permitted_use_status", "overlap_status",
    "overlap_decision_reference", "eligibility_status",
)
MAPPING_STATUSES = {"EXACT", "CLINICALLY_JUSTIFIED_NONIDENTICAL", "UNSUPPORTED", "UNKNOWN"}
PHASH_DISTANCE = 6  # Stage 3 candidate retrieval setting, not identity proof.


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not set(MANIFEST_FIELDS) <= set(reader.fieldnames or ()):
            raise ValueError("External manifest schema incomplete")
        return list(reader)


def source_key(row: dict[str, str]) -> tuple[str, str, str]:
    return row["source_dataset"], row["source_version"], row["image_path"]


def validate_manifest_schema(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("External manifest empty")
    keys = [source_key(row) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate source-qualified external path")
    for row in rows:
        if not all(row.get(field, "").strip() for field in
                   ("source_dataset", "source_version", "image_path", "original_clinical_label", "sha256")):
            raise ValueError("External source, version, path, original label or hash missing")
        if row["mapping_status"] not in MAPPING_STATUSES:
            raise ValueError("Unknown mapping status")
        if row["target_label"] and row["target_label"] not in CLASS_NAMES:
            raise ValueError("Target outside fixed nine-class order")
        if row["eligibility_status"] not in ("UNREVIEWED", "QUARANTINED", "EXCLUDED", "APPROVED_EXTERNAL_EVALUATION"):
            raise ValueError("Unknown external eligibility status")
        relative = Path(row["image_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("External image path must be source-root relative")
        if len(row["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["sha256"].lower()):
            raise ValueError("Invalid external SHA-256")


def external_path(root: Path, row: dict[str, str]) -> Path:
    root = root.resolve()
    path = (root / row["image_path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Missing or escaping external image path: {row['image_path']}")
    return path


def _stage3_references(path: Path | None) -> dict[str, list[str]]:
    links = defaultdict(list)
    if path is None:
        return links
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for key in ("binary_image_path", "candidate_path"):
                if row.get(key):
                    links[row[key]].append(row.get("candidate_pair_id", ""))
    return links


def screen_external(external_root: Path, manifest: Path, internal_inventory: Path,
                    internal_fingerprints: Path, output_dir: Path,
                    *, stage3_evidence: Path | None = None) -> dict:
    """Retrieve candidates; never certify photographic or patient independence."""
    if output_dir.exists():
        raise FileExistsError(output_dir)
    rows = read_csv(manifest)
    validate_manifest_schema(rows)
    with internal_inventory.open(newline="", encoding="utf-8") as handle:
        internal = list(csv.DictReader(handle))
    with internal_fingerprints.open(newline="", encoding="utf-8") as handle:
        fingerprints = {r["image_path"]: r for r in csv.DictReader(handle)}
    if not internal or set(fingerprints) != {r["image_path"] for r in internal}:
        raise ValueError("Internal inventory and fingerprints do not cover the same paths")
    hashes = defaultdict(list)
    for item in internal:
        hashes[item["sha256"]].append(item)
    links = _stage3_references(stage3_evidence)
    summaries, candidates = [], []
    for row in rows:
        path = external_path(external_root, row)
        if file_sha256(path) != row["sha256"]:
            raise ValueError(f"External file hash differs from manifest: {source_key(row)}")
        phash, dhash = fingerprint(path)
        key = source_key(row)
        found = []
        for match in hashes.get(row["sha256"], []):
            found.append(("EXACT_SHA256", match, 0, 0))
        exact_paths = {match["image_path"] for _, match, _, _ in found}
        for match in internal:
            if match["image_path"] in exact_paths:
                continue
            fp = fingerprints[match["image_path"]]
            pd = (phash ^ int(fp["phash64"], 16)).bit_count()
            dd = (dhash ^ int(fp["dhash64"], 16)).bit_count()
            same_namespace = row["identifier_namespace"] and row["identifier_namespace"] == match["source_dataset"]
            identifier_match = bool(same_namespace and (
                (row["patient_id"] and row["patient_id"] == match["patient_id"]) or
                (row["lesion_id"] and row["lesion_id"] == match["lesion_id"])))
            if identifier_match:
                found.append(("VERIFIED_NAMESPACE_IDENTIFIER", match, pd, dd))
            elif min(pd, dd) <= PHASH_DISTANCE:
                found.append(("PERCEPTUAL_CANDIDATE", match, pd, dd))
        for kind, match, pd, dd in found:
            candidates.append({"external_source_dataset": key[0], "external_source_version": key[1],
                               "external_image_path": key[2], "internal_image_path": match["image_path"],
                               "match_type": kind, "phash_distance": pd, "dhash_distance": dd,
                               "stage3_pair_ids_for_internal_image": "|".join(sorted(set(links.get(match["image_path"], []))))})
        types = {item[0] for item in found}
        status = ("EXACT_HASH_OVERLAP" if "EXACT_SHA256" in types else
                  "IDENTIFIER_OVERLAP" if "VERIFIED_NAMESPACE_IDENTIFIER" in types else
                  "POSSIBLE_PHOTO_OVERLAP" if types else
                  "NO_CANDIDATE_FOUND_IDENTITY_UNKNOWN" if not row["patient_id"] and not row["lesion_id"] else
                  "NO_CANDIDATE_FOUND")
        summaries.append({"source_dataset": key[0], "source_version": key[1], "image_path": key[2],
                          "sha256": row["sha256"], "screen_status": status,
                          "candidate_count": len(found), "patient_independence_verified": False})
    output_dir.mkdir(parents=True, exist_ok=False)
    with (output_dir / "overlap_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ("external_source_dataset", "external_source_version", "external_image_path",
                  "internal_image_path", "match_type", "phash_distance", "dhash_distance",
                  "stage3_pair_ids_for_internal_image")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)
    report = {"schema_version": SCHEMA_VERSION, "status": "CANDIDATE_SCREEN_NOT_IDENTITY_CERTIFICATION",
              "external_manifest_sha256": file_sha256(manifest),
              "internal_inventory_sha256": file_sha256(internal_inventory),
              "internal_fingerprints_sha256": file_sha256(internal_fingerprints),
              "stage3_evidence_sha256": file_sha256(stage3_evidence) if stage3_evidence else None,
              "candidate_rule": "exact SHA-256 OR same verified identifier namespace OR pHash/dHash Hamming <=6",
              "screen_status_counts": dict(Counter(r["screen_status"] for r in summaries)),
              "rows": summaries}
    (output_dir / "overlap_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def validate_approved_external(external_root: Path, manifest: Path, approval_file: Path,
                               overlap_report_file: Path, internal_inventory: Path,
                               checkpoint_sha256: str, preprocess_config_sha256: str,
                               *, allow_synthetic_fixture: bool = False) -> tuple[list[dict[str, str]], dict]:
    for path in (manifest, approval_file, overlap_report_file, internal_inventory):
        if not path.is_file():
            raise FileNotFoundError(path)
    approval = json.loads(approval_file.read_text(encoding="utf-8"))
    if approval.get("synthetic_fixture") and not allow_synthetic_fixture:
        raise ValueError("Synthetic approval cannot authorize external evaluation")
    if approval.get("approval_status") != "APPROVED_EXTERNAL_EVALUATION" or approval.get("external_test_frozen") is not True:
        raise ValueError("Frozen external evaluation approval missing")
    required = ("approved_by", "approval_date_utc", "label_mapping_reference",
                "overlap_review_reference", "source_rights_reference",
                "preprocessing_protocol_reference", "unknown_identity_limitation_acknowledged")
    if any(not approval.get(key) for key in required):
        raise ValueError("External approval lacks source, mapping, overlap or limitation references")
    if approval.get("unknown_identity_limitation_acknowledged") is not True:
        raise ValueError("Unknown-identity limitation must be explicitly acknowledged")
    expected = {"approved_external_manifest_sha256": file_sha256(manifest),
                "overlap_report_sha256": file_sha256(overlap_report_file),
                "internal_inventory_sha256": file_sha256(internal_inventory),
                "checkpoint_sha256": checkpoint_sha256,
                "preprocess_config_sha256": preprocess_config_sha256}
    if any(approval.get(key) != value for key, value in expected.items()):
        raise ValueError("External approval provenance mismatch")
    report = json.loads(overlap_report_file.read_text(encoding="utf-8"))
    if report.get("external_manifest_sha256") != expected["approved_external_manifest_sha256"] or report.get("internal_inventory_sha256") != expected["internal_inventory_sha256"]:
        raise ValueError("Overlap screen and approved sources disagree")
    rows = read_csv(manifest)
    validate_manifest_schema(rows)
    screened = {source_key(r): r for r in report.get("rows", [])}
    if len(screened) != len(rows) or set(screened) != {source_key(r) for r in rows}:
        raise ValueError("Overlap screen lacks external images")
    eligible = []
    for row in rows:
        if row["eligibility_status"] != "APPROVED_EXTERNAL_EVALUATION":
            continue
        if row["mapping_status"] not in ("EXACT", "CLINICALLY_JUSTIFIED_NONIDENTICAL") or row["target_label"] not in CLASS_NAMES or not row["mapping_justification"]:
            raise ValueError("Unsupported or unjustified target mapping in evaluation")
        if row["permitted_use_status"] != "PERMITTED_FOR_RESEARCH_EVALUATION" or not row["source_license"]:
            raise ValueError("External image rights not approved")
        screen = screened[source_key(row)]
        if screen["sha256"] != row["sha256"]:
            raise ValueError("Overlap screen image hash mismatch")
        status = screen["screen_status"]
        if status in ("EXACT_HASH_OVERLAP", "IDENTIFIER_OVERLAP"):
            raise ValueError("Known internal/external overlap cannot be evaluated")
        if status == "POSSIBLE_PHOTO_OVERLAP":
            if row["overlap_status"] != "REVIEWED_DISTINCT" or not row["overlap_decision_reference"]:
                raise ValueError("Suspected photographic overlap requires independent adjudication")
        elif row["overlap_status"] != "NO_KNOWN_OVERLAP_AFTER_REVIEW":
            raise ValueError("External overlap status not reviewed")
        path = external_path(external_root, row)
        if file_sha256(path) != row["sha256"]:
            raise ValueError("External image bytes differ from approved manifest")
        eligible.append(row)
    if not eligible:
        raise ValueError("No approved external images")
    return eligible, {"approval": approval, "approval_sha256": file_sha256(approval_file),
                      "manifest_sha256": expected["approved_external_manifest_sha256"],
                      "overlap_report_sha256": expected["overlap_report_sha256"],
                      "internal_inventory_sha256": expected["internal_inventory_sha256"],
                      "supported_classes": [name for name in CLASS_NAMES if any(r["target_label"] == name for r in eligible)]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--internal-inventory", type=Path,
                        default=ROOT / "analysis/nine_class_stage4/nine_class_source_manifest.csv")
    parser.add_argument("--internal-fingerprints", type=Path,
                        default=ROOT / "analysis/nine_class_similarity/fingerprints.csv")
    parser.add_argument("--stage3-evidence", type=Path,
                        default=ROOT / "analysis/nine_class_recovery/stage3i/ai_pair_review.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = screen_external(args.external_root, args.manifest, args.internal_inventory,
                             args.internal_fingerprints, args.output_dir,
                             stage3_evidence=args.stage3_evidence)
    print(json.dumps({"status": report["status"],
                      "screen_status_counts": report["screen_status_counts"],
                      "output_dir": str(args.output_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
