"""Freeze read-only Stage 6 dataset-resolution evidence; no approval inferred."""

import csv
import json
from collections import Counter
from pathlib import Path

from nine_class_protocol import file_sha256
from nine_class_stage4 import ROOT


def main() -> None:
    stage4 = ROOT / "analysis/nine_class_stage4"
    stage3i = ROOT / "analysis/nine_class_recovery/stage3i/ai_pair_review.csv"
    inventory = stage4 / "nine_class_source_manifest.csv"
    split_audit = stage4 / "split_eligibility_audit.json"
    review = []
    with stage3i.open(newline="", encoding="utf-8") as handle:
        review = list(csv.DictReader(handle))
    with inventory.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    audit = json.loads(split_audit.read_text(encoding="utf-8"))
    if len(rows) != 13312 or len(review) != 429 or audit["final_split_created"]:
        raise ValueError("Frozen evidence or Stage 4 split status changed")
    benign = [r for r in rows if r["class_name"] == "BENIGN"]
    result = {
        "stage3i_assessment_counts": dict(sorted(Counter(r["ai_assessment"] for r in review).items())),
        "stage4_inventory_records": len(rows),
        "benign_status_counts": dict(sorted(Counter(r["provisional_eligibility_status"] for r in benign).items())),
        "approved_eligible_records_in_stage4_inventory": sum(r["provisional_eligibility_status"] == "APPROVED_ELIGIBLE" for r in rows),
        "stage4_final_split_created": False,
        "publisher_source_test_entries": audit["protected_source_test_records"],
        "paper_exact_binary_version_verified": False,
        "binary_patient_or_lesion_ids_available": False,
        "independent_benign_photo_adjudication_complete": False,
        "nine_class_training_approved": False,
        "nine_class_final_test_approved": False,
        "source_hashes": {
            "stage3i_ai_review": file_sha256(stage3i),
            "stage4_inventory": file_sha256(inventory),
            "stage4_split_audit": file_sha256(split_audit),
        },
    }
    output = ROOT / "analysis/nine_class_stage6/dataset_readiness_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
