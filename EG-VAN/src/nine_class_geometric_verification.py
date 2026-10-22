#!/usr/bin/env python3
"""Independent geometric evidence for Stage 3F; never edits review decisions."""

from __future__ import annotations

import csv
import argparse
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from nine_class_benign_review import LEDGER, QUEUE, ROOT, read_csv, sha256, atomic_text


OUTPUT = Path("analysis/nine_class_recovery/geometric_pair_evidence.csv")
SUMMARY = Path("analysis/nine_class_recovery/geometric_verification_summary.json")
VALIDATION = Path("analysis/nine_class_recovery/geometric_validation_manifest.csv")
VALIDATION_SUMMARY = Path("analysis/nine_class_recovery/geometric_validation_summary.json")
MAX_SIDE = 800
MIN_FEATURES = 8
MIN_GOOD_MATCHES = 8
RANSAC_PIXELS = 3.0
ORB_RATIO = 0.75
SIFT_RATIO = 0.70
FIELDS = ("candidate_pair_id", "binary_image_path", "candidate_path", "method",
          "binary_size", "candidate_size", "candidate_view", "keypoints_binary", "keypoints_candidate",
          "ratio_matches", "mutual_matches", "inlier_count", "inlier_ratio",
          "median_reprojection_error_px", "homography", "geometry_status",
          "failure_reason", "automated_evidence_category", "evidence_explanation",
          "landmark_visualization_available", "source_queue_sha256", "source_ledger_sha256_at_run")
VALIDATION_FIELDS = ("partition", "source_image_path", "comparison_image_path",
                     "construction", "truth_status", "source_sha256", "comparison_sha256",
                     "source_lesion_id", "comparison_lesion_id", "phash_distance",
                     "method", "candidate_view", "keypoints_binary", "keypoints_candidate", "mutual_matches",
                     "inlier_count", "inlier_ratio", "geometry_status", "failure_reason")


