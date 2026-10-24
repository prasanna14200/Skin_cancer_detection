"""Bounded descriptive preprocessing comparison; never writes source images or splits."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from nine_class_dataset import PreprocessConfig, preprocessing_hash
from nine_class_iqa import measure_rgb
from nine_class_protocol import file_sha256
from nine_class_stage4 import CLASS_NAMES, ROOT
from preprocessing import gray_world, remove_hair, retinex

VARIANTS = ("A_raw", "B_hair_grayworld", "C_stage4_full", "D_mild_luminance_retinex")
VERSION = "stage10_descriptive_v1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def select_sample(root: Path, inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    """Choose brightness extremes and an artifact proxy from 16 sorted non-test rows/class."""
    selected = []
    for class_name in CLASS_NAMES:
        candidates = sorted((r for r in inventory if r["class_name"] == class_name
                             and r["source_split"] != "test"), key=lambda r: r["image_path"])[:16]
        if not candidates:
            raise ValueError(f"No non-test candidate for {class_name}")
        scored = []
        for row in candidates:
            image = cv2.imread(str(root / row["image_path"]), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"Cannot decode {row['image_path']}")
            rgb = cv2.cvtColor(cv2.resize(image, (224, 224)), cv2.COLOR_BGR2RGB)
            metrics, _ = measure_rgb(rgb)
            scored.append((row, metrics))
        picks = [(min(scored, key=lambda x: (x[1]["brightness_mean"], x[0]["image_path"])), "low_brightness"),
                 (max(scored, key=lambda x: (x[1]["brightness_mean"], x[0]["image_path"])), "high_brightness"),
                 (max(scored, key=lambda x: (x[1]["dark_line_fraction"], x[0]["image_path"])), "high_dark_line_proxy")]
        for (row, metrics), reason in picks:
            if not any(item["image_path"] == row["image_path"] for item in selected):
                selected.append({**row, "selection_reason": reason,
                                 "selection_brightness": metrics["brightness_mean"],
                                 "selection_dark_line_fraction": metrics["dark_line_fraction"]})
    return selected


def mild_luminance_retinex(image_bgr: np.ndarray, sigma: float = 80.0,
                            strength: float = 0.15, max_gain: float = 1.2) -> np.ndarray:
    """Exploratory standard-sign luminance correction with bounded gain; no channel stretch."""
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3 or image_bgr.dtype != np.uint8:
        raise ValueError("Expected uint8 BGR image")
    if sigma <= 0 or not 0 <= strength <= 1 or max_gain < 1:
        raise ValueError("Invalid conservative Retinex settings")
    luminance = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    blurred = cv2.GaussianBlur(luminance, (0, 0), sigmaX=sigma, sigmaY=sigma)
    response = np.log(np.maximum(luminance, 1 / 255)) - np.log(np.maximum(blurred, 1 / 255))
    gain = np.exp(np.clip(strength * response, -np.log(max_gain), np.log(max_gain)))
    return np.clip(np.rint(image_bgr.astype(np.float32) * gain[..., None]), 0, 255).astype(np.uint8)


def variant_rgb(raw_bgr: np.ndarray, variant: str, config: PreprocessConfig) -> np.ndarray:
    if variant not in VARIANTS:
        raise ValueError("Unknown variant")
    result = raw_bgr
    if variant != "A_raw":
        result = remove_hair(result, config.hair_kernel_size, config.hair_threshold, config.inpaint_radius)
        result = gray_world(result)
    if variant == "C_stage4_full":
        result = retinex(result, config.retinex_sigmas, config.retinex_weights)
    elif variant == "D_mild_luminance_retinex":
        result = mild_luminance_retinex(result)
    rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return cv2.resize(rgb, (config.image_size, config.image_size), interpolation=cv2.INTER_AREA)


def similarity_proxies(raw: np.ndarray, processed: np.ndarray) -> dict[str, float]:
    first = cv2.cvtColor(raw, cv2.COLOR_RGB2GRAY)
    second = cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY)
    hist_a = cv2.calcHist([first], [0], None, [256], [0, 256]).ravel() / first.size
    hist_b = cv2.calcHist([second], [0], None, [256], [0, 256]).ravel() / second.size
    edge_a = cv2.Laplacian(first, cv2.CV_32F).ravel()
    edge_b = cv2.Laplacian(second, cv2.CV_32F).ravel()
    def correlation(a: np.ndarray, b: np.ndarray) -> float | None:
        if float(np.std(a)) < 1e-8 or float(np.std(b)) < 1e-8:
            return None
        return float(np.corrcoef(a, b)[0, 1])
    return {"luminance_histogram_l1": float(np.abs(hist_a - hist_b).sum()),
            "luminance_pixel_correlation": correlation(first.ravel(), second.ravel()),
            "laplacian_edge_correlation": correlation(edge_a, edge_b),
            "channel_clip_fraction": float(np.mean((processed <= 1) | (processed >= 254)))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "analysis/nine_class_stage10")
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output_dir
    if out.exists():
        raise FileExistsError(out)
    inventory_path = root / "analysis/nine_class_stage4/nine_class_source_manifest.csv"
    review_path = root / "analysis/nine_class_recovery/stage3i/ai_pair_review.csv"
    exclusion_path = root / "analysis/nine_class_overlap_completion/proposed_binary_exclusions.csv"
    inventory = read_csv(inventory_path)
    reviews = read_csv(review_path)
    sample = select_sample(root, inventory)
    config = PreprocessConfig()
    pair_counts = Counter(r["ai_assessment"] for r in reviews)
    statuses = Counter(r["provisional_eligibility_status"] for r in inventory)
    groups = defaultdict(list)
    for row in inventory:
        groups[row["overlap_group"]].append(row)
    crossing = sum(any(r["source_split"] == "test" for r in rows)
                   and any(r["source_split"] == "train" for r in rows)
                   for rows in groups.values())
    upper = {}
    for name in CLASS_NAMES:
        rows = [r for r in inventory if r["class_name"] == name]
        proposed = [r for r in rows if r["provisional_eligibility_status"] != "PRIOR_PROPOSED_EXCLUSION_NOT_APPROVED"]
        upper[name] = {"inventory_records": len(rows), "post_proposal_records_upper_bound": len(proposed),
                       "post_proposal_source_train_upper_bound": sum(r["source_split"] != "test" for r in proposed),
                       "post_proposal_source_test_upper_bound": sum(r["source_split"] == "test" for r in proposed),
                       "post_proposal_distinct_overlap_groups_upper_bound": len({r["overlap_group"] for r in proposed}),
                       "approved_eligible": sum(r["provisional_eligibility_status"] == "APPROVED_ELIGIBLE" for r in rows)}
    audit = {"version": VERSION, "inventory_sha256": file_sha256(inventory_path),
             "review_sha256": file_sha256(review_path), "proposed_exclusions_sha256": file_sha256(exclusion_path),
             "source_records": len(inventory), "source_dataset_counts": dict(Counter(r["source_dataset"] for r in inventory)),
             "provisional_status_counts": dict(statuses), "ai_pair_counts": dict(pair_counts),
             "source_train_test_overlap_groups": crossing, "class_upper_bounds_not_eligible_counts": upper,
             "approved_split_exists": False, "full_training_ready": False}
    out.mkdir(parents=True, exist_ok=False)
    (out / "dataset_eligibility_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    sample_fields = list(sample[0])
    with (out / "descriptive_sample.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, sample_fields)
        writer.writeheader()
        writer.writerows(sample)
    metric_rows = []
    tiles = []
    for row in sample:
        path = root / row["image_path"]
        if file_sha256(path) != row["sha256"]:
            raise ValueError(f"Original image hash differs from inventory: {path}")
        raw_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
        variants = {name: variant_rgb(raw_bgr, name, config) for name in VARIANTS}
        raw = variants["A_raw"]
        for name, rgb in variants.items():
            metrics, flags = measure_rgb(rgb)
            metric_rows.append({"image_path": row["image_path"], "source_dataset": row["source_dataset"],
                                "class_name": row["class_name"], "source_split": row["source_split"],
                                "source_sha256": row["sha256"], "variant": name, "metric_flags": "|".join(flags),
                                **metrics, **similarity_proxies(raw, rgb)})
        thumb_rows = []
        for name, rgb in variants.items():
            thumb = cv2.resize(rgb, (192, 192), interpolation=cv2.INTER_AREA)
            thumb = cv2.copyMakeBorder(thumb, 24, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            cv2.putText(thumb, name.split("_")[0], (5, 17), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 0), 1)
            thumb_rows.append(thumb)
        tiles.append(np.hstack(thumb_rows))
        if file_sha256(path) != row["sha256"]:
            raise ValueError(f"Original image changed during audit: {path}")
    with (out / "preprocessing_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, list(metric_rows[0]))
        writer.writeheader()
        writer.writerows(metric_rows)
    cv2.imwrite(str(out / "preprocessing_contact_sheet.jpg"), cv2.cvtColor(np.vstack(tiles), cv2.COLOR_RGB2BGR))
    summary = {"version": VERSION, "sample_count": len(sample), "metric_rows": len(metric_rows),
               "source_test_sample_count": sum(r["source_split"] == "test" for r in sample),
               "legacy_preprocess_sha256": preprocessing_hash(config),
               "candidate_raw_preprocess_sha256": preprocessing_hash(PreprocessConfig(pipeline_version="raw_resize_imagenet_v2")),
               "variants": {name: {metric: float(np.median([r[metric] for r in metric_rows if r["variant"] == name and r[metric] is not None]))
                                    for metric in ("brightness_mean", "contrast_std", "underexposed_fraction", "overexposed_fraction",
                                                   "color_cast_range", "sharpness_laplacian_variance", "channel_clip_fraction",
                                                   "luminance_histogram_l1", "luminance_pixel_correlation", "laplacian_edge_correlation")}
                            for name in VARIANTS}}
    (out / "preprocessing_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sample_count": len(sample), "metric_rows": len(metric_rows),
                      "eligibility": "BLOCKED", "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
