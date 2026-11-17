"""Separate validation/final-test inference for an approved nine-class cohort."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from models.egvan import build_nine_class_egvan
from nine_class_dataset import NineClassDataset, preprocessing_for_training, preprocessing_hash
from nine_class_metrics import summarize_predictions
from nine_class_protocol import file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES, ROOT
from nine_class_training import DEFAULT_INVENTORY


def predict(model: torch.nn.Module, loader: DataLoader, device: torch.device,
            *, return_logits: bool = False):
    model.eval()
    probabilities, targets, raw_logits = [], [], []
    with torch.inference_mode():
        for images, labels in loader:
            logits = model(images.to(device))
            if logits.ndim != 2 or logits.shape[1] != 9:
                raise ValueError("Checkpoint model does not return nine logits")
            probabilities.append(torch.softmax(logits.float(), dim=1).cpu().numpy())
            if return_logits:
                raw_logits.append(logits.float().cpu().numpy())
            targets.extend(labels.tolist())
    result = np.concatenate(probabilities), np.asarray(targets, dtype=np.int64)
    return (*result, np.concatenate(raw_logits)) if return_logits else result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--approved-split", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", choices=("validation", "calibration", "test"), required=True)
    parser.add_argument("--final-test", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    if args.batch_size < 1:
        raise ValueError("Batch size must be positive")
    rows, provenance = validate_approved_split(args.root, args.approved_split, args.approval, args.inventory)
    if args.split == "test":
        if not args.final_test or not provenance["approval"].get("test_partition_frozen"):
            raise ValueError("Final test requires --final-test and an explicitly frozen protected test")
        if not provenance["test_has_all_classes"]:
            raise ValueError("Cannot report nine-class test accuracy: one or more test classes absent")
    elif args.final_test:
        raise ValueError("--final-test is only valid for protected test evaluation")
    checkpoint = args.checkpoint.resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    # Read only a project-owned, trusted checkpoint; the loader checks hashes below.
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    run_provenance = checkpoint.parent / "run_provenance.json"
    if not run_provenance.is_file():
        raise ValueError("Missing run provenance next to checkpoint")
    run_info = json.loads(run_provenance.read_text(encoding="utf-8"))
    expected = {"split_sha256": provenance["split_sha256"],
                "inventory_sha256": provenance["inventory_sha256"],
                "approval_sha256": provenance["approval_sha256"],
                "config_sha256": run_info["config_sha256"],
                "preprocess_config_sha256": preprocessing_hash(
                    preprocessing_for_training(run_info["config"])) }
    if any(state.get(key) != value or run_info.get(key) != value for key, value in expected.items()):
        raise ValueError("Checkpoint, run or approved cohort provenance mismatch")
    config = run_info["config"]
    model = build_nine_class_egvan(fusion_channels=int(config["fusion_channels"]))
    model.load_state_dict(state["model_state"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    dataset = NineClassDataset(args.root, args.approved_split, args.split,
                               preprocessing_for_training(config))
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    if args.split == "calibration":
        probabilities, targets, logits = predict(model, loader, device, return_logits=True)
    else:
        probabilities, targets = predict(model, loader, device)
    report = summarize_predictions(probabilities, targets, split=args.split)
    report["provenance"] = {**expected, "checkpoint_sha256": file_sha256(checkpoint),
                            "checkpoint_epoch": int(state["epoch"]), "checkpoint_path": str(checkpoint),
                            "source_split": str(args.approved_split)}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with (args.output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["image_path", "source_dataset", "target_index", "predicted_index"] + [f"prob_{name}" for name in CLASS_NAMES]
        if args.split == "calibration":
            fields += [f"logit_{name}" for name in CLASS_NAMES]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, (row, target, prob) in enumerate(zip(dataset.rows, targets, probabilities)):
            writer.writerow({"image_path": row["image_path"], "source_dataset": row["source_dataset"],
                             "target_index": int(target), "predicted_index": int(prob.argmax()),
                             **{f"prob_{name}": float(prob[i]) for i, name in enumerate(CLASS_NAMES)},
                             **({f"logit_{name}": float(logits[index, i]) for i, name in enumerate(CLASS_NAMES)}
                                if args.split == "calibration" else {})})
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
