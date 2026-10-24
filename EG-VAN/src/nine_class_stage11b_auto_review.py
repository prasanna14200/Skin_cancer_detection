"""Recheck only Stage 11A's 19 primary and 101 linked photographic candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from nine_class_stage4 import ROOT

PACKAGE = Path("analysis/nine_class_stage11a")
OUTPUT = Path("analysis/nine_class_stage11b")
AI = Path("analysis/nine_class_recovery/stage3i/ai_pair_review.csv")
GEOMETRY = Path("analysis/nine_class_recovery/geometric_pair_evidence.csv")
STRONG = Path("analysis/nine_class_recovery/stage3g/strong_pair_identity_evidence.csv")
INVENTORY = Path("analysis/nine_class_stage4/nine_class_source_manifest.csv")
FIELDS = ("review_id", "candidate_pair_id", "relation_scope", "binary_image_path", "ham_candidate_path",
          "binary_sha256", "ham_sha256", "exact_sha256_match", "phash_distance", "dhash_distance",
          "prior_pixel_correlation", "prior_pixel_mae_8bit", "geometric_method", "geometric_status",
          "geometric_inliers", "geometric_inlier_ratio", "geometric_failure_reason",
          "stage3g_transform_plausibility", "stage3g_aligned_correlation", "stage3g_central_inlier_fraction",
          "stage3g_inlier_hull_fraction", "crop_aware_correlation", "crop_view", "central_structure_correlation",
          "surrounding_field_correlation", "automated_category", "decision_rationale", "method_limitations",
          "prior_ai_assessment_for_analyst_only", "human_decision_used", "approved_eligible")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_corr(left: np.ndarray, right: np.ndarray) -> float | None:
    a, b = left.astype(np.float32).ravel(), right.astype(np.float32).ravel()
    if len(a) < 10 or np.std(a) < 1e-7 or np.std(b) < 1e-7:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def crop_aware_evidence(binary: np.ndarray, ham: np.ndarray) -> dict:
    """Best unregistered grayscale match under bounded central HAM crop/aspect hypotheses."""
    if binary.ndim != 2 or ham.ndim != 2 or min(*binary.shape, *ham.shape) < 20:
        raise ValueError("Two nonempty grayscale photographs required")
    h, w = binary.shape
    best = {"crop_aware_correlation": -2.0, "crop_view": "", "central_structure_correlation": None,
            "surrounding_field_correlation": None}
    for fraction in (1.0, .9, .8):
        yh, xw = max(20, round(ham.shape[0] * fraction)), max(20, round(ham.shape[1] * fraction))
        y0, x0 = (ham.shape[0] - yh) // 2, (ham.shape[1] - xw) // 2
        crop = ham[y0:y0 + yh, x0:x0 + xw]
        hypotheses = [("stretched", crop)]
        side = min(crop.shape)
        square = crop[(crop.shape[0] - side)//2:(crop.shape[0] + side)//2,
                      (crop.shape[1] - side)//2:(crop.shape[1] + side)//2]
        hypotheses.append(("central_square", square))
        for view, image in hypotheses:
            resized = cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA)
            correlation = safe_corr(binary, resized)
            if correlation is None or correlation <= best["crop_aware_correlation"]:
                continue
            center = np.zeros((h, w), dtype=bool)
            center[round(.2*h):round(.8*h), round(.2*w):round(.8*w)] = True
            # Center/outer scores are field-layout proxies; no lesion mask exists.
            best = {"crop_aware_correlation": correlation, "crop_view": f"{fraction:g}:{view}",
                    "central_structure_correlation": safe_corr(binary[center], resized[center]),
                    "surrounding_field_correlation": safe_corr(binary[~center], resized[~center])}
    if best["crop_aware_correlation"] == -2:
        best["crop_aware_correlation"] = None
    return best


def automatic_category(row: dict) -> tuple[str, str]:
    """Heuristic triage, not an independently calibrated identity classifier."""
    if row["exact_sha256_match"]:
        return "AUTO_SAME_PHOTO", "Byte-identical source images (SHA-256)."
    aligned = row["stage3g_aligned_correlation"]
    if (row["geometric_status"] == "coherent" and row["stage3g_transform_plausibility"] == "plausible_geometric_mapping"
        and aligned is not None and aligned >= .985 and row["geometric_inliers"] >= 12
        and row["geometric_inlier_ratio"] >= .5 and row["crop_aware_correlation"] is not None
        and row["crop_aware_correlation"] >= .9):
        return ("AUTO_SAME_PHOTO", "Coherent plausible homography, high aligned agreement and an independent crop/aspect view agree; photographic-landmark support is automated only.")
    if (row["geometric_status"] != "coherent" and row["phash_distance"] >= 18
        and row["dhash_distance"] >= 18 and row["prior_pixel_correlation"] < .8
        and row["crop_aware_correlation"] is not None and row["crop_aware_correlation"] < .8
        and row["central_structure_correlation"] is not None and row["central_structure_correlation"] < .8
        and row["surrounding_field_correlation"] is not None and row["surrounding_field_correlation"] < .8):
        return ("AUTO_DISTINCT_PHOTO", "Both perceptual hashes, direct pixels, bounded crop views and central/outer field proxies disagree; no coherent geometry. This does not establish different lesions or patients.")
    return ("AUTO_UNCERTAIN", "Evidence is mixed or the bounded registration cannot resolve photographic identity; failed geometry is not proof of distinctness.")


def evidence_row(root: Path, mapping: dict, candidate: dict, prior: dict, geometry: dict,
                 strong: dict | None, inventory: dict, image_cache: dict) -> dict:
    binary, ham = candidate["binary_image_path"], candidate["ham_candidate_path"]
    if prior["binary_image_path"] != binary or prior["candidate_path"] != ham:
        raise ValueError("Stage 3I pair mapping differs")
    for path, digest in ((binary, prior["original_binary_sha256"]), (ham, prior["original_candidate_sha256"])):
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file() or inventory[path]["sha256"] != digest or sha256(resolved) != digest:
            raise ValueError(f"Source image or inventory hash differs: {path}")
        if path not in image_cache:
            image_cache[path] = cv2.imread(str(resolved), cv2.IMREAD_GRAYSCALE)
        if image_cache[path] is None:
            raise ValueError(f"Cannot decode {path}")
    crop = crop_aware_evidence(image_cache[binary], image_cache[ham])
    def num(value: str, kind=float):
        return kind(value) if value not in (None, "") else None
    result = {"review_id": mapping["review_id"], "candidate_pair_id": candidate["candidate_pair_id"],
              "relation_scope": candidate["relation_scope"], "binary_image_path": binary,
              "ham_candidate_path": ham, "binary_sha256": prior["original_binary_sha256"],
              "ham_sha256": prior["original_candidate_sha256"],
              "exact_sha256_match": prior["original_binary_sha256"] == prior["original_candidate_sha256"],
              "phash_distance": num(prior["phash_distance"], int), "dhash_distance": num(prior["dhash_distance"], int),
              "prior_pixel_correlation": num(prior["pixel_correlation"]),
              "prior_pixel_mae_8bit": num(prior["pixel_mae_8bit"]),
              "geometric_method": geometry["method"], "geometric_status": geometry["geometry_status"],
              "geometric_inliers": num(geometry["inlier_count"], int),
              "geometric_inlier_ratio": num(geometry["inlier_ratio"]),
              "geometric_failure_reason": geometry["failure_reason"],
              "stage3g_transform_plausibility": strong["transformation_plausibility"] if strong else "NOT_ASSESSED",
              "stage3g_aligned_correlation": num(strong["aligned_grayscale_correlation"]) if strong else None,
              "stage3g_central_inlier_fraction": num(strong["central_inlier_fraction"]) if strong else None,
              "stage3g_inlier_hull_fraction": num(strong["inlier_hull_fraction"]) if strong else None,
              **crop, "method_limitations": "Crop search tests six center/aspect hypotheses only; center/outer fields are not lesion masks; geometry and Stage3G come from earlier nonblind audit; no independently validated classifier error rate.",
              "prior_ai_assessment_for_analyst_only": prior["ai_assessment"],
              "human_decision_used": False, "approved_eligible": False}
    result["automated_category"], result["decision_rationale"] = automatic_category(result)
    return result


def summarize(primary: list[dict], additional: list[dict], inventory_rows: list[dict]) -> dict:
    def counts(rows):
        return dict(Counter(r["automated_category"] for r in rows))
    # Proposals are never applied here. Upper bounds are numerical, not eligible cohorts.
    proposed_train = sum(r["class_name"] == "BENIGN" and r["source_split"] == "train" and
                         r["provisional_eligibility_status"] != "PRIOR_PROPOSED_EXCLUSION_NOT_APPROVED" for r in inventory_rows)
    proposed_test = sum(r["class_name"] == "BENIGN" and r["source_split"] == "test" and
                        r["provisional_eligibility_status"] != "PRIOR_PROPOSED_EXCLUSION_NOT_APPROVED" for r in inventory_rows)
    by_binary = defaultdict(list)
    for row in primary + additional:
        by_binary[row["binary_image_path"]].append(row)
    record_bounds = {path: {"automated_same_pair_count": sum(r["automated_category"] == "AUTO_SAME_PHOTO" for r in rows),
                            "automated_uncertain_pair_count": sum(r["automated_category"] == "AUTO_UNCERTAIN" for r in rows),
                            "automated_distinct_pair_count": sum(r["automated_category"] == "AUTO_DISTINCT_PHOTO" for r in rows),
                            "potentially_usable_if_all_automated_same_and_uncertain_relations_are_independently_cleared":
                                not any(r["automated_category"] != "AUTO_DISTINCT_PHOTO" for r in rows),
                            "approved_eligible": False} for path, rows in by_binary.items()}
    return {"primary_pairs": len(primary), "additional_relations": len(additional),
            "primary_automated_categories": counts(primary), "additional_automated_categories": counts(additional),
            "exact_sha256_pairs": sum(r["exact_sha256_match"] for r in primary + additional),
            "benign_post_proposal_train_upper_bound": proposed_train,
            "benign_post_proposal_protected_test_upper_bound": proposed_test,
            "protected_test_records_without_auto_same_or_auto_uncertain_relations": sum(v["potentially_usable_if_all_automated_same_and_uncertain_relations_are_independently_cleared"] for v in record_bounds.values()),
            "approved_benign_train": 0, "approved_benign_test": 0,
            "record_level_conditional_bounds": record_bounds,
            "human_review_decisions_changed": False, "dataset_approval_created": False,
            "final_split_created": False, "full_nine_class_training_ready": False}


def run(root: Path = ROOT, output: Path = OUTPUT) -> dict:
    root = root.resolve()
    destination = (root / output).resolve()
    if not destination.is_relative_to(root / OUTPUT) or destination.exists():
        raise FileExistsError("New Stage 11B output directory required")
    mapping = read_csv(root / PACKAGE / "review_id_mapping.csv")
    related = read_csv(root / PACKAGE / "additional_candidate_relations.csv")
    ledger = read_csv(root / PACKAGE / "decision_ledger.csv")
    if len(mapping) != 19 or len(related) != 101 or any(r["reviewer_decision"] for r in ledger):
        raise ValueError("Stage 11A pair set or blank human ledger changed")
    prior = {r["candidate_pair_id"]: r for r in read_csv(root / AI)}
    geometry = {r["candidate_pair_id"]: r for r in read_csv(root / GEOMETRY)}
    strong = {r["candidate_pair_id"]: r for r in read_csv(root / STRONG)}
    inventory_rows = read_csv(root / INVENTORY)
    inventory = {r["image_path"]: r for r in inventory_rows}
    originals = {r["review_id"]: r for r in mapping}
    candidates = [{"review_id": r["review_id"], "candidate_pair_id": r["candidate_pair_id"],
                   "binary_image_path": r["binary_image_path"], "ham_candidate_path": r["ham_image_path"],
                   "relation_scope": "PRIMARY_PROTECTED_TEST"} for r in mapping]
    candidates += [{**r, "relation_scope": "ADDITIONAL_PROTECTED_TEST"} for r in related]
    if len({r["candidate_pair_id"] for r in candidates}) != 120:
        raise ValueError("Duplicate or missing candidate pair ID")
    cache = {}
    results = []
    source_paths = (root / PACKAGE / "review_id_mapping.csv", root / PACKAGE / "additional_candidate_relations.csv",
                    root / PACKAGE / "decision_ledger.csv", root / AI, root / GEOMETRY, root / STRONG, root / INVENTORY)
    frozen_hashes = {str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in source_paths}
    for candidate in candidates:
        pair_id = candidate["candidate_pair_id"]
        if pair_id not in prior or pair_id not in geometry or candidate["review_id"] not in originals:
            raise ValueError(f"Missing frozen relation evidence: {pair_id}")
        results.append(evidence_row(root, originals[candidate["review_id"]], candidate, prior[pair_id],
                                    geometry[pair_id], strong.get(pair_id), inventory, cache))
    primary = [r for r in results if r["relation_scope"] == "PRIMARY_PROTECTED_TEST"]
    additional = [r for r in results if r["relation_scope"] == "ADDITIONAL_PROTECTED_TEST"]
    summary = summarize(primary, additional, inventory_rows)
    summary["source_evidence_sha256"] = frozen_hashes
    summary["method_version"] = "stage11b_bounded_auto_v1"
    summary["calibration_status"] = "NO_INDEPENDENT_HELD_OUT_IDENTITY_GROUND_TRUTH; categories are heuristic triage"
    destination.mkdir(parents=True, exist_ok=False)
    for name, rows in (("primary_19_auto_evidence.csv", primary), ("additional_101_auto_evidence.csv", additional)):
        with (destination / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    (destination / "automated_review_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if any(sha256(root / path) != digest for path, digest in frozen_hashes.items()):
        raise ValueError("Source evidence changed during bounded auto review")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    summary = run(args.root, args.output)
    print(json.dumps({key: summary[key] for key in ("primary_pairs", "additional_relations", "primary_automated_categories", "additional_automated_categories", "exact_sha256_pairs", "full_nine_class_training_ready")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