def load_gray(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Cannot decode {path}")
    return image


def scaled(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(1.0, MAX_SIDE / max(height, width))
    if scale == 1.0:
        return image
    return cv2.resize(image, (round(width * scale), round(height * scale)),
                      interpolation=cv2.INTER_AREA)


def _feature_match(left: np.ndarray, right: np.ndarray, method: str) -> dict:
    if method == "ORB":
        detector = cv2.ORB_create(nfeatures=3000, scaleFactor=1.2, nlevels=8,
                                  edgeThreshold=15, fastThreshold=10)
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        ratio_limit = ORB_RATIO
    else:
        detector = cv2.SIFT_create(nfeatures=3000)
        matcher = cv2.BFMatcher(cv2.NORM_L2)
        ratio_limit = SIFT_RATIO
    key_left, desc_left = detector.detectAndCompute(left, None)
    key_right, desc_right = detector.detectAndCompute(right, None)
    result = {"method": method, "keypoints_binary": len(key_left),
              "keypoints_candidate": len(key_right), "ratio_matches": 0,
              "mutual_matches": 0, "inlier_count": 0, "inlier_ratio": 0.0,
              "median_reprojection_error_px": "", "homography": "",
              "geometry_status": "unreliable", "failure_reason": "",
              "points_binary": [], "points_candidate": []}
    if desc_left is None or desc_right is None or min(len(key_left), len(key_right)) < MIN_FEATURES:
        result["failure_reason"] = "too_few_keypoints"
        return result

    def ratio_pairs(a, b):
        pairs = matcher.knnMatch(a, b, k=2)
        return {m.queryIdx: m.trainIdx for candidates in pairs if len(candidates) == 2
                for m, n in [candidates] if m.distance < ratio_limit * n.distance}

    forward = ratio_pairs(desc_left, desc_right)
    reverse = ratio_pairs(desc_right, desc_left)
    matches = sorted((i, j) for i, j in forward.items() if reverse.get(j) == i)
    result["ratio_matches"] = len(forward)
    result["mutual_matches"] = len(matches)
    if len(matches) < MIN_GOOD_MATCHES:
        result["failure_reason"] = "too_few_mutual_matches"
        return result
    a = np.float32([key_left[i].pt for i, _ in matches]).reshape(-1, 1, 2)
    b = np.float32([key_right[j].pt for _, j in matches]).reshape(-1, 1, 2)
    transform, mask = cv2.findHomography(b, a, cv2.RANSAC, RANSAC_PIXELS,
                                         maxIters=5000, confidence=0.995)
    if transform is None or mask is None or not np.isfinite(transform).all():
        result["failure_reason"] = "ransac_failed"
        return result
    inliers = mask.ravel().astype(bool)
    count = int(inliers.sum())
    predicted = cv2.perspectiveTransform(b[inliers], transform) if count else np.empty((0, 1, 2))
    error = float(np.median(np.linalg.norm(predicted.reshape(-1, 2) -
                                           a[inliers].reshape(-1, 2), axis=1))) if count else float("inf")
    result.update(inlier_count=count, inlier_ratio=round(count / len(matches), 6),
                  median_reprojection_error_px=round(error, 4) if np.isfinite(error) else "",
                  homography=json.dumps(np.round(transform, 7).tolist(), separators=(",", ":")))
    if count < 12 or count / len(matches) < 0.5 or error > 2.0:
        result["failure_reason"] = "weak_consensus"
        return result
    # A plausible registration must have a nondegenerate mapped field of view.
    height, width = right.shape
    corners = np.float32([[0, 0], [width, 0], [width, height], [0, height]]).reshape(-1, 1, 2)
    mapped = cv2.perspectiveTransform(corners, transform).reshape(-1, 2)
    area = abs(float(cv2.contourArea(mapped.astype(np.float32))))
    if not np.isfinite(mapped).all() or area < 0.02 * left.shape[0] * left.shape[1]:
        result["failure_reason"] = "implausible_transform_area"
        return result
    result["geometry_status"] = "coherent"
    result["points_binary"] = a[inliers].reshape(-1, 2).round(2).tolist()
    result["points_candidate"] = b[inliers].reshape(-1, 2).round(2).tolist()
    return result


def geometric_evidence(binary: np.ndarray, candidate: np.ndarray) -> dict:
    left, right = scaled(binary), scaled(candidate)
    views = [("native_aspect", right)]
    if abs(left.shape[1] / left.shape[0] - right.shape[1] / right.shape[0]) > .01:
        # Fanconic's square image may be a nonuniformly resized HAM photo.
        # Record this hypothesis explicitly rather than hiding it in matching.
        normalized = cv2.resize(right, (left.shape[1], left.shape[0]),
                                interpolation=cv2.INTER_AREA)
        views.insert(0, ("aspect_normalized_to_binary", normalized))
    result = None
    for view_name, view in views:
        orb = _feature_match(left, view, "ORB")
        candidate_result = orb
        if orb["geometry_status"] != "coherent":
            sift = _feature_match(left, view, "SIFT")
            if sift["geometry_status"] == "coherent" or sift["inlier_count"] > orb["inlier_count"]:
                candidate_result = sift
        candidate_result["candidate_view"] = view_name
        if result is None or candidate_result["geometry_status"] == "coherent" or \
                candidate_result["inlier_count"] > result["inlier_count"]:
            result = candidate_result
        if result["geometry_status"] == "coherent":
            break
    result["binary_size"] = f"{binary.shape[1]}x{binary.shape[0]}"
    result["candidate_size"] = f"{candidate.shape[1]}x{candidate.shape[0]}"
    return result


def category(row: dict, geometry: dict) -> tuple[str, str]:
    # There is no independent negative calibration for a high-confidence
    # identity/nonidentity classifier. Geometry only prioritizes human review.
    if geometry["geometry_status"] == "coherent":
        return ("NEEDS_HUMAN_REVIEW",
                "Coherent local-feature homography; supports common image content, not independently validated photo identity. Review original images and visualized landmarks.")
    if float(row["pixel_correlation"]) >= 0.995 and float(row["pixel_mae"]) <= 5:
        return ("NEEDS_HUMAN_REVIEW",
                "Strong unregistered pixel similarity, but geometric verification is unreliable. Review originals; failure may reflect low texture or preprocessing.")
    return ("INSUFFICIENT_EVIDENCE",
            "No reliable geometric consensus and no strong aligned-pixel agreement. This is not evidence of distinct lesions or photographs.")


def render_landmarks(root: Path, evidence_row: dict, max_lines: int = 24) -> bytes:
    """Recompute and render inliers on demand; visualization is never an image source."""
    left = scaled(load_gray(root / evidence_row["binary_image_path"]))
    right = scaled(load_gray(root / evidence_row["candidate_path"]))
    geometry = geometric_evidence(left, right)
    if geometry["geometry_status"] != "coherent":
        raise ValueError("No coherent landmarks available for this pair")
    if geometry["method"] != evidence_row["method"] or str(geometry["inlier_count"]) != evidence_row["inlier_count"]:
        raise ValueError("Geometric evidence changed; rerun the audit")
    if geometry["candidate_view"] == "aspect_normalized_to_binary":
        right = cv2.resize(right, (left.shape[1], left.shape[0]), interpolation=cv2.INTER_AREA)
    h = max(left.shape[0], right.shape[0])
    panel = np.full((h, left.shape[1] + right.shape[1], 3), 245, np.uint8)
    panel[:left.shape[0], :left.shape[1]] = cv2.cvtColor(left, cv2.COLOR_GRAY2BGR)
    panel[:right.shape[0], left.shape[1]:] = cv2.cvtColor(right, cv2.COLOR_GRAY2BGR)
    points = list(zip(geometry["points_binary"], geometry["points_candidate"]))
    for a, b in points[:max_lines]:
        p = tuple(map(int, a)); q = (int(b[0] + left.shape[1]), int(b[1]))
        cv2.line(panel, p, q, (0, 210, 40), 1, cv2.LINE_AA)
        cv2.circle(panel, p, 3, (255, 80, 0), -1, cv2.LINE_AA)
        cv2.circle(panel, q, 3, (255, 80, 0), -1, cv2.LINE_AA)
    ok, encoded = cv2.imencode(".jpg", panel, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ValueError("Cannot encode visualization")
    return encoded.tobytes()


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({key: row.get(key, "") for key in fields} for row in rows)
    atomic_text(path, buffer.getvalue())


def _synthetic(original: np.ndarray, kind: str) -> np.ndarray:
    if kind == "byte_copy":
        return original.copy()
    if kind == "resized_jpeg_q75":
        resized = cv2.resize(original, (224, 224), interpolation=cv2.INTER_AREA)
        ok, encoded = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not ok:
            raise ValueError("Cannot generate in-memory JPEG control")
        return cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    if kind == "rotated_90":
        return cv2.rotate(original, cv2.ROTATE_90_CLOCKWISE)
    if kind == "center_crop_80pct":
        h, w = original.shape
        y0, x0 = round(h * .1), round(w * .1)
        return original[y0:h-y0, x0:w-x0]
    raise ValueError(kind)


def _phash_distance(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


def run_validation(root: Path = ROOT, verify_existing: bool = False) -> dict:
    """Controlled positives and provisional metadata-based hard negatives.

    Different HAM lesion IDs are not accepted as independently confirmed
    negative ground truth; accuracy metrics remain unavailable.
    """
    root = root.resolve()
    output = root / VALIDATION
    if output.exists() and not verify_existing:
        raise FileExistsError(f"Preserving existing validation evidence: {output}")
    if verify_existing and not output.exists():
        raise FileNotFoundError(output)
    metadata_path = root / "data/raw/HAM10000_metadata.csv"
    fingerprints_path = root / "analysis/nine_class_similarity/fingerprints.csv"
    metadata = {r["image_id"]: r for r in read_csv(metadata_path)}
    fingerprints = [r for r in read_csv(fingerprints_path)
                    if r["image_path"].startswith("data/raw/HAM10000_images_part_")]
    by_image_id = {Path(r["image_path"]).stem: r for r in fingerprints}
    if len(by_image_id) != 10015:
        raise ValueError("HAM fingerprint list changed")
    # Source selection is deterministic and independent of geometric scores.
    ranked = sorted(metadata, key=lambda image_id: hashlib.sha256(
        ("stage3f_validation_v1:" + image_id).encode()).hexdigest())
    chosen, lesions = [], set()
    for image_id in ranked:
        lesion_id = metadata[image_id]["lesion_id"]
        if lesion_id in lesions:
            continue
        chosen.append(image_id)
        lesions.add(lesion_id)
        if len(chosen) == 40:
            break
    if len(chosen) != 40:
        raise ValueError("Insufficient distinct HAM lesion IDs")
    rows = []
    for source_index, image_id in enumerate(chosen):
        partition = "development" if source_index < 20 else "held_out"
        item = by_image_id[image_id]
        source_path = item["image_path"]
        source = load_gray(root / source_path)
        source_hash = sha256(root / source_path)
        for kind in ("byte_copy", "resized_jpeg_q75", "rotated_90", "center_crop_80pct"):
            transformed = _synthetic(source, kind)
            geometry = geometric_evidence(source, transformed)
            rows.append({"partition": partition, "source_image_path": source_path,
                         "comparison_image_path": "", "construction": kind,
                         "truth_status": "controlled_same_source_photo",
                         "source_sha256": source_hash,
                         "comparison_sha256": source_hash if kind == "byte_copy" else "",
                         "source_lesion_id": metadata[image_id]["lesion_id"],
                         "comparison_lesion_id": metadata[image_id]["lesion_id"],
                         "phash_distance": "",
                         **{key: geometry.get(key, "") for key in VALIDATION_FIELDS if key in geometry}})
        # Closest same-diagnosis, different-lesion pHash neighbor is a difficult
        # *candidate* negative. Metadata alone cannot prove distinct photos.
        candidates = (r for r in fingerprints
                      if Path(r["image_path"]).stem != image_id
                      and metadata[Path(r["image_path"]).stem]["dx"] == metadata[image_id]["dx"]
                      and metadata[Path(r["image_path"]).stem]["lesion_id"] != metadata[image_id]["lesion_id"])
        neighbor = min(candidates, key=lambda r: (
            _phash_distance(item["phash64"], r["phash64"]), r["image_path"]))
        neighbor_path = neighbor["image_path"]
        geometry = geometric_evidence(source, load_gray(root / neighbor_path))
        rows.append({"partition": partition, "source_image_path": source_path,
                     "comparison_image_path": neighbor_path,
                     "construction": "similar_hash_different_metadata_lesion_id",
                     "truth_status": "provisional_distinct_requires_independent_verification",
                     "source_sha256": source_hash,
                     "comparison_sha256": sha256(root / neighbor_path),
                     "source_lesion_id": metadata[image_id]["lesion_id"],
                     "comparison_lesion_id": metadata[Path(neighbor_path).stem]["lesion_id"],
                     "phash_distance": _phash_distance(item["phash64"], neighbor["phash64"]),
                     **{key: geometry.get(key, "") for key in VALIDATION_FIELDS if key in geometry}})
    # This pair is the audited SHA-256-identical local source-file control.
    exact_a = "data/isic/data/train/malignant/768.jpg"
    exact_b = "data/isic/data/train/malignant/769.jpg"
    exact_hash = sha256(root / exact_a)
    if exact_hash != sha256(root / exact_b):
        raise ValueError("Known exact duplicate source control changed")
    geometry = geometric_evidence(load_gray(root / exact_a), load_gray(root / exact_b))
    rows.append({"partition": "positive_reference", "source_image_path": exact_a,
                 "comparison_image_path": exact_b, "construction": "source_file_sha256_identical",
                 "truth_status": "verified_byte_identical_files",
                 "source_sha256": exact_hash, "comparison_sha256": exact_hash,
                 "source_lesion_id": "", "comparison_lesion_id": "", "phash_distance": 0,
                 **{key: geometry.get(key, "") for key in VALIDATION_FIELDS if key in geometry}})
    if verify_existing:
        expected = [{key: str(row.get(key, "")) for key in VALIDATION_FIELDS} for row in rows]
        if read_csv(output) != expected:
            raise ValueError("Saved validation manifest differs from recomputed measurements")
    else:
        write_csv(output, VALIDATION_FIELDS, rows)
    report = {"source_images": 40, "development_source_images": 20,
              "held_out_source_images": 20,
              "controlled_positive_pairs": 160,
              "verified_byte_identical_file_pairs": 1,
              "provisional_hard_negative_pairs": 40,
              "independently_verified_negative_pairs": 0,
              "source_metadata_sha256": sha256(metadata_path),
              "source_fingerprints_sha256": sha256(fingerprints_path),
              "held_out_controlled_positive_geometry_by_transform": {
                  kind: {"coherent": sum(r["partition"] == "held_out" and
                                           r["construction"] == kind and
                                           r["geometry_status"] == "coherent" for r in rows),
                         "total": 20}
                  for kind in ("byte_copy", "resized_jpeg_q75", "rotated_90", "center_crop_80pct")},
              "precision": None, "recall": None,
              "false_positive_rate": None, "false_negative_rate": None,
              "reason_accuracy_unavailable": "No independently verified difficult negative set; geometric coherence is a triage aid, not a validated identity classifier."}
    if verify_existing:
        if json.loads((root / VALIDATION_SUMMARY).read_text(encoding="utf-8")) != report:
            raise ValueError("Saved validation summary differs from recomputed measurements")
    else:
        atomic_text(root / VALIDATION_SUMMARY, json.dumps(report, indent=2) + "\n")
    return report


def run(root: Path = ROOT, verify_existing: bool = False) -> dict:
    root = root.resolve()
    ledger_path, queue_path = root / LEDGER, root / QUEUE
    ledger_hash, queue_hash = sha256(ledger_path), sha256(queue_path)
    ledger = read_csv(ledger_path)
    if len(ledger) != 429 or len({row["candidate_pair_id"] for row in ledger}) != 429:
        raise ValueError("Expected 429 unique Stage 3E pair IDs")
    rows = []
    for index, row in enumerate(ledger, 1):
        a = load_gray(root / row["binary_image_path"])
        b = load_gray(root / row["candidate_path"])
        geometry = geometric_evidence(a, b)
        label, explanation = category(row, geometry)
        rows.append({"candidate_pair_id": row["candidate_pair_id"],
                     "binary_image_path": row["binary_image_path"],
                     "candidate_path": row["candidate_path"],
                     **{key: geometry.get(key, "") for key in FIELDS if key in geometry},
                     "automated_evidence_category": label,
                     "evidence_explanation": explanation,
                     "landmark_visualization_available": str(geometry["geometry_status"] == "coherent").lower(),
                     "source_queue_sha256": queue_hash,
                     "source_ledger_sha256_at_run": ledger_hash})
        if index % 50 == 0:
            print(f"Geometric evidence {index}/429", flush=True)
    if sha256(queue_path) != queue_hash:
        raise ValueError("Source queue changed during audit")
    # The review ledger may be edited by a person while this calculation runs.
    # Pair IDs and paths are frozen; decision fields are intentionally ignored.
    latest = read_csv(ledger_path)
    if [(r["candidate_pair_id"], r["binary_image_path"], r["candidate_path"]) for r in latest] != [
            (r["candidate_pair_id"], r["binary_image_path"], r["candidate_path"]) for r in ledger]:
        raise ValueError("Review pair list changed during geometric audit")
    out = root / OUTPUT
    if out.exists() and not verify_existing:
        raise FileExistsError(f"Preserving existing evidence: {out}")
    if verify_existing:
        if not out.exists():
            raise FileNotFoundError(out)
        frozen_fields = [field for field in FIELDS if field != "source_ledger_sha256_at_run"]
        expected = [{field: str(row.get(field, "")) for field in frozen_fields} for row in rows]
        actual = [{field: row[field] for field in frozen_fields} for row in read_csv(out)]
        if actual != expected:
            raise ValueError("Saved geometric pair evidence differs from recomputed measurements")
    else:
        write_csv(out, FIELDS, rows)
    counts = Counter(row["automated_evidence_category"] for row in rows)
    methods = Counter(row["method"] for row in rows)
    status = Counter(row["geometry_status"] for row in rows)
    summary = {"pairs": len(rows), "automated_categories": dict(counts),
               "geometry_status": dict(status), "methods": dict(methods),
               "source_queue_sha256": queue_hash, "source_ledger_pair_list_hash": hashlib.sha256(
                   "\n".join(r["candidate_pair_id"] for r in ledger).encode()).hexdigest(),
               "human_decisions_not_modified": True,
               "detector_precision_recall_not_validated": True}
    if verify_existing:
        if json.loads((root / SUMMARY).read_text(encoding="utf-8")) != summary:
            raise ValueError("Saved geometric summary differs from recomputed measurements")
    else:
        atomic_text(root / SUMMARY, json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Recompute and compare existing evidence without writing")
    arguments = parser.parse_args()
    print(json.dumps({"validation": run_validation(verify_existing=arguments.verify),
                      "pair_audit": run(verify_existing=arguments.verify)}, indent=2))
