"""Fail-closed launcher for approved Stage 6 training runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from nine_class_stage4 import CLASS_NAMES, ROOT

PARTITIONS = {
    "approved_training_record_ids": "train",
    "approved_validation_record_ids": "validation",
    "approved_calibration_record_ids": "calibration",
    "approved_test_record_ids": "test",
}
IDENTITY_FIELDS = (
    "record_id", "image_path", "sha256", "image_id", "lesion_id",
    "patient_id", "overlap_group",
)
RESOLVED_CHECKLIST_STATUSES = {"APPROVED", "CLOSED", "COMPLETE", "COMPLETED", "RESOLVED"}


class TrainingAuthorizationError(ValueError):
    """Raised when an approval or cohort authorization gate is incomplete."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TrainingAuthorizationError(f"Expected a JSON object: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise TrainingAuthorizationError(f"CSV has no header: {path}")
        return list(reader)


def _string_ids(config: dict, key: str, *, required: bool) -> list[str]:
    values = config.get(key)
    if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip()
                                           for value in values):
        raise TrainingAuthorizationError(f"{key} must be a list of non-empty strings")
    if len(set(values)) != len(values):
        raise TrainingAuthorizationError(f"{key} contains duplicate IDs")
    if required and not values:
        raise TrainingAuthorizationError(f"{key} is empty; training is blocked")
    return values


