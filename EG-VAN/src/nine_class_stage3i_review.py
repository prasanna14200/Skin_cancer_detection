#!/usr/bin/env python3
"""Freeze the Stage 3I AI visual review without changing source or human evidence.

The review-order assessments below were recorded after inspecting all 36 original-image
sheets and all seven strong-pair overlay sheets. They are AI judgments, not a
calibrated detector or independent human adjudication. This script only validates
and writes the frozen annotation; it does not perform visual inspection itself.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from nine_class_benign_review import ROOT, atomic_text, read_csv
from nine_class_stage3i_sheets import GEOMETRY, LEDGER, OUTPUT, STRONG, ordered_pairs, sha256


CONFIG_VERSION = "stage3i_ai_visual_review_v1_2026-10-19"
MODEL = "Codex, GPT-6 family (exact vision build/version not exposed)"
# After side-by-side inspection, these alternative candidates retained similar
# small-lesion appearances or conflicting pixel evidence without matching field
# landmarks. No lesion identity is inferred. Review-order IDs are frozen by the
# sheet manifest; everything outside 1..83 and this set was visibly different.
UNCERTAIN_ORDERS = frozenset({
    85, 86, 87, 88, 89, 90, 140, 141, 183, 185, 186, 187, 188, 189,
    190, 191, 200, 250, 251, 336,
})
REVIEW_FIELDS = (
    "review_order", "candidate_pair_id", "binary_image_path", "candidate_path",
    "source_split", "candidate_source", "ai_assessment", "evidence_summary",
    "visual_landmarks", "phash_distance", "dhash_distance", "pixel_mae_8bit",
    "pixel_correlation", "coarse_correlation", "geometric_method",
    "geometric_candidate_view", "geometric_inlier_count", "geometric_inlier_ratio",
    "geometric_median_reprojection_error_px", "geometric_status",
    "geometric_failure_reason", "stage3g_transformation_plausibility",
    "stage3g_aligned_correlation", "conflicting_evidence", "uncertainty_reason",
    "automated_cross_check", "cross_check_disagreement", "review_method",
    "model_name_version", "prompt_configuration_version", "review_timestamp_utc",
    "original_binary_sha256", "original_candidate_sha256", "contact_sheet_reference",
    "stage3g_overlay_reference", "stage3g_difference_reference",
    "stage3g_landmark_reference", "human_decision_used",
)
EDGE_FIELDS = ("path_a", "path_b", "evidence_tier", "basis", "candidate_pair_id")
GROUP_FIELDS = ("proposed_group_id", "member_path", "group_member_count",
                "has_prior_established_photo_edge", "has_ai_supported_photo_edge",
                "has_unresolved_suspected_edge", "group_has_source_test_image",
                "group_has_source_train_image", "recommendation")


def csv_text(fields: tuple[str, ...], rows: list[dict]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return buffer.getvalue()


def create_reviews(root: Path, timestamp: str) -> list[dict]:
    pairs = ordered_pairs(root)
    manifest = read_csv(root / OUTPUT / "sheet_manifest.csv")
    geometry = {r["candidate_pair_id"]: r for r in read_csv(root / GEOMETRY)}
    strong = {r["candidate_pair_id"]: r for r in read_csv(root / STRONG)}
    if len(manifest) != 429 or len(geometry) != 429 or len(strong) != 83:
        raise ValueError("Required review evidence count changed")
    if len(UNCERTAIN_ORDERS) != 20 or any(i <= 83 or i > 429 for i in UNCERTAIN_ORDERS):
        raise ValueError("Frozen visual uncertainty index set changed")
    reviews = []
    for n, (pair, source) in enumerate(zip(pairs, manifest, strict=True), 1):
        pair_id = pair["candidate_pair_id"]
        if int(source["review_order"]) != n or source["candidate_pair_id"] != pair_id:
            raise ValueError("Sheet order does not match frozen pair order")
        for side, field in (("binary_image_path", "binary_sha256"),
                            ("candidate_path", "candidate_sha256")):
            if pair[side] != source[side] or sha256(root / pair[side]) != source[field]:
                raise ValueError(f"Original image changed for pair {pair_id}")
        geo = geometry[pair_id]
        evidence = strong.get(pair_id)
        if n <= 83 and not evidence:
            raise ValueError("Strong-pair visual index differs from Stage 3G")
        if n <= 83:
            decision = "AI_SAME_PHOTO"
            if n == 46:
                landmarks = ("Matching diffuse lesion border, center pigment and nearby dark speck "
                             "in native originals; aligned overlay has a projective-warp artifact.")
                conflict = "Stage 3G projective strength exceeded its plausibility gate"
            elif n in {75, 77, 83}:
                landmarks = ("Matching image-wide hair/stubble arrangements and faint lesion area "
                             "in both originals and the aligned overlay; fine lesion detail is limited.")
                conflict = "Low-contrast lesion limits lesion-specific visual confirmation"
            else:
                landmarks = ("Corresponding lesion outline and internal pigment pattern, with "
                             "matching nearby skin/hair/artifact arrangement in originals and overlay.")
                conflict = "No material visual disagreement; different processing/scale remains"
            summary = ("AI visual comparison finds the same photographic field after size, crop "
                       "or compression differences; Stage 3G alignment supports this relation.")
            uncertainty = ("AI-only judgment; no independently verified Fanconic source image ID "
                           "or second human adjudication")
            cross = "ORB_RANSAC_COHERENT_PHOTO_SUPPORT"
            disagreement = "no" if n != 46 else "registration_plausibility_outlier"
        elif n in UNCERTAIN_ORDERS:
            decision = "AI_UNCERTAIN"
            landmarks = ("Broad central-lesion appearance is similar at sheet scale; no matching "
                         "lesion-specific or surrounding photographic landmark was established.")
            summary = ("Visual comparison does not establish photographic identity or safe "
                       "lesion distinctness; retain this relation as suspected overlap.")
            conflict = ("Some native-size pixel correlation is elevated despite absent "
                        "coherent geometric registration")
            uncertainty = ("Different field/scale and no verified cross-source lesion ID; "
                           "contact-sheet view cannot settle same-lesion possibility")
            cross = "GEOMETRY_UNRELIABLE_INCONCLUSIVE"
            disagreement = "unresolved_visual_vs_pixel_similarity"
        else:
            decision = "AI_DISTINCT"
            landmarks = ("Displayed lesion/field arrangements differ; no distinctive shared "
                         "lesion boundary, pigment or surrounding landmark was seen.")
            summary = ("AI visual comparison finds different photographs at the review-sheet "
                       "scale; this is not a verified patient- or lesion-distinct conclusion.")
            conflict = "No known positive photographic evidence; failed geometry alone is inconclusive"
            uncertainty = ("Patient/lesion identity is unavailable for Fanconic and small or "
                           "separately acquired same-lesion views cannot be ruled out")
            cross = "GEOMETRY_UNRELIABLE_INCONCLUSIVE"
            disagreement = "no_positive_geometric_verification"
        if n <= 83:
            method = ("AI visual inspection of numbered original-image contact sheet, Stage 3G "
                      "aligned overlay sheet, original-resolution references when needed; "
                      "metrics reviewed separately from human choice")
        else:
            method = ("AI visual inspection of numbered contact sheet rendered from both "
                      "original photographs; original paths and similarity/geometry metrics reviewed")
        reviews.append({
            "review_order": n, "candidate_pair_id": pair_id,
            "binary_image_path": pair["binary_image_path"],
            "candidate_path": pair["candidate_path"],
            "source_split": pair["source_split"], "candidate_source": pair["candidate_source"],
            "ai_assessment": decision, "evidence_summary": summary,
            "visual_landmarks": landmarks,
            "phash_distance": pair["phash_distance"],
            "dhash_distance": pair["dhash_distance"],
            "pixel_mae_8bit": pair["pixel_mae"],
            "pixel_correlation": pair["pixel_correlation"],
            "coarse_correlation": pair["coarse_correlation"],
            "geometric_method": geo["method"],
            "geometric_candidate_view": geo["candidate_view"],
            "geometric_inlier_count": geo["inlier_count"],
            "geometric_inlier_ratio": geo["inlier_ratio"],
            "geometric_median_reprojection_error_px": geo["median_reprojection_error_px"],
            "geometric_status": geo["geometry_status"],
            "geometric_failure_reason": geo["failure_reason"],
            "stage3g_transformation_plausibility": evidence["transformation_plausibility"] if evidence else "",
            "stage3g_aligned_correlation": evidence["aligned_grayscale_correlation"] if evidence else "",
            "conflicting_evidence": conflict, "uncertainty_reason": uncertainty,
            "automated_cross_check": cross, "cross_check_disagreement": disagreement,
            "review_method": method, "model_name_version": MODEL,
            "prompt_configuration_version": CONFIG_VERSION,
            "review_timestamp_utc": timestamp,
            "original_binary_sha256": source["binary_sha256"],
            "original_candidate_sha256": source["candidate_sha256"],
            "contact_sheet_reference": str(OUTPUT / "sheets" / source["sheet"]).replace("\\", "/"),
            "stage3g_overlay_reference": evidence["overlay_reference"] if evidence else "",
            "stage3g_difference_reference": evidence["difference_reference"] if evidence else "",
            "stage3g_landmark_reference": evidence["landmark_reference"] if evidence else "",
            "human_decision_used": "no",
        })
    return reviews


def proposed_groups(root: Path, reviews: list[dict]) -> tuple[list[dict], list[dict]]:
    # Existing Stage 3 proposed exclusions supply established photo/group relations.
    prior_path = root / "analysis/nine_class_overlap_completion/proposed_binary_exclusions.csv"
    prior = read_csv(prior_path)
    if len(prior) != 2369:
        raise ValueError("Prior proposed exclusions changed")
    edges = []
    for row in prior:
        members = row["confirmed_group_members"].split("|")
        if row["image_path"] not in members:
            raise ValueError("Prior group does not contain its excluded image")
        for other in members:
            if other != row["image_path"]:
                a, b = sorted((row["image_path"], other))
                edges.append({"path_a": a, "path_b": b,
                              "evidence_tier": "PRIOR_ESTABLISHED_PHOTO_RELATION",
                              "basis": row["reason"], "candidate_pair_id": ""})
    for row in reviews:
        if row["ai_assessment"] in {"AI_SAME_PHOTO", "AI_UNCERTAIN", "AI_POSSIBLE_SAME_LESION"}:
            a, b = sorted((row["binary_image_path"], row["candidate_path"]))
            tier = ("AI_SUPPORTED_SAME_PHOTO" if row["ai_assessment"] == "AI_SAME_PHOTO"
                    else "SUSPECTED_UNRESOLVED_OVERLAP")
            edges.append({"path_a": a, "path_b": b, "evidence_tier": tier,
                          "basis": row["ai_assessment"], "candidate_pair_id": row["candidate_pair_id"]})
    edges = sorted({(e["path_a"], e["path_b"], e["evidence_tier"], e["candidate_pair_id"]): e
                    for e in edges}.values(), key=lambda e: (e["path_a"], e["path_b"],
                                                              e["evidence_tier"], e["candidate_pair_id"]))
    parent = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        a, b = find(e["path_a"]), find(e["path_b"])
        if a != b:
            parent[max(a, b)] = min(a, b)
    components = defaultdict(list)
    for member in parent:
        components[find(member)].append(member)
    edge_by_component = defaultdict(set)
    for e in edges:
        edge_by_component[find(e["path_a"])].add(e["evidence_tier"])
    groups = []
    for root_id, members in sorted(components.items()):
        members.sort()
        tiers = edge_by_component[root_id]
        group_id = "S3I-" + hashlib.sha256("\n".join(members).encode()).hexdigest()[:16]
        test = any("/test/" in path for path in members)
        train = any("/train/" in path for path in members)
        recommendation = ("QUARANTINE_PRIMARY_EVALUATION_OR_KEEP_IN_ONE_PARTITION"
                          if "SUSPECTED_UNRESOLVED_OVERLAP" in tiers or
                          "AI_SUPPORTED_SAME_PHOTO" in tiers else
                          "APPLY_PRIOR_EXCLUSION_POLICY_AFTER_PROTOCOL_APPROVAL")
        for member in members:
            groups.append({"proposed_group_id": group_id, "member_path": member,
                           "group_member_count": len(members),
                           "has_prior_established_photo_edge": str("PRIOR_ESTABLISHED_PHOTO_RELATION" in tiers).lower(),
                           "has_ai_supported_photo_edge": str("AI_SUPPORTED_SAME_PHOTO" in tiers).lower(),
                           "has_unresolved_suspected_edge": str("SUSPECTED_UNRESOLVED_OVERLAP" in tiers).lower(),
                           "group_has_source_test_image": str(test).lower(),
                           "group_has_source_train_image": str(train).lower(),
                           "recommendation": recommendation})
    return edges, groups


def freeze(root: Path = ROOT) -> dict:
    root = root.resolve()
    output = root / OUTPUT
    targets = [output / name for name in ("ai_pair_review.csv", "proposed_overlap_edges.csv",
                                         "proposed_overlap_groups.csv", "review_summary.json")]
    if any(path.exists() for path in targets):
        raise FileExistsError("Preserving existing Stage 3I AI review")
    inputs = [root / path for path in (LEDGER, GEOMETRY, STRONG,
                                      OUTPUT / "sheet_manifest.csv",
                                      Path("analysis/nine_class_overlap_completion/proposed_binary_exclusions.csv"))]
    before = {str(path.relative_to(root)): sha256(path) for path in inputs}
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    reviews = create_reviews(root, timestamp)
    edges, groups = proposed_groups(root, reviews)
    counts = Counter(row["ai_assessment"] for row in reviews)
    if counts != {"AI_SAME_PHOTO": 83, "AI_DISTINCT": 326, "AI_UNCERTAIN": 20}:
        raise ValueError("Frozen visual assessment counts changed")
    summary = {"review_timestamp_utc": timestamp, "model_name_version": MODEL,
               "prompt_configuration_version": CONFIG_VERSION,
               "total_unique_pairs": 429, "visually_inspected_from_original_image_sheets": 429,
               "numerical_only_assessments": 0, "ai_assessment_counts": dict(counts),
               "strong_pair_count": 83, "strong_pair_ai_uncertain": 0,
               "prior_human_choices_copied_or_modified": False,
               "prior_source_evidence_sha256": before,
               "overlap_edge_count": len(edges), "proposed_overlap_group_count":
                   len({r["proposed_group_id"] for r in groups}),
               "clinical_patient_lesion_identity_verified": False,
               "detector_error_rates_available": False,
               "stage4_split_ready": False}
    atomic_text(targets[0], csv_text(REVIEW_FIELDS, reviews))
    atomic_text(targets[1], csv_text(EDGE_FIELDS, edges))
    atomic_text(targets[2], csv_text(GROUP_FIELDS, groups))
    atomic_text(targets[3], json.dumps(summary, indent=2) + "\n")
    if any(sha256(root / name) != digest for name, digest in before.items()):
        raise ValueError("Original audit evidence changed during AI review freeze")
    return summary


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2))
