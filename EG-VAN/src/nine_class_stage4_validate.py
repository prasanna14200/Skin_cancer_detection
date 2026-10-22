"""Read-only Stage 4 manifest checks and two-image preprocessing smoke test."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from nine_class_dataset import PreprocessConfig, image_tensor
from nine_class_stage4 import CLASS_NAMES, ROOT


def validate(root: Path = ROOT) -> dict:
    manifest = root / "analysis/nine_class_stage4/nine_class_source_manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 13312 or len({r["image_path"] for r in rows}) != len(rows):
        raise ValueError("Manifest count or path uniqueness changed")
    if any(not (root / r["image_path"]).is_file() for r in rows):
        raise FileNotFoundError("Manifest refers to missing images")
    if any(not len(r["sha256"]) == 64 for r in rows):
        raise ValueError("Missing source hash")
    if any(r["image_path"].startswith(("data/isic/train/", "data/isic/test/")) for r in rows):
        raise ValueError("Mirrored binary tree included")
    if any(CLASS_NAMES[int(r["class_index"])] != r["class_name"] for r in rows):
        raise ValueError("Class mapping changed")
    groups = defaultdict(list)
    for row in rows:
        groups[row["overlap_group"]].append(row)
    boundary = sum(any(r["source_split"] == "test" for r in group)
                   and any(r["source_split"] == "train" for r in group)
                   for group in groups.values())
    picks = [next(r for r in rows if r["source_dataset"] == "HAM10000"),
             next(r for r in rows if r["class_name"] == "BENIGN")]
    smoke = []
    for row in picks:
        tensor = image_tensor(root / row["image_path"], PreprocessConfig(image_size=64))
        smoke.append(dict(path=row["image_path"], shape=list(tensor.shape), dtype=str(tensor.dtype)))
    return {
        "rows": len(rows), "unique_groups": len(groups),
        "publisher_train_test_overlap_groups": boundary,
        "quarantine_by_class": dict(sorted(Counter(r["class_name"] for r in rows
                                                 if "QUARANTINE" in r["provisional_eligibility_status"]).items())),
        "binary_status_by_class": {name: dict(sorted(Counter(r["provisional_eligibility_status"]
                                                          for r in rows if r["class_name"] == name).items()))
                                   for name in ("BENIGN", "MALIGNANT")},
        "smoke": smoke,
    }


if __name__ == "__main__":
    report = validate()
    output = ROOT / "analysis/nine_class_stage4/validation_report.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
