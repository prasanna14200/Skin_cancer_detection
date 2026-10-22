#!/usr/bin/env python3
"""Make ordered visual-review sheets from the frozen 429-pair evidence."""

from __future__ import annotations

import csv
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from nine_class_benign_review import ROOT, atomic_text, read_csv


LEDGER = Path("analysis/nine_class_recovery/benign_pair_review_ledger.csv")
GEOMETRY = Path("analysis/nine_class_recovery/geometric_pair_evidence.csv")
STRONG = Path("analysis/nine_class_recovery/stage3g/strong_pair_identity_evidence.csv")
OUTPUT = Path("analysis/nine_class_recovery/stage3i")
FIELDS = ("review_order", "sheet", "sheet_slot", "candidate_pair_id", "binary_image_path",
          "candidate_path", "binary_sha256", "candidate_sha256", "binary_dimensions",
          "candidate_dimensions")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ordered_pairs(root: Path) -> list[dict]:
    rows = read_csv(root / LEDGER)
    strong = read_csv(root / STRONG)
    strong_ids = {row["candidate_pair_id"] for row in strong}
    if len(rows) != 429 or len({r["candidate_pair_id"] for r in rows}) != 429 or len(strong_ids) != 83:
        raise ValueError("Frozen pair count or IDs changed")
    source_test = [r for r in rows if r["candidate_pair_id"] in strong_ids and
                   r["source_split"] == "test"]
    source_train = [r for r in rows if r["candidate_pair_id"] in strong_ids and
                    r["source_split"] == "train"]
    other = [r for r in rows if r["candidate_pair_id"] not in strong_ids]
    ordered = source_test + source_train + other
    if len(source_test) != 19 or len(source_train) != 64 or len(other) != 346:
        raise ValueError("Frozen strong-pair priority changed")
    return ordered


