import csv
import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nine_class_authorized_training import (  # noqa: E402
    TrainingAuthorizationError,
    validate_training_authorization,
)
from nine_class_stage4 import CLASS_NAMES  # noqa: E402
from nine_class_training import DEFAULT_CONFIG, main as stage6_main  # noqa: E402


def authorization_fixture():
    partitions = ("train", "validation", "calibration", "test")
    config = {
        "authorization_schema_version": "nine_class_training_authorization_v1",
        "label_order": list(CLASS_NAMES),
        "permitted_source_ids": ["HAM10000"],
        "approved_training_record_ids": ["record-train"],
        "approved_validation_record_ids": ["record-validation"],
        "approved_calibration_record_ids": ["record-calibration"],
        "approved_test_record_ids": ["record-test"],
        "required_decision_ids": ["decision-1"],
        "pending_researcher_decisions": [],
    }
    checklist = {
        "status": "APPROVED",
        "approved_eligible_images": 4,
        "approved_four_way_split": True,
        "items": [{"id": "gate-1", "status": "COMPLETE"}],
    }
    source_rows = [{
        "source_id": "HAM10000",
        "training_eligibility_status": "APPROVED_FOR_TRAINING",
        "rights_status": "VERIFIED",
        "identity_review_status": "VERIFIED",
        "pending_researcher_decision_count": "0",
        "evidence_reference": "approved-source-register",
    }]
    decision_rows = [{
        "decision_id": "decision-1",
        "decision_status": "RESOLVED",
        "decision_outcome": "approved-for-synthetic-fixture",
        "evidence_reference": "synthetic-only",
    }]
    split_rows, inventory_rows = [], []
    for index, partition in enumerate(partitions):
        record_id = f"record-{partition}"
        row = {
            "record_id": record_id,
            "source_dataset": "HAM10000",
            "image_path": f"images/{record_id}.jpg",
            "sha256": f"sha-{index}",
            "image_id": f"image-{index}",
            "lesion_id": f"lesion-{index}",
            "patient_id": f"patient-{index}",
            "overlap_group": f"group-{index}",
            "split": partition,
            "provisional_eligibility_status": "APPROVED_ELIGIBLE",
        }
        split_rows.append(row)
        inventory_rows.append({
            "record_id": record_id,
            "source_dataset": "HAM10000",
            "image_path": row["image_path"],
        })
    hashes = {
        "authorization_config_sha256": "config-hash",
        "approval_checklist_sha256": "checklist-hash",
        "approved_split_sha256": "split-hash",
        "source_inventory_sha256": "inventory-hash",
        "source_eligibility_sha256": "source-hash",
        "researcher_decision_register_sha256": "decisions-hash",
    }
    approval = {
        "approval_status": "APPROVED_BY_RESEARCHER",
        "approved_source_ids": ["HAM10000"],
        "approved_record_ids": [row["record_id"] for row in split_rows],
        **hashes,
    }
    return config, checklist, source_rows, decision_rows, split_rows, inventory_rows, approval, hashes


