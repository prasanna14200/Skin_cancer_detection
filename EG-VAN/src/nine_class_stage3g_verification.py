#!/usr/bin/env python3
"""Stage 3G evidence for 83 strong BENIGN-HAM pairs; no adjudication or exclusions."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from nine_class_benign_review import LEDGER, ROOT, atomic_text, read_csv, sha256
from nine_class_geometric_verification import OUTPUT as GEOMETRY, VALIDATION, geometric_evidence, load_gray


OUTPUT = Path("analysis/nine_class_recovery/stage3g")
PAIR_FILE = "strong_pair_identity_evidence.csv"
SUMMARY_FILE = "stage3g_summary.json"
BLIND_QUEUE_FILE = "blinded_validation_queue.csv"
FIELDS = ("candidate_pair_id", "binary_image_path", "ham_candidate_path",
          "source_partition", "ham_image_id", "ham_lesion_id", "ham_dx",
          "ham_dx_type", "binary_source_image_id", "binary_patient_id",
          "original_phash_distance", "original_dhash_distance", "original_pixel_mae_8bit",
          "original_pixel_correlation", "geometric_method", "candidate_view",
          "keypoints_binary", "keypoints_ham", "mutual_matches", "inlier_count",
          "inlier_ratio", "median_reprojection_error_px", "corner_area_ratio",
          "center_shift_px", "perspective_strength", "valid_aligned_fraction",
          "aligned_grayscale_mae_8bit", "aligned_grayscale_correlation",
          "central_inlier_fraction", "inlier_hull_fraction", "transformation_plausibility",
          "registration_failure_reason", "lesion_structure_match_status",
          "overlay_reference", "difference_reference", "landmark_reference",
          "original_binary_reference", "original_ham_reference", "prior_human_decision",
          "prior_human_timestamp_utc", "identity_conclusion_status", "review_requirement",
          "geometric_evidence_reference", "human_ledger_reference")
BLIND_FIELDS = ("blind_case_id", "source_image_path", "comparison_image_path",
                "partition", "metadata_relation_status", "review_status",
                "independent_reviewer_1", "independent_reviewer_2", "adjudication_status")


def write_rows(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    atomic_text(path, buffer.getvalue())


def safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    x, y = a.astype(np.float32).ravel(), b.astype(np.float32).ravel()
    if len(x) < 10 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def analyze_pair(root: Path, row: dict, geometry_row: dict) -> tuple[dict, dict[str, bytes]]:
    binary = load_gray(root / row["binary_image_path"])
    ham = load_gray(root / row["candidate_path"])
    if geometry_row["candidate_view"] != "aspect_normalized_to_binary":
        raise ValueError("Unexpected view for strong HAM pair")
    ham_view = cv2.resize(ham, (binary.shape[1], binary.shape[0]), interpolation=cv2.INTER_AREA)
    result = geometric_evidence(binary, ham)
    if result["geometry_status"] != "coherent" or result["method"] != geometry_row["method"]:
        raise ValueError("Strong pair geometry could not be reproduced")
    if str(result["inlier_count"]) != geometry_row["inlier_count"]:
        raise ValueError("Inlier count changed from frozen Stage 3F evidence")
    transform = np.asarray(json.loads(geometry_row["homography"]), dtype=np.float64)
    if transform.shape != (3, 3) or not np.isfinite(transform).all():
        raise ValueError("Invalid frozen homography")
    h, w = binary.shape
    warped = cv2.warpPerspective(ham_view, transform, (w, h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    mask = cv2.warpPerspective(np.full(ham_view.shape, 255, np.uint8), transform, (w, h),
                               flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT,
                               borderValue=0) > 0
    valid_fraction = float(np.mean(mask))
    if mask.sum() < 10:
        raise ValueError("No aligned comparison area")
    mae = float(np.mean(np.abs(binary[mask].astype(np.float32) - warped[mask].astype(np.float32))))
    correlation = safe_corr(binary[mask], warped[mask])
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    mapped = cv2.perspectiveTransform(corners, transform).reshape(-1, 2)
    area_ratio = abs(float(cv2.contourArea(mapped.astype(np.float32)))) / (w * h)
    center = np.float32([[[w / 2, h / 2]]])
    transformed_center = cv2.perspectiveTransform(center, transform)[0, 0]
    shift = float(np.linalg.norm(transformed_center - center[0, 0]))
    perspective = abs(float(transform[2, 0])) * w + abs(float(transform[2, 1])) * h
    points = np.asarray(result["points_binary"], dtype=np.float32)
    central = ((points[:, 0] >= .2 * w) & (points[:, 0] <= .8 * w) &
               (points[:, 1] >= .2 * h) & (points[:, 1] <= .8 * h))
    central_fraction = float(np.mean(central))
    hull_fraction = float(cv2.contourArea(cv2.convexHull(points))) / (w * h) if len(points) >= 3 else 0.0
    # These are geometric sanity gates only, not image-identity thresholds.
    plausible = (np.isfinite(mapped).all() and .5 <= area_ratio <= 2.0 and
                 np.linalg.det(transform[:2, :2]) > 0 and perspective <= .1 and
                 shift <= .5 * np.hypot(w, h) and valid_fraction >= .7)
    failure = "" if plausible else "implausible_corner_mapping_or_low_overlap"

    bgr_binary = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    bgr_warped = cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)
    blended = cv2.addWeighted(bgr_binary, .5, bgr_warped, .5, 0)
    blended[~mask] = (230, 230, 230)
    overlay = np.concatenate((bgr_binary, bgr_warped, blended), axis=1)
    diff = cv2.absdiff(binary, warped)
    diff = np.minimum(diff.astype(np.uint16) * 4, 255).astype(np.uint8)
    difference = cv2.applyColorMap(diff, cv2.COLORMAP_TURBO)
    difference[~mask] = (230, 230, 230)
    landmarks = np.concatenate((bgr_binary, bgr_warped), axis=1)
    cv2.rectangle(landmarks, (round(.2*w), round(.2*h)), (round(.8*w), round(.8*h)),
                  (255, 200, 0), 1)
    for point, is_central in zip(points, central):
        x, y = int(round(point[0])), int(round(point[1]))
        if 0 <= x < w and 0 <= y < h:
            cv2.circle(landmarks, (x, y), 1, (0, 255, 0) if is_central else (0, 0, 255), -1)
    result_row = {
        "corner_area_ratio": round(area_ratio, 6),
        "center_shift_px": round(shift, 4),
        "perspective_strength": round(perspective, 6),
        "valid_aligned_fraction": round(valid_fraction, 6),
        "aligned_grayscale_mae_8bit": round(mae, 6),
        "aligned_grayscale_correlation": round(correlation, 8),
        "central_inlier_fraction": round(central_fraction, 6),
        "inlier_hull_fraction": round(hull_fraction, 6),
        "transformation_plausibility": "plausible_geometric_mapping" if plausible else "requires_manual_geometry_check",
        "registration_failure_reason": failure,
    }
    encoded = {}
    for name, image in (("overlay", overlay), ("difference", difference), ("landmarks", landmarks)):
        ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 92])
        if not ok:
            raise ValueError("Could not encode review visualization")
        encoded[name] = buffer.tobytes()
    return result_row, encoded


def run(root: Path = ROOT, output: Path = OUTPUT) -> dict:
    root = root.resolve()
    destination = (root / output).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Preserving existing Stage 3G output: {destination}")
    geometry_path = root / GEOMETRY
    ledger_path = root / LEDGER
    validation_path = root / VALIDATION
    source_hashes = {str(path.relative_to(root)): sha256(path) for path in
                     (geometry_path, ledger_path, validation_path,
                      root / "data/raw/HAM10000_metadata.csv")}
    geometry = read_csv(geometry_path)
    ledger = {row["candidate_pair_id"]: row for row in read_csv(ledger_path)}
    metadata = {row["image_id"]: row for row in read_csv(root / "data/raw/HAM10000_metadata.csv")}
    strong = [row for row in geometry if row["geometry_status"] == "coherent"]
    if len(strong) != 83 or len({row["binary_image_path"] for row in strong}) != 83:
        raise ValueError("Expected one coherent pair for each of 83 BENIGN records")
    validation = [row for row in read_csv(validation_path)
                  if row["truth_status"] == "provisional_distinct_requires_independent_verification"]
    if len(validation) != 40:
        raise ValueError("Expected 40 provisional negative validation pairs")
    report_rows = []
    artifacts = {}
    for index, geometric in enumerate(strong, 1):
        pair_id = geometric["candidate_pair_id"]
        human = ledger[pair_id]
        ham_id = Path(geometric["candidate_path"]).stem
        ham = metadata[ham_id]
        metrics, images = analyze_pair(root, human, geometric)
        short = pair_id[:16]
        image_refs = {
            "overlay": f"overlays/{short}.jpg",
            "difference": f"differences/{short}.jpg",
            "landmarks": f"landmarks/{short}.jpg",
        }
        for name, relative in image_refs.items():
            artifacts[relative] = images[name]
        report_rows.append({
            "candidate_pair_id": pair_id,
            "binary_image_path": human["binary_image_path"],
            "ham_candidate_path": human["candidate_path"],
            "source_partition": human["source_split"],
            "ham_image_id": ham_id,
            "ham_lesion_id": ham["lesion_id"],
            "ham_dx": ham["dx"],
            "ham_dx_type": ham["dx_type"],
            "binary_source_image_id": "",
            "binary_patient_id": "",
            "original_phash_distance": human["phash_distance"],
            "original_dhash_distance": human["dhash_distance"],
            "original_pixel_mae_8bit": human["pixel_mae"],
            "original_pixel_correlation": human["pixel_correlation"],
            "geometric_method": geometric["method"],
            "candidate_view": geometric["candidate_view"],
            "keypoints_binary": geometric["keypoints_binary"],
            "keypoints_ham": geometric["keypoints_candidate"],
            "mutual_matches": geometric["mutual_matches"],
            "inlier_count": geometric["inlier_count"],
            "inlier_ratio": geometric["inlier_ratio"],
            "median_reprojection_error_px": geometric["median_reprojection_error_px"],
            **metrics,
            "lesion_structure_match_status": "not_independently_verified_no_lesion_mask",
            "overlay_reference": (output / image_refs["overlay"]).as_posix(),
            "difference_reference": (output / image_refs["difference"]).as_posix(),
            "landmark_reference": (output / image_refs["landmarks"]).as_posix(),
            "original_binary_reference": human["binary_image_path"],
            "original_ham_reference": human["candidate_path"],
            "prior_human_decision": human["reviewer_decision"],
            "prior_human_timestamp_utc": human["review_timestamp_utc"],
            "identity_conclusion_status": "REQUIRES_REVIEW" if metrics["transformation_plausibility"] == "plausible_geometric_mapping" else "INSUFFICIENT_EVIDENCE",
            "review_requirement": "Independent original-resolution review of lesion landmarks, vessels/pigment and artifacts; reconcile prior decision if any; do not infer from score alone.",
            "geometric_evidence_reference": GEOMETRY.as_posix(),
            "human_ledger_reference": LEDGER.as_posix(),
        })
        if index % 20 == 0:
            print(f"Stage 3G aligned evidence {index}/83", flush=True)
    blind_rows = []
    for row in validation:
        source, other = row["source_image_path"], row["comparison_image_path"]
        case_id = "BV-" + hashlib.sha256((source + "\n" + other).encode()).hexdigest()[:16]
        blind_rows.append({"blind_case_id": case_id, "source_image_path": source,
                           "comparison_image_path": other, "partition": row["partition"],
                           "metadata_relation_status": row["truth_status"],
                           "review_status": "unreviewed", "independent_reviewer_1": "",
                           "independent_reviewer_2": "", "adjudication_status": "pending"})
    blind_rows.sort(key=lambda row: hashlib.sha256(("blind_order_v1:" + row["blind_case_id"]).encode()).hexdigest())
    if any(sha256(root / path) != original for path, original in source_hashes.items()):
        raise ValueError("Source evidence changed during Stage 3G")
    destination.mkdir(parents=True, exist_ok=True)
    for folder in ("overlays", "differences", "landmarks"):
        (destination / folder).mkdir(exist_ok=True)
    for relative, content in artifacts.items():
        (destination / relative).write_bytes(content)
    write_rows(destination / PAIR_FILE, FIELDS, report_rows)
    write_rows(destination / BLIND_QUEUE_FILE, BLIND_FIELDS, blind_rows)
    summary = {"strong_pairs_investigated": len(report_rows),
               "identity_status_counts": dict(Counter(r["identity_conclusion_status"] for r in report_rows)),
               "transformation_plausibility": dict(Counter(r["transformation_plausibility"] for r in report_rows)),
               "source_test_pairs": sum(r["source_partition"] == "test" for r in report_rows),
               "prior_human_same_photo_decisions": sum(r["prior_human_decision"] == "SAME_PHOTO" for r in report_rows),
               "independently_verified_negative_pairs": 0,
               "detector_error_metrics_available": False,
               "source_evidence_sha256": source_hashes,
               "human_decision_ledger_unchanged": True,
               "exclusions_applied": False}
    atomic_text(destination / SUMMARY_FILE, json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
