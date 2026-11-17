"""Deterministic image-quality proxies for raw and Stage 4 processed images."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nine_class_dataset import PreprocessConfig
from nine_class_protocol import file_sha256, validate_approved_split
from nine_class_stage4 import CLASS_NAMES, ROOT
from preprocessing import gray_world, remove_hair, retinex

IQA_VERSION = "nine_class_iqa_v2"
FEATURES = ("sharpness_laplacian_variance", "brightness_mean", "contrast_std",
            "underexposed_fraction", "overexposed_fraction", "rgb_mean_r", "rgb_mean_g",
            "rgb_mean_b", "rgb_std_r", "rgb_std_g", "rgb_std_b", "color_cast_range",
            "dark_line_fraction", "dark_border_fraction")
FIELDS = ("source_image_key", "image_path", "source_dataset", "class_name", "class_index",
          "source_split", "model_split", "source_image_sha256", "iqa_config_version", "preprocess_config_sha256",
          "measurement_view", "original_width", "original_height", "original_aspect_ratio",
          "original_megapixels", "measured_width", "measured_height", *FEATURES,
          "invalid_metric_flags", "processing_status")


def measure_rgb(image: np.ndarray, *, dark_threshold: int = 30,
                bright_threshold: int = 225, line_threshold: int = 10,
                hair_kernel_size: int = 17) -> tuple[dict[str, float], list[str]]:
    """Measure uint8 RGB pixels; no metric is a clinical usability judgment."""
    if image.ndim != 3 or image.shape[2] != 3 or image.size == 0 or image.dtype != np.uint8:
        raise ValueError("Expected nonempty uint8 RGB image")
    if hair_kernel_size < 3 or hair_kernel_size % 2 != 1:
        raise ValueError("Hair indicator kernel must be odd and >=3")
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    means = image.astype(np.float64).mean(axis=(0, 1))
    stds = image.astype(np.float64).std(axis=(0, 1))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (hair_kernel_size, hair_kernel_size))
    dark_lines = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    height, width = gray.shape
    border = max(1, int(round(min(height, width) * 0.05)))
    mask = np.zeros(gray.shape, dtype=bool)
    mask[:border, :] = mask[-border:, :] = True
    mask[:, :border] = mask[:, -border:] = True
    metrics = {
        "sharpness_laplacian_variance": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "brightness_mean": float(gray.mean()),
        "contrast_std": float(gray.std()),
        "underexposed_fraction": float(np.mean(gray < dark_threshold)),
        "overexposed_fraction": float(np.mean(gray > bright_threshold)),
        "rgb_mean_r": float(means[0]), "rgb_mean_g": float(means[1]),
        "rgb_mean_b": float(means[2]), "rgb_std_r": float(stds[0]),
        "rgb_std_g": float(stds[1]), "rgb_std_b": float(stds[2]),
        "color_cast_range": float((means.max() - means.min()) / 255.0),
        "dark_line_fraction": float(np.mean(dark_lines > line_threshold)),
        "dark_border_fraction": float(np.mean(gray[mask] < dark_threshold)),
    }
    flags = []
    if gray.min() == gray.max():
        flags.append("UNIFORM_LUMINANCE")
    if not all(np.isfinite(value) for value in metrics.values()):
        flags.append("NONFINITE_METRIC")
    return metrics, flags


def stage4_processed_rgb(raw_bgr: np.ndarray, config: PreprocessConfig) -> np.ndarray:
    """Stage 4 deterministic pixel operations, before tensor normalization."""
    bgr = remove_hair(raw_bgr, config.hair_kernel_size, config.hair_threshold,
                      config.inpaint_radius)
    bgr = gray_world(bgr)
    bgr = retinex(bgr, config.retinex_sigmas, config.retinex_weights)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return cv2.resize(rgb, (config.image_size, config.image_size), interpolation=cv2.INTER_AREA)


def select_rows(root: Path, approved_split: Path, approval: Path, inventory: Path,
                per_class: int) -> tuple[list[dict[str, str]], dict]:
    """Select approved train/validation records; never infer model splits."""
    if per_class < 0:
        raise ValueError("per_class must be nonnegative (zero means all eligible records)")
    rows, provenance = validate_approved_split(root, approved_split, approval, inventory)
    if not rows:
        raise ValueError("Approved split contains no rows")
    if any(not provenance.get(key) for key in
           ("split_sha256", "inventory_sha256", "approval_sha256", "split_protocol")):
        raise ValueError("Approved split provenance is incomplete")
    approval_record = provenance.get("approval")
    if (not isinstance(approval_record, dict)
            or approval_record.get("approval_status") != "APPROVED_BY_RESEARCHER"):
        raise ValueError("Researcher approval record is missing")
    required_row_fields = {"image_path", "source_dataset", "class_name", "class_index",
                           "sha256", "source_split", "split", "provisional_eligibility_status"}
    allowed_splits = {"train", "validation", "calibration", "test"}
    for row in rows:
        if not required_row_fields <= row.keys():
            raise ValueError("Approved split row has missing required provenance or model split")
        if row["split"] not in allowed_splits:
            raise ValueError(f'Unknown model split: {row["split"]}')
        if row["provisional_eligibility_status"] != "APPROVED_ELIGIBLE":
            raise ValueError("Unapproved cohort row cannot be used for descriptive IQA")
    selected = []
    for name in CLASS_NAMES:
        candidates = sorted((row for row in rows if row["class_name"] == name
                             and row["split"] in ("train", "validation")), key=lambda r: r["image_path"])
        if not candidates:
            raise ValueError(f"No approved train/validation image for {name}")
        selected.extend(candidates[:per_class] if per_class else candidates)
    keys = [(r["source_dataset"], r["image_path"]) for r in selected]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate source-qualified image key")
    return selected, provenance


def collect_record(root: Path, row: dict[str, str], view: str,
                   config: PreprocessConfig, config_hash: str) -> tuple[dict, np.ndarray | None]:
    if view not in ("raw", "stage4_processed"):
        raise ValueError("Unknown IQA view")
    relative = Path(row["image_path"])
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Invalid or missing source path: {relative}")
    if file_sha256(path) != row["sha256"]:
        raise ValueError(f"Source image hash changed: {relative}")
    record = {"source_image_key": f'{row["source_dataset"]}:{relative.as_posix()}',
              "image_path": relative.as_posix(), "source_dataset": row["source_dataset"],
              "class_name": row["class_name"], "class_index": row["class_index"],
              "source_split": row["source_split"], "model_split": row["split"],
              "source_image_sha256": row["sha256"],
              "iqa_config_version": IQA_VERSION, "preprocess_config_sha256": config_hash,
              "measurement_view": view, "invalid_metric_flags": "", "processing_status": "OK"}
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        return {**record, "processing_status": "DECODE_FAILED", "invalid_metric_flags": "ALL_METRICS_MISSING"}, None
    height, width = bgr.shape[:2]
    record.update(original_width=width, original_height=height,
                  original_aspect_ratio=width / height, original_megapixels=width * height / 1e6)
    try:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if view == "raw" else stage4_processed_rgb(bgr, config)
        record.update(measured_width=rgb.shape[1], measured_height=rgb.shape[0])
        metrics, flags = measure_rgb(rgb, hair_kernel_size=config.hair_kernel_size,
                                    line_threshold=config.hair_threshold)
        record.update(metrics)
        record["invalid_metric_flags"] = "|".join(flags)
        if "NONFINITE_METRIC" in flags:
            record["processing_status"] = "INVALID_METRIC"
        return record, rgb
    except (ValueError, cv2.error, FloatingPointError) as exc:
        return {**record, "processing_status": "PROCESSING_FAILED",
                "invalid_metric_flags": f"ALL_METRICS_MISSING:{type(exc).__name__}"}, None


def render_summary(records: list[dict], output_dir: Path) -> list[str]:
    valid = [r for r in records if r["processing_status"] == "OK"]
    outputs = []
    if not valid:
        return outputs
    for feature in ("sharpness_laplacian_variance", "brightness_mean", "contrast_std",
                    "underexposed_fraction", "overexposed_fraction"):
        fig, ax = plt.subplots(figsize=(6, 4))
        for view in ("raw", "stage4_processed"):
            values = [float(r[feature]) for r in valid if r["measurement_view"] == view]
            if values:
                ax.hist(values, bins=min(15, max(1, len(values))), alpha=0.55, label=view)
        ax.set(xlabel=feature, ylabel="Number of descriptive sample images", title=feature)
        ax.legend()
        fig.tight_layout()
        filename = f"distribution_{feature}.png"
        fig.savefig(output_dir / filename, dpi=140)
        plt.close(fig)
        outputs.append(filename)
    features = ("sharpness_laplacian_variance", "brightness_mean", "contrast_std",
                "underexposed_fraction", "overexposed_fraction", "color_cast_range", "dark_line_fraction")
    raw = [r for r in valid if r["measurement_view"] == "raw"]
    matrix = np.array([[float(r[name]) for name in features] for r in raw], dtype=float)
    if len(matrix) >= 3:
        correlation = np.ma.masked_invalid(np.corrcoef(matrix, rowvar=False))
        fig, ax = plt.subplots(figsize=(8, 7))
        plot = ax.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(features)), [x.replace("_", " ") for x in features], rotation=60, ha="right")
        ax.set_yticks(range(len(features)), [x.replace("_", " ") for x in features])
        fig.colorbar(plot, ax=ax)
        fig.tight_layout()
        fig.savefig(output_dir / "raw_feature_correlation.png", dpi=140)
        plt.close(fig)
        outputs.append("raw_feature_correlation.png")
    return outputs


def run(root: Path, approved_split: Path, approval: Path, inventory: Path,
        output_dir: Path, *, per_class: int = 1) -> dict:
    if output_dir.exists():
        raise FileExistsError(output_dir)
    rows, provenance = select_rows(root, approved_split, approval, inventory, per_class)
    config = PreprocessConfig()
    config_json = json.dumps(asdict(config), sort_keys=True)
    config_hash = hashlib.sha256(config_json.encode()).hexdigest()
    records = []
    examples = []
    example_sources = set()
    for row in rows:
        pair = []
        for view in ("raw", "stage4_processed"):
            record, rgb = collect_record(root, row, view, config, config_hash)
            records.append(record)
            pair.append(rgb)
        if file_sha256(root / row["image_path"]) != row["sha256"]:
            raise ValueError(f'Source image changed during IQA: {row["image_path"]}')
        if row["source_dataset"] not in example_sources and all(item is not None for item in pair):
            examples.append((row["source_dataset"], row["image_path"], pair))
            example_sources.add(row["source_dataset"])
    output_dir.mkdir(parents=True, exist_ok=False)
    with (output_dir / "iqa_features.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    figures = render_summary(records, output_dir)
    for index, (source, path, pair) in enumerate(examples, 1):
        fig, axes = plt.subplots(1, 2, figsize=(9, 4))
        for axis, image, label in zip(axes, pair, ("Raw example", "Stage 4 processed example")):
            axis.imshow(image)
            axis.set_title(label)
            axis.axis("off")
        fig.suptitle(f"Descriptive example {index}: {source}:{path}\nProxy changes are not proof of clinical improvement", fontsize=9)
        fig.tight_layout()
        name = f"example_{index}_raw_vs_processed.png"
        fig.savefig(output_dir / name, dpi=140)
        plt.close(fig)
        figures.append(name)
    summary = {"status": "DESCRIPTIVE_ONLY_NOT_ELIGIBILITY_OR_PERFORMANCE",
               "iqa_config_version": IQA_VERSION,
               "approved_split_sha256": provenance["split_sha256"],
               "inventory_sha256": provenance["inventory_sha256"],
               "approval_sha256": provenance["approval_sha256"],
               "selected_model_splits": sorted({row["split"] for row in rows}),
               "excluded_model_splits": ["calibration", "test"],
               "preprocess_config_sha256": config_hash, "preprocess_config": asdict(config),
               "publisher_test_excluded": all(row["source_split"] != "test" for row in rows),
               "sample_per_class": per_class,
               "source_image_hashes_unchanged": True,
               "source_images": len(rows), "measurements": len(records),
               "status_counts": {key: sum(r["processing_status"] == key for r in records)
                                 for key in sorted({r["processing_status"] for r in records})},
               "figures": figures}
    (output_dir / "iqa_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--approved-split", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-per-class", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.approved_split, args.approval, args.inventory, args.output_dir,
                         per_class=args.sample_per_class), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