def validate_training_authorization(
    config: dict,
    checklist: dict,
    source_rows: list[dict[str, str]],
    decision_rows: list[dict[str, str]],
    split_rows: list[dict[str, str]],
    inventory_rows: list[dict[str, str]],
    approval: dict,
    hashes: dict[str, str],
) -> dict:
    """Validate source, researcher, approval, partition, and identity gates."""
    if config.get("authorization_schema_version") != "nine_class_training_authorization_v1":
        raise TrainingAuthorizationError("Unsupported training-authorization config schema")
    if tuple(config.get("label_order", ())) != CLASS_NAMES:
        raise TrainingAuthorizationError("Training authorization class mapping differs from EG-VAN")

    checklist_status = checklist.get("status")
    if checklist_status not in ("APPROVED", "APPROVED_FOR_TRAINING"):
        raise TrainingAuthorizationError(
            f"Approval checklist status is {checklist_status!r}; expected APPROVED"
        )
    approved_count = checklist.get("approved_eligible_images")
    if isinstance(approved_count, bool) or not isinstance(approved_count, int) or approved_count < 1:
        raise TrainingAuthorizationError("Approval checklist has zero approved eligible images")
    if checklist.get("approved_four_way_split") is not True:
        raise TrainingAuthorizationError("Approval checklist does not approve a four-way split")
    items = checklist.get("items")
    if not isinstance(items, list) or not items:
        raise TrainingAuthorizationError("Approval checklist has no review-gate items")
    unresolved = [item.get("id", "<unknown>") for item in items
                  if not isinstance(item, dict)
                  or item.get("status") not in RESOLVED_CHECKLIST_STATUSES]
    if unresolved:
        raise TrainingAuthorizationError(
            "Approval checklist has unresolved gates: " + ", ".join(unresolved)
        )

    permitted_sources = _string_ids(config, "permitted_source_ids", required=True)
    partition_ids = {
        key: _string_ids(config, key, required=True)
        for key in PARTITIONS
    }
    required_decisions = _string_ids(config, "required_decision_ids", required=True)
    pending_decisions = _string_ids(config, "pending_researcher_decisions", required=False)
    if pending_decisions:
        raise TrainingAuthorizationError(
            "Researcher decisions remain pending: " + ", ".join(pending_decisions)
        )

    source_required = {
        "source_id", "training_eligibility_status", "rights_status",
        "identity_review_status", "pending_researcher_decision_count", "evidence_reference",
    }
    if not source_rows or not source_required <= source_rows[0].keys():
        raise TrainingAuthorizationError("Source eligibility register schema is incomplete")
    sources = {}
    for row in source_rows:
        source_id = row["source_id"].strip()
        if not source_id or source_id in sources:
            raise TrainingAuthorizationError("Source eligibility register has a blank or duplicate source ID")
        sources[source_id] = row
    for source_id in permitted_sources:
        row = sources.get(source_id)
        if row is None:
            raise TrainingAuthorizationError(f"Permitted source lacks an eligibility record: {source_id}")
        try:
            pending_count = int(row["pending_researcher_decision_count"])
        except (TypeError, ValueError) as error:
            raise TrainingAuthorizationError(
                f"Invalid pending-decision count for source {source_id}"
            ) from error
        if (row["training_eligibility_status"] != "APPROVED_FOR_TRAINING"
                or row["rights_status"] != "VERIFIED"
                or row["identity_review_status"] != "VERIFIED"
                or pending_count != 0
                or not row["evidence_reference"].strip()):
            raise TrainingAuthorizationError(
                f"Source eligibility is unresolved for {source_id}"
            )

    decision_required = {"decision_id", "decision_status", "decision_outcome", "evidence_reference"}
    if not decision_rows or not decision_required <= decision_rows[0].keys():
        raise TrainingAuthorizationError("Researcher decision register schema is incomplete")
    decisions = {}
    for row in decision_rows:
        decision_id = row["decision_id"].strip()
        if not decision_id or decision_id in decisions:
            raise TrainingAuthorizationError("Decision register has a blank or duplicate decision ID")
        decisions[decision_id] = row
    missing_decisions = sorted(set(required_decisions) - decisions.keys())
    if missing_decisions:
        raise TrainingAuthorizationError(
            "Required researcher decisions are absent: " + ", ".join(missing_decisions)
        )
    unresolved_decisions = sorted(
        decision_id for decision_id in required_decisions
        if decisions[decision_id]["decision_status"] != "RESOLVED"
        or not decisions[decision_id]["decision_outcome"].strip()
        or not decisions[decision_id]["evidence_reference"].strip()
    )
    if unresolved_decisions:
        raise TrainingAuthorizationError(
            "Required researcher decisions remain unresolved: " + ", ".join(unresolved_decisions)
        )

    expected_ids = {partition: set(partition_ids[key]) for key, partition in PARTITIONS.items()}
    if any(expected_ids[a] & expected_ids[b] for a, b in (
        ("train", "validation"), ("train", "calibration"), ("train", "test"),
        ("validation", "calibration"), ("validation", "test"), ("calibration", "test"),
    )):
        raise TrainingAuthorizationError("Configured partition record IDs overlap")

    split_required = {
        "record_id", "source_dataset", "image_path", "sha256", "image_id", "lesion_id",
        "patient_id", "overlap_group", "split", "provisional_eligibility_status",
    }
    if not split_rows or not split_required <= split_rows[0].keys():
        raise TrainingAuthorizationError("Approved split schema lacks required IDs or status fields")
    if not inventory_rows or not {"record_id", "source_dataset", "image_path"} <= inventory_rows[0].keys():
        raise TrainingAuthorizationError("Approved source inventory lacks record IDs")

    inventory = {}
    for row in inventory_rows:
        record_id = row["record_id"].strip()
        if not record_id or record_id in inventory:
            raise TrainingAuthorizationError("Source inventory has a blank or duplicate record ID")
        inventory[record_id] = row

    seen = set()
    observed_by_partition = {partition: set() for partition in PARTITIONS.values()}
    identity_partitions: dict[tuple[str, str], set[str]] = {}
    sources_used = set()
    for row in split_rows:
        record_id = row["record_id"].strip()
        partition = row["split"]
        if not record_id or record_id in seen:
            raise TrainingAuthorizationError("Approved split has a blank or duplicate record ID")
        if partition not in observed_by_partition:
            raise TrainingAuthorizationError(f"Unknown approved partition: {partition}")
        if row["provisional_eligibility_status"] != "APPROVED_ELIGIBLE":
            raise TrainingAuthorizationError(f"Record is not approved eligible: {record_id}")
        source_id = row["source_dataset"].strip()
        if source_id not in permitted_sources:
            raise TrainingAuthorizationError(f"Record uses an unapproved source: {source_id}")
        inventory_row = inventory.get(record_id)
        if (inventory_row is None or inventory_row["source_dataset"] != source_id
                or inventory_row["image_path"] != row["image_path"]):
            raise TrainingAuthorizationError(f"Record is not bound to the approved inventory: {record_id}")
        seen.add(record_id)
        observed_by_partition[partition].add(record_id)
        sources_used.add(source_id)
        for field in IDENTITY_FIELDS:
            value = row.get(field, "").strip()
            if value:
                identity_partitions.setdefault((field, value), set()).add(partition)

    for partition, ids in expected_ids.items():
        if observed_by_partition[partition] != ids:
            raise TrainingAuthorizationError(
                f"Approved {partition} records differ from the authorization config"
            )
    if sources_used != set(permitted_sources):
        raise TrainingAuthorizationError("Permitted source IDs differ from sources in the approved split")
    crossing = [f"{field}={value}" for (field, value), partitions in identity_partitions.items()
                if len(partitions) > 1]
    if crossing:
        raise TrainingAuthorizationError(
            "Training/validation/calibration/test identity overlap: " + ", ".join(crossing[:8])
        )
    all_ids = set().union(*expected_ids.values())
    if approved_count != len(all_ids):
        raise TrainingAuthorizationError(
            "Checklist approved image count differs from the partition record count"
        )

    if approval.get("approval_status") != "APPROVED_BY_RESEARCHER":
        raise TrainingAuthorizationError("Researcher approval record is missing")
    if set(approval.get("approved_source_ids", [])) != set(permitted_sources):
        raise TrainingAuthorizationError("Approval record source IDs differ from permitted sources")
    if set(approval.get("approved_record_ids", [])) != all_ids:
        raise TrainingAuthorizationError("Approval record IDs differ from approved partitions")
    for field in (
        "authorization_config_sha256", "approval_checklist_sha256",
        "approved_split_sha256", "source_inventory_sha256",
        "source_eligibility_sha256", "researcher_decision_register_sha256",
    ):
        if not hashes.get(field) or approval.get(field) != hashes[field]:
            raise TrainingAuthorizationError(f"Approval evidence hash mismatch: {field}")
    return {
        "status": "AUTHORIZED_INPUTS_VALIDATED",
        "approved_records": len(all_ids),
        "permitted_source_ids": sorted(permitted_sources),
        "partition_counts": {partition: len(ids) for partition, ids in observed_by_partition.items()},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, required=True,
                        help="Researcher-reviewed Stage 6 config plus authorization fields")
    parser.add_argument("--approval-checklist", type=Path, required=True)
    parser.add_argument("--source-eligibility-register", type=Path, required=True)
    parser.add_argument("--decision-register", type=Path, required=True)
    parser.add_argument("--approved-split", type=Path, required=True)
    parser.add_argument("--approval-record", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--launch", action="store_true",
                        help="Start Stage 6 only after all authorization checks pass")
    args = parser.parse_args(argv)
    try:
        config = read_json(args.config)
        checklist = read_json(args.approval_checklist)
        approval = read_json(args.approval_record)
        source_rows = read_csv(args.source_eligibility_register)
        decision_rows = read_csv(args.decision_register)
        split_rows = read_csv(args.approved_split)
        inventory_rows = read_csv(args.inventory)
        hashes = {
            "authorization_config_sha256": file_sha256(args.config),
            "approval_checklist_sha256": file_sha256(args.approval_checklist),
            "approved_split_sha256": file_sha256(args.approved_split),
            "source_inventory_sha256": file_sha256(args.inventory),
            "source_eligibility_sha256": file_sha256(args.source_eligibility_register),
            "researcher_decision_register_sha256": file_sha256(args.decision_register),
        }
        result = validate_training_authorization(
            config, checklist, source_rows, decision_rows, split_rows,
            inventory_rows, approval, hashes,
        )
    except (TrainingAuthorizationError, OSError, csv.Error, json.JSONDecodeError) as error:
        print(f"TRAINING AUTHORIZATION BLOCKED: {error}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    if not args.launch:
        print("Training not started; rerun with --launch only after review.")
        return 0
    command = [
        sys.executable, str(args.root / "src/nine_class_training.py"),
        "--root", str(args.root), "--config", str(args.config),
        "--approved-split", str(args.approved_split),
        "--approval", str(args.approval_record),
        "--inventory", str(args.inventory), "--runs-root", str(args.runs_root),
    ]
    if args.resume is not None:
        command.extend(("--resume", str(args.resume)))
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