class AuthorizedTrainingGateTests(unittest.TestCase):
    def test_complete_synthetic_authorization_fixture_passes_validation_only(self):
        fixture = authorization_fixture()
        result = validate_training_authorization(*fixture)
        self.assertEqual(result["status"], "AUTHORIZED_INPUTS_VALIDATED")
        self.assertEqual(result["approved_records"], 4)
        self.assertEqual(result["partition_counts"], {
            "train": 1, "validation": 1, "calibration": 1, "test": 1,
        })

    def test_not_approved_checklist_fails_first(self):
        fixture = list(authorization_fixture())
        fixture[1]["status"] = "NOT_APPROVED"
        fixture[1]["approved_eligible_images"] = 0
        fixture[1]["approved_four_way_split"] = False
        with self.assertRaisesRegex(TrainingAuthorizationError, "checklist status"):
            validate_training_authorization(*fixture)

    def test_zero_approved_count_and_unapproved_split_are_rejected(self):
        fixture = list(authorization_fixture())
        fixture[1]["approved_eligible_images"] = 0
        with self.assertRaisesRegex(TrainingAuthorizationError, "zero approved eligible images"):
            validate_training_authorization(*fixture)

        fixture = list(authorization_fixture())
        fixture[1]["approved_four_way_split"] = False
        with self.assertRaisesRegex(TrainingAuthorizationError, "does not approve a four-way split"):
            validate_training_authorization(*fixture)

    def test_empty_source_and_partition_authorization_is_rejected(self):
        fixture = list(authorization_fixture())
        fixture[0]["permitted_source_ids"] = []
        with self.assertRaisesRegex(TrainingAuthorizationError, "permitted_source_ids is empty"):
            validate_training_authorization(*fixture)

    def test_each_approved_partition_requires_record_ids(self):
        for key in (
            "approved_training_record_ids",
            "approved_validation_record_ids",
            "approved_calibration_record_ids",
            "approved_test_record_ids",
        ):
            with self.subTest(key=key):
                fixture = list(authorization_fixture())
                fixture[0][key] = []
                with self.assertRaisesRegex(TrainingAuthorizationError, f"{key} is empty"):
                    validate_training_authorization(*fixture)

    def test_pending_decisions_or_unresolved_source_block(self):
        fixture = list(authorization_fixture())
        fixture[0]["pending_researcher_decisions"] = ["HAM-D01"]
        with self.assertRaisesRegex(TrainingAuthorizationError, "remain pending"):
            validate_training_authorization(*fixture)

        fixture = list(authorization_fixture())
        fixture[2][0]["rights_status"] = "NOT_ESTABLISHED"
        with self.assertRaisesRegex(TrainingAuthorizationError, "eligibility is unresolved"):
            validate_training_authorization(*fixture)

    def test_decision_register_must_resolve_every_required_item(self):
        fixture = list(authorization_fixture())
        fixture[3][0]["decision_status"] = "PENDING_RESEARCHER_REVIEW"
        with self.assertRaisesRegex(TrainingAuthorizationError, "remain unresolved"):
            validate_training_authorization(*fixture)

    def test_cross_partition_identity_overlap_is_rejected(self):
        fixture = list(authorization_fixture())
        fixture[4][1]["patient_id"] = fixture[4][0]["patient_id"]
        with self.assertRaisesRegex(TrainingAuthorizationError, "identity overlap"):
            validate_training_authorization(*fixture)

    def test_test_or_calibration_record_cannot_be_added_to_training(self):
        for record_id in ("record-test", "record-calibration"):
            with self.subTest(record_id=record_id):
                fixture = list(authorization_fixture())
                fixture[0]["approved_training_record_ids"].append(record_id)
                with self.assertRaisesRegex(TrainingAuthorizationError, "partition record IDs overlap"):
                    validate_training_authorization(*fixture)

    def test_unapproved_record_or_inventory_mismatch_is_rejected(self):
        fixture = list(authorization_fixture())
        fixture[4][0]["provisional_eligibility_status"] = "NOT_APPROVED"
        with self.assertRaisesRegex(TrainingAuthorizationError, "not approved eligible"):
            validate_training_authorization(*fixture)

        fixture = list(authorization_fixture())
        fixture[5][0]["image_path"] = "images/other.jpg"
        with self.assertRaisesRegex(TrainingAuthorizationError, "not bound to the approved inventory"):
            validate_training_authorization(*fixture)

    def test_approval_record_must_bind_current_authorization_inputs(self):
        fixture = list(authorization_fixture())
        fixture[6]["source_eligibility_sha256"] = "stale"
        with self.assertRaisesRegex(TrainingAuthorizationError, "hash mismatch"):
            validate_training_authorization(*fixture)

        fixture = list(authorization_fixture())
        fixture[6]["source_inventory_sha256"] = "stale"
        with self.assertRaisesRegex(TrainingAuthorizationError, "source_inventory_sha256"):
            validate_training_authorization(*fixture)

    def test_direct_stage6_validate_only_does_not_consult_central_decision_gates(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            image_directory = root / "synthetic"
            image_directory.mkdir()
            split_rows = []
            inventory_rows = []

            for class_index, class_name in enumerate(CLASS_NAMES):
                for partition in ("train", "validation", "test"):
                    record_id = f"{partition}-{class_index}"
                    relative_path = f"synthetic/{record_id}.jpg"
                    image_bytes = f"synthetic fixture only: {record_id}".encode("ascii")
                    image_path = root / relative_path
                    image_path.write_bytes(image_bytes)
                    row = {
                        "image_path": relative_path,
                        "source_dataset": "SYNTHETIC_FIXTURE",
                        "original_label": class_name.lower(),
                        "class_name": class_name,
                        "class_index": str(class_index),
                        "image_id": record_id,
                        "lesion_id": record_id,
                        "patient_id": record_id,
                        "source_split": "train",
                        "sha256": hashlib.sha256(image_bytes).hexdigest(),
                        "overlap_group": record_id,
                        "duplicate_overlap_evidence_tier": "NONE",
                    }
                    inventory_rows.append(row)
                    split_rows.append({
                        **row,
                        "provisional_eligibility_status": "APPROVED_ELIGIBLE",
                        "split": partition,
                    })

            split_path = root / "approved_split.csv"
            inventory_path = root / "inventory.csv"
            split_fields = list(split_rows[0])
            inventory_fields = list(inventory_rows[0])
            with split_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=split_fields)
                writer.writeheader()
                writer.writerows(split_rows)
            with inventory_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=inventory_fields)
                writer.writeheader()
                writer.writerows(inventory_rows)

            approval = {
                "approval_status": "APPROVED_BY_RESEARCHER",
                "split_protocol": "three_way_v1",
                "approved_by": "synthetic fixture",
                "approval_date_utc": "synthetic fixture",
                "adjudication_reference": "synthetic fixture",
                "source_rights_reference": "synthetic fixture",
                "protected_test_policy_reference": "synthetic fixture",
                "test_partition_frozen": True,
            }
            approval["approved_split_sha256"] = hashlib.sha256(split_path.read_bytes()).hexdigest()
            approval["source_inventory_sha256"] = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
            approval_path = root / "approval.json"
            approval_path.write_text(json.dumps(approval), encoding="utf-8")

            arguments = [
                "nine_class_training.py",
                "--root", str(root),
                "--config", str(DEFAULT_CONFIG),
                "--approved-split", str(split_path),
                "--approval", str(approval_path),
                "--inventory", str(inventory_path),
                "--runs-root", str(root / "runs"),
                "--validate-only",
            ]
            output = StringIO()
            with patch.object(sys, "argv", arguments), redirect_stdout(output):
                result = stage6_main()

            self.assertEqual(result, 0)
            self.assertIn('"approved_split_valid": true', output.getvalue())


if __name__ == "__main__":
    unittest.main()