def csv_text(rows: list[dict]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def draw_fit(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
    fitted = ImageOps.contain(image, (box[2] - box[0], box[3] - box[1]))
    x = box[0] + (box[2] - box[0] - fitted.width) // 2
    y = box[1] + (box[3] - box[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))


def generate(root: Path = ROOT, output: Path = OUTPUT) -> dict:
    root = root.resolve()
    output = (root / output).resolve()
    if not output.is_relative_to(root / "analysis/nine_class_recovery"):
        raise ValueError("Output must stay under nine_class_recovery")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Stage 3I output exists; preserve existing review evidence")
    rows = ordered_pairs(root)
    geometry = {r["candidate_pair_id"]: r for r in read_csv(root / GEOMETRY)}
    if set(geometry) != {r["candidate_pair_id"] for r in rows}:
        raise ValueError("Geometry and review pairs differ")
    font = ImageFont.load_default()
    manifest = []
    sheets = []
    for start in range(0, len(rows), 12):
        sheet_number = start // 12 + 1
        sheet_name = f"sheet_{sheet_number:02d}.jpg"
        canvas = Image.new("RGB", (1770, 1320), "white")
        draw = ImageDraw.Draw(canvas)
        for slot, row in enumerate(rows[start:start + 12], 1):
            n = start + slot
            col = (slot - 1) % 3
            line = (slot - 1) // 3
            x, y = col * 590, line * 330
            pair_id = row["candidate_pair_id"]
            geo = geometry[pair_id]
            originals = []
            sizes = []
            for side, relative in enumerate((row["binary_image_path"], row["candidate_path"])):
                path = (root / relative).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    raise ValueError(f"Missing or unsafe original image: {relative}")
                with Image.open(path) as source:
                    picture = source.convert("RGB")
                originals.append(sha256(path))
                sizes.append(f"{picture.width}x{picture.height}")
                draw_fit(canvas, picture, (x + 5 + side * 290, y + 38, x + 287 + side * 290, y + 278))
            draw.rectangle((x, y, x + 589, y + 329), outline="#777777", width=1)
            draw.text((x + 7, y + 5), f"#{n:03d}  {pair_id}", fill="black", font=font)
            draw.text((x + 7, y + 21), f"{Path(row['binary_image_path']).name} / {Path(row['candidate_path']).name}"
                      f"  {row['source_split']}", fill="black", font=font)
            draw.text((x + 7, y + 282), f"corr={row['pixel_correlation']} MAE={row['pixel_mae']}"
                      f" pH={row['phash_distance']} dH={row['dhash_distance']}", fill="black", font=font)
            draw.text((x + 7, y + 299), f"geo={geo['method']} inliers={geo['inlier_count']}"
                      f" ratio={geo['inlier_ratio']} {geo['geometry_status']}", fill="black", font=font)
            manifest.append({"review_order": n, "sheet": sheet_name, "sheet_slot": slot,
                             "candidate_pair_id": pair_id,
                             "binary_image_path": row["binary_image_path"],
                             "candidate_path": row["candidate_path"],
                             "binary_sha256": originals[0], "candidate_sha256": originals[1],
                             "binary_dimensions": sizes[0], "candidate_dimensions": sizes[1]})
        sheets.append((sheet_name, canvas))
    source_hashes = {str(path): sha256(root / path) for path in (LEDGER, GEOMETRY, STRONG)}
    output.mkdir(parents=True, exist_ok=False) if not output.exists() else None
    (output / "sheets").mkdir(exist_ok=False)
    for name, canvas in sheets:
        canvas.save(output / "sheets" / name, quality=93, subsampling=0)
    atomic_text(output / "sheet_manifest.csv", csv_text(manifest))
    summary = {"pair_count": len(manifest), "sheet_count": len(sheets),
               "ordering": "19 strong source test, 64 strong source train, 346 remaining",
               "source_sha256": source_hashes,
               "purpose": "visual review aids; sheets alone do not constitute identity decisions"}
    atomic_text(output / "sheet_manifest_summary.json", json.dumps(summary, indent=2) + "\n")
    if any(sha256(root / Path(path)) != value for path, value in source_hashes.items()):
        raise ValueError("Source evidence changed while making visual review sheets")
    return summary


def generate_overlay_sheets(root: Path = ROOT, output: Path = OUTPUT) -> int:
    """Arrange existing Stage 3G overlays for a separate visual inspection pass."""
    root = root.resolve()
    output = (root / output).resolve()
    target = output / "overlay_sheets"
    if target.exists():
        raise FileExistsError("Preserving existing overlay sheets")
    ordered = ordered_pairs(root)[:83]
    strong = {r["candidate_pair_id"]: r for r in read_csv(root / STRONG)}
    target.mkdir(parents=True)
    count = 0
    for start in range(0, 83, 12):
        canvas = Image.new("RGB", (1770, 1120), "white")
        draw = ImageDraw.Draw(canvas)
        for local, row in enumerate(ordered[start:start + 12]):
            n = start + local + 1
            x, y = local % 3 * 590, local // 3 * 280
            path = (root / strong[row["candidate_pair_id"]]["overlay_reference"]).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError(f"Missing overlay {path}")
            with Image.open(path) as image:
                picture = image.convert("RGB")
            draw_fit(canvas, picture, (x + 3, y + 30, x + 587, y + 255))
            draw.rectangle((x, y, x + 589, y + 279), outline="#777777")
            draw.text((x + 5, y + 5), f"#{n:03d} {Path(row['binary_image_path']).name} / "
                      f"{Path(row['candidate_path']).name}", fill="black")
        canvas.save(target / f"overlay_sheet_{start // 12 + 1:02d}.jpg",
                    quality=93, subsampling=0)
        count += 1
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlays", action="store_true", help="Make separate Stage 3G overlay sheets")
    args = parser.parse_args()
    print(generate_overlay_sheets() if args.overlays else json.dumps(generate(), indent=2))
