#!/usr/bin/env python3
"""Conservative planning evidence for a modified nine-class cohort; never approves data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import requests

from nine_class_geometric_verification import geometric_evidence, load_gray
from nine_class_siim2020_pilot import (DUPS, FINGERPRINTS, META, OUT as PILOT, ROOT, SOURCE,
                                       duplicate_components, rows, save_csv, sha256)
from nine_class_similarity_audit import POPCOUNT

OUT = ROOT / "analysis/nine_class_final_cohort"
SEED = 42
VERSION = "modified_nine_class_cohort_plan_v1"
TARGET_BENIGN = 1200
SOURCE_FIELDS = ("selection_rank", "image_id", "patient_id", "lesion_id", "duplicate_component",
                 "duplicate_component_size", "source_dataset", "original_label", "original_target",
                 "original_diagnosis", "selection_seed", "metadata_sha256", "duplicates_sha256",
                 "official_record_url", "local_image_path", "prior_pilot", "acquisition_status",
                 "automated_eligibility", "review_status")


def current_plan_paths() -> tuple[Path, Path]:
    if (OUT / "candidate_manifest_v2.csv").exists():
        return OUT / "candidate_manifest_v2.csv", OUT / "candidate_selection_record_v2.json"
    return OUT / "candidate_manifest_v1.csv", OUT / "candidate_selection_record_v1.json"


def fp_array(image: np.ndarray) -> tuple[int, int]:
    small = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    dct = cv2.dct(small)[:8, :8]
    phash = (dct > np.median(dct[1:])).reshape(-1)
    tiny = cv2.resize(image, (9, 8), interpolation=cv2.INTER_AREA)
    dhash = (tiny[:, 1:] > tiny[:, :-1]).reshape(-1)
    return int.from_bytes(np.packbits(phash).tobytes(), "big"), int.from_bytes(np.packbits(dhash).tobytes(), "big")


def variants(gray: np.ndarray) -> dict[str, np.ndarray]:
    h, w = gray.shape
    crop = gray[round(.1*h):round(.9*h), round(.1*w):round(.9*w)]
    return {"native": gray, "rotate90": cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE),
            "rotate180": cv2.rotate(gray, cv2.ROTATE_180),
            "rotate270": cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE),
            "horizontal_flip": cv2.flip(gray, 1), "center_crop80": crop}


def rescreen_pilot84() -> None:
    original = {r["image_id"]: r for r in rows(PILOT / "overlap_by_image.csv")}
    pilot = [r for r in rows(PILOT / "pilot_manifest.csv") if original[r["image_id"]]["status"] == "no_candidate"]
    if len(pilot) != 84:
        raise ValueError("Frozen pilot's 84 no-candidate records changed")
    source = rows(SOURCE)
    old = {r["image_path"]: r for r in rows(FINGERPRINTS)}
    integrity = json.loads((PILOT / "canonical_source_integrity.json").read_text())
    if integrity["missing"] or integrity["sha256_mismatches"] or integrity["source_manifest_sha256"] != sha256(SOURCE):
        raise ValueError("Canonical source integrity changed")
    if len(source) != 13312 or set(old) != {r["image_path"] for r in source}:
        raise ValueError("Source/fingerprint inventory changed")
    ph = np.asarray([int(old[r["image_path"]]["phash64"], 16) for r in source], dtype=np.uint64)
    dh = np.asarray([int(old[r["image_path"]]["dhash64"], 16) for r in source], dtype=np.uint64)
    evidence, outcomes = [], []
    for entry in pilot:
        path = ROOT / entry["local_image_path"]
        gray = load_gray(path)
        found = {}
        for name, image in variants(gray).items():
            a, b = fp_array(image)
            pd = POPCOUNT[(ph ^ a).view(np.uint8).reshape(-1, 8)].sum(axis=1)
            dd = POPCOUNT[(dh ^ b).view(np.uint8).reshape(-1, 8)].sum(axis=1)
            for index in np.flatnonzero(pd <= 10):
                i = int(index)
                candidate = (int(pd[i]), int(dd[i]), name, i)
                if i not in found or candidate < found[i]:
                    found[i] = candidate
        ordered = sorted(found.values())
        geometric_checked = set()
        for source_name in ("HAM10000", "FANCONIC_LOCAL_UNVERIFIED_VERSION"):
            chosen = [x for x in ordered if source[x[3]]["source_dataset"] == source_name][:3]
            geometric_checked.update(x[3] for x in chosen)
        coherent = 0
        for p_distance, d_distance, variant, i in ordered:
            candidate = source[i]
            result = {"geometry_status": "not_run_rank_limit", "method": "", "inlier_count": "", "failure_reason": ""}
            if i in geometric_checked:
                result = geometric_evidence(gray, load_gray(ROOT / candidate["image_path"]))
            if result["geometry_status"] == "coherent":
                coherent += 1
            evidence.append({"pilot_image_id": entry["image_id"], "pilot_path": entry["local_image_path"],
                             "comparison_path": candidate["image_path"],
                             "comparison_source": candidate["source_dataset"],
                             "comparison_image_id": candidate["image_id"],
                             "comparison_lesion_id": candidate["lesion_id"],
                             "best_transform": variant, "phash_distance": p_distance,
                             "dhash_distance": d_distance,
                             "geometry_status": result["geometry_status"],
                             "geometry_method": result["method"],
                             "geometry_inliers": result["inlier_count"],
                             "geometry_failure_reason": result["failure_reason"],
                             "identity_status": "UNCERTAIN", "human_review_status": "UNREVIEWED"})
        outcomes.append({"image_id": entry["image_id"], "patient_id": entry["patient_id"],
                         "candidate_pairs": len(ordered), "geometry_checked": len(geometric_checked),
                         "coherent_geometry_candidates": coherent,
                         "screen_status": "QUARANTINE_REVIEW" if ordered else "NO_CANDIDATE_STRONGER_SCREEN",
                         "approval_status": "NOT_APPROVED"})
        print(f"{entry['image_id']}: {len(ordered)} transformed candidates; {coherent} coherent", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    save_csv(OUT / "pilot84_transformed_candidates.csv", evidence,
             ("pilot_image_id", "pilot_path", "comparison_path", "comparison_source", "comparison_image_id",
              "comparison_lesion_id", "best_transform", "phash_distance", "dhash_distance",
              "geometry_status", "geometry_method", "geometry_inliers", "geometry_failure_reason",
              "identity_status", "human_review_status"))
    save_csv(OUT / "pilot84_rescreen_outcomes.csv", outcomes,
             ("image_id", "patient_id", "candidate_pairs", "geometry_checked",
              "coherent_geometry_candidates", "screen_status", "approval_status"))
    (OUT / "pilot84_rescreen_summary.json").write_text(json.dumps({
        "pilot84": len(pilot), "candidate_pairs": len(evidence),
        "outcomes": dict(Counter(r["screen_status"] for r in outcomes)),
        "geometry_coherent_candidate_pairs": sum(r["geometry_status"] == "coherent" for r in evidence),
        "method": "pHash<=10 on native, 90/180/270-degree rotation, horizontal flip, center 80% crop; top 3 per existing source receive ORB/SIFT RANSAC; no human adjudication; no sensitivity calibration",
        "source_fingerprints_sha256": sha256(FINGERPRINTS),
        "pilot_manifest_sha256": sha256(PILOT / "pilot_manifest.csv")}, indent=2) + "\n", encoding="utf-8")


def plan_acquisition() -> None:
    result = {r["image_id"]: r for r in rows(OUT / "pilot84_rescreen_outcomes.csv")}
    old = {r["image_id"]: r for r in rows(PILOT / "pilot_manifest.csv")}
    old_status = {r["image_id"]: r["status"] for r in rows(PILOT / "overlap_by_image.csv")}
    metadata = rows(META)
    components, listed = duplicate_components(metadata, rows(DUPS))
    eligible = [r for r in metadata if r["benign_malignant"].lower() == "benign" and r["target"] == "0"
                and r["patient_id"] and r["lesion_id"] and r["image_name"] not in listed]
    eligible.sort(key=lambda r: (hashlib.sha256(f"siim2020-final-v1:{SEED}:{r['image_name']}".encode()).hexdigest(), r["image_name"]))
    selected = [r.copy() for r in rows(PILOT / "pilot_manifest.csv")]
    for r in selected:
        r.update(prior_pilot="true", acquisition_status="ACQUIRED_PILOT",
                 automated_eligibility=("QUARANTINE_CANDIDATE_RELATION" if old_status[r["image_id"]] != "no_candidate"
                  or result.get(r["image_id"], {}).get("screen_status") == "QUARANTINE_REVIEW"
                  else "PRELIMINARY_NO_CANDIDATE_NOT_APPROVED"),
                 review_status="UNREVIEWED")
    patients = {r["patient_id"] for r in selected}
    for record in eligible:
        if len(selected) >= TARGET_BENIGN:
            break
        image_id = record["image_name"]
        if image_id in old or record["patient_id"] in patients:
            continue
        patients.add(record["patient_id"])
        group, size = components[image_id]
        selected.append({"selection_rank": len(selected) + 1, "image_id": image_id,
                         "patient_id": record["patient_id"], "lesion_id": record["lesion_id"],
                         "duplicate_component": group, "duplicate_component_size": size,
                         "source_dataset": "SIIM-ISIC 2020 training v2",
                         "original_label": record["benign_malignant"], "original_target": record["target"],
                         "original_diagnosis": record["diagnosis"], "selection_seed": SEED,
                         "metadata_sha256": sha256(META), "duplicates_sha256": sha256(DUPS),
                         "official_record_url": f"https://api.isic-archive.com/api/v2/images/{image_id}/",
                         "local_image_path": f"analysis/nine_class_final_cohort/images/{image_id}.jpg",
                         "prior_pilot": "false", "acquisition_status": "PLANNED_NOT_ACQUIRED",
                         "automated_eligibility": "NOT_SCREENED", "review_status": "UNREVIEWED"})
    if len(selected) != TARGET_BENIGN or len({r['patient_id'] for r in selected}) != TARGET_BENIGN:
        raise ValueError("Unable to select target distinct patient groups")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "candidate_manifest_v1.csv"
    if path.exists():
        raise FileExistsError(path)
    save_csv(path, selected, SOURCE_FIELDS)
    quarantine = [r for r in selected if r["automated_eligibility"] == "QUARANTINE_CANDIDATE_RELATION"]
    save_csv(OUT / "exclusion_quarantine_manifest_v1.csv", quarantine, SOURCE_FIELDS)
    (OUT / "candidate_selection_record_v1.json").write_text(json.dumps({
        "version": VERSION, "seed": SEED, "target_benign": TARGET_BENIGN,
        "existing_pilot": len(old), "additional_planned": TARGET_BENIGN-len(old),
        "distinct_patient_groups": len(patients), "candidate_manifest_sha256": sha256(path),
        "source_metadata_sha256": sha256(META), "duplicate_list_sha256": sha256(DUPS),
        "rule": "Retain frozen 100-image pilot; rank remaining official benign/target=0, nonduplicate-list images by SHA256(siim2020-final-v1:42:image_id); first image per distinct patient; no approval inferred",
        "note": "Planned images are not acquired or screened; no split is approved."}, indent=2) + "\n", encoding="utf-8")


def revise_plan() -> None:
    """Version the one sentinel-lesion exclusion; preserve the original plan."""
    old_path = OUT / "candidate_manifest_v1.csv"
    new_path = OUT / "candidate_manifest_v2.csv"
    if new_path.exists():
        raise FileExistsError(new_path)
    records = rows(old_path)
    bad = [r for r in records if r["lesion_id"] == "0"]
    if len(bad) != 1 or bad[0]["image_id"] != "ISIC_3746471" or bad[0]["selection_rank"] != "200":
        raise ValueError("Sentinel-lesion source discrepancy no longer matches evidence")
    used_ids = {r["image_id"] for r in records}
    used_patients = {r["patient_id"] for r in records}
    metadata = rows(META)
    components, listed = duplicate_components(metadata, rows(DUPS))
    eligible = [r for r in metadata if r["benign_malignant"].lower() == "benign" and r["target"] == "0"
                and r["patient_id"] and r["lesion_id"] not in ("", "0") and r["image_name"] not in listed]
    eligible.sort(key=lambda r: (hashlib.sha256(f"siim2020-final-v1:{SEED}:{r['image_name']}".encode()).hexdigest(), r["image_name"]))
    replacement = next(r for r in eligible if r["image_name"] not in used_ids and r["patient_id"] not in used_patients)
    group, size = components[replacement["image_name"]]
    row = {"selection_rank": "200", "image_id": replacement["image_name"],
           "patient_id": replacement["patient_id"], "lesion_id": replacement["lesion_id"],
           "duplicate_component": group, "duplicate_component_size": size,
           "source_dataset": "SIIM-ISIC 2020 training v2",
           "original_label": replacement["benign_malignant"], "original_target": replacement["target"],
           "original_diagnosis": replacement["diagnosis"], "selection_seed": str(SEED),
           "metadata_sha256": sha256(META), "duplicates_sha256": sha256(DUPS),
           "official_record_url": f"https://api.isic-archive.com/api/v2/images/{replacement['image_name']}/",
           "local_image_path": f"analysis/nine_class_final_cohort/images/{replacement['image_name']}.jpg",
           "prior_pilot": "false", "acquisition_status": "PLANNED_NOT_ACQUIRED",
           "automated_eligibility": "NOT_SCREENED", "review_status": "UNREVIEWED"}
    revised = [row if r["selection_rank"] == "200" else r for r in records]
    save_csv(new_path, revised, SOURCE_FIELDS)
    (OUT / "candidate_selection_record_v2.json").write_text(json.dumps({
        "version": "modified_nine_class_cohort_plan_v2", "seed": SEED,
        "target_benign": TARGET_BENIGN, "candidate_manifest_sha256": sha256(new_path),
        "replaces": bad[0]["image_id"], "replacement": replacement["image_name"],
        "reason": "Challenge lesion_id sentinel 0 conflicts with official per-image Archive lesion ID; excluded without relabeling",
        "previous_manifest_sha256": sha256(old_path),
        "source_metadata_sha256": sha256(META), "duplicate_list_sha256": sha256(DUPS),
        "note": "All reviewer/approval statuses remain unresolved; no split is approved."}, indent=2) + "\n", encoding="utf-8")
    save_csv(OUT / "source_identifier_conflicts_v1.csv", [{
        "image_id": bad[0]["image_id"], "challenge_lesion_id": "0", "archive_lesion_id": "IL_0983669",
        "challenge_patient_id": bad[0]["patient_id"], "decision": "EXCLUDE_FROM_CANDIDATE_PLAN",
        "human_review_status": "UNREVIEWED", "source_plan": "candidate_manifest_v1.csv"}],
        ("image_id", "challenge_lesion_id", "archive_lesion_id", "challenge_patient_id",
         "decision", "human_review_status", "source_plan"))


def acquire_interval(start: int, end: int) -> None:
    if start < 101 or end > TARGET_BENIGN or end < start or end-start+1 > 100:
        raise ValueError("Incremental acquisition is limited to at most 100 nonpilot records")
    manifest_path, plan_path = current_plan_paths()
    manifest = rows(manifest_path)
    plan = json.loads(plan_path.read_text())
    if sha256(manifest_path) != plan["candidate_manifest_sha256"]:
        raise ValueError("Frozen candidate manifest changed")
    selected = [r for r in manifest if start <= int(r["selection_rank"]) <= end]
    if len(selected) != end-start+1 or any(r["prior_pilot"] != "false" for r in selected):
        raise ValueError("Requested interval is not a complete new-image tranche")
    ledger = OUT / "incremental_acquisition_v1.csv"
    fields = ("selection_rank", "image_id", "patient_id", "lesion_id", "status", "api_url", "file_url",
              "license", "attribution", "api_size", "download_bytes", "sha256", "s3_etag",
              "etag_matches_download_md5", "width", "height", "error")
    existing = {r["image_id"]: r for r in rows(ledger)} if ledger.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = "EG-VAN-SIIM2020-bounded-research-pilot/1.0"
    for entry in selected:
        image_id = entry["image_id"]
        path = ROOT / entry["local_image_path"]
        old = existing.get(image_id)
        if old and old["status"] == "acquired" and path.exists() and sha256(path) == old["sha256"]:
            continue
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite unexpected image: {path}")
        row = {"selection_rank": entry["selection_rank"], "image_id": image_id,
               "patient_id": entry["patient_id"], "lesion_id": entry["lesion_id"],
               "status": "failed", "api_url": entry["official_record_url"]}
        try:
            response = session.get(row["api_url"], timeout=30)
            response.raise_for_status()
            info = response.json()
            clinical = info.get("metadata", {}).get("clinical", {})
            if info.get("isic_id") != image_id or not info.get("public") or \
                    clinical.get("patient_id") != entry["patient_id"] or \
                    clinical.get("lesion_id") != entry["lesion_id"]:
                raise ValueError("Official Archive/challenge identity mismatch")
            row.update(license=info.get("copyright_license", ""),
                       attribution=info.get("attribution", ""))
            if row["license"] not in {"CC0", "CC-0", "CC-BY", "CC-BY-NC"}:
                raise ValueError("Unreviewed image-level license")
            full = info.get("files", {}).get("full", {})
            url = full.get("url", "")
            if url != f"https://isic-archive.s3.amazonaws.com/images/{image_id}.jpg":
                raise ValueError("Unexpected official full-image URL")
            row["file_url"] = url
            row["api_size"] = full.get("size", "")
            if not isinstance(full.get("size"), int) or full["size"] > 30_000_000:
                raise ValueError("Unexpected API file size")
            with session.get(url, timeout=90, stream=True) as image_response:
                image_response.raise_for_status()
                content = b"".join(image_response.iter_content(1024 * 1024))
                etag = image_response.headers.get("ETag", "").strip('"')
            if not content.startswith(b"\xff\xd8") or len(content) > 30_000_000:
                raise ValueError("Invalid bounded JPEG response")
            image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("JPEG decode failed")
            md5 = hashlib.md5(content).hexdigest()
            if etag and etag != md5:
                raise ValueError("S3 ETag differs from downloaded content MD5")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            row.update(status="acquired", download_bytes=len(content), sha256=sha256(path),
                       s3_etag=etag, etag_matches_download_md5=bool(etag and etag == md5),
                       width=image.shape[1], height=image.shape[0])
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        existing[image_id] = row
        save_csv(ledger, sorted(existing.values(), key=lambda r: (int(r["selection_rank"]), r["image_id"])), fields)
        print(f"{entry['selection_rank']} {image_id}: {row['status']} {row.get('error', '')}", flush=True)
        time.sleep(.1)


def screen_acquired() -> None:
    """Screen acquired SIIM cases against canonical sources and one another."""
    manifest_path, _ = current_plan_paths()
    manifest = rows(manifest_path)
    by_id = {r["image_id"]: r for r in manifest}
    pilot_acq = {r["image_id"]: r for r in rows(PILOT / "acquisition.csv") if r["status"] == "acquired"}
    new_acq = {r["image_id"]: r for r in rows(OUT / "incremental_acquisition_v1.csv") if r["status"] == "acquired"}
    acquired = {**pilot_acq, **new_acq}
    if len(pilot_acq) != 100 or len(new_acq) != 100 or len(acquired) != 200:
        raise ValueError("Expected frozen pilot plus one complete 100-image incremental tranche")
    for image_id, record in acquired.items():
        if sha256(ROOT / by_id[image_id]["local_image_path"]) != record["sha256"]:
            raise ValueError(f"Acquired image hash changed: {image_id}")
    save_csv(OUT / "acquired_source_attribution_v1.csv", [
        {"image_id": image_id, "image_path": by_id[image_id]["local_image_path"],
         "source_dataset": "SIIM-ISIC 2020 training v2", "aggregate_license": "CC-BY-NC 4.0",
         "image_level_license": record["license"], "image_level_attribution": record["attribution"],
         "official_api_record": record["api_url"], "official_full_url": record["file_url"],
         "sha256": record["sha256"]} for image_id, record in sorted(acquired.items())],
        ("image_id", "image_path", "source_dataset", "aggregate_license", "image_level_license",
         "image_level_attribution", "official_api_record", "official_full_url", "sha256"))
    integrity = json.loads((PILOT / "canonical_source_integrity.json").read_text())
    if integrity["missing"] or integrity["sha256_mismatches"] or integrity["source_manifest_sha256"] != sha256(SOURCE):
        raise ValueError("Frozen canonical source integrity is not verified")
    source = rows(SOURCE)
    old = {r["image_path"]: r for r in rows(FINGERPRINTS)}
    source_ph = np.asarray([int(old[r["image_path"]]["phash64"], 16) for r in source], dtype=np.uint64)
    source_dh = np.asarray([int(old[r["image_path"]]["dhash64"], 16) for r in source], dtype=np.uint64)
    source_hash = {}
    for record in source:
        source_hash.setdefault(record["sha256"], []).append(record)
    fields = ("left_image_id", "left_path", "right_path", "right_source", "right_image_id",
              "right_patient_id", "right_lesion_id", "relation_type", "best_transform",
              "phash_distance", "dhash_distance", "geometry_status", "geometry_inliers",
              "evidence_class", "human_review_status")
    evidence = []
    # Existing pilot-vs-HAM/Fanconic evidence is reused, not recomputed.
    for record in rows(PILOT / "overlap_candidates.csv"):
        evidence.append({"left_image_id": record["pilot_image_id"], "left_path": record["pilot_image_path"],
                         "right_path": record["comparison_path"], "right_source": record["comparison_source"],
                         "right_image_id": record["comparison_image_id"],
                         "right_patient_id": record["comparison_patient_id"],
                         "right_lesion_id": record["comparison_lesion_id"],
                         "relation_type": "cross_source_perceptual", "best_transform": "native",
                         "phash_distance": record["phash_distance"], "dhash_distance": record["dhash_distance"],
                         "geometry_status": record["geometry_status"], "geometry_inliers": record["geometry_inliers"],
                         "evidence_class": "UNCERTAIN", "human_review_status": "UNREVIEWED"})
    for record in rows(OUT / "pilot84_transformed_candidates.csv"):
        evidence.append({"left_image_id": record["pilot_image_id"], "left_path": record["pilot_path"],
                         "right_path": record["comparison_path"], "right_source": record["comparison_source"],
                         "right_image_id": record["comparison_image_id"], "right_patient_id": "",
                         "right_lesion_id": record["comparison_lesion_id"],
                         "relation_type": "cross_source_transformed_perceptual", "best_transform": record["best_transform"],
                         "phash_distance": record["phash_distance"], "dhash_distance": record["dhash_distance"],
                         "geometry_status": record["geometry_status"], "geometry_inliers": record["geometry_inliers"],
                         "evidence_class": "UNCERTAIN", "human_review_status": "UNREVIEWED"})
    # New tranche versus canonical HAM and Fanconic. Retain every pHash<=10
    # transformed candidate, checking geometry only for the closest three per source.
    for image_id in new_acq:
        entry = by_id[image_id]
        gray = load_gray(ROOT / entry["local_image_path"])
        found = {}
        for name, image in variants(gray).items():
            a, b = fp_array(image)
            pd = POPCOUNT[(source_ph ^ a).view(np.uint8).reshape(-1, 8)].sum(axis=1)
            dd = POPCOUNT[(source_dh ^ b).view(np.uint8).reshape(-1, 8)].sum(axis=1)
            for index in np.flatnonzero(pd <= 10):
                i = int(index)
                candidate = (int(pd[i]), int(dd[i]), name, i)
                if i not in found or candidate < found[i]:
                    found[i] = candidate
        for match in source_hash.get(new_acq[image_id]["sha256"], []):
            i = next(i for i, r in enumerate(source) if r["image_path"] == match["image_path"])
            found.setdefault(i, (0, 0, "exact_sha256", i))
        ordered = sorted(found.values())
        checked = set()
        for source_name in ("HAM10000", "FANCONIC_LOCAL_UNVERIFIED_VERSION"):
            checked.update(x[3] for x in [x for x in ordered if source[x[3]]["source_dataset"] == source_name][:3])
        for pd, dd, transform, i in ordered:
            other = source[i]
            exact = new_acq[image_id]["sha256"] == other["sha256"]
            geo = {"geometry_status": "not_run_rank_limit", "inlier_count": ""}
            if i in checked and not exact:
                geo = geometric_evidence(gray, load_gray(ROOT / other["image_path"]))
            evidence.append({"left_image_id": image_id, "left_path": entry["local_image_path"],
                             "right_path": other["image_path"], "right_source": other["source_dataset"],
                             "right_image_id": other["image_id"], "right_patient_id": other["patient_id"],
                             "right_lesion_id": other["lesion_id"],
                             "relation_type": "cross_source_exact" if exact else "cross_source_transformed_perceptual",
                             "best_transform": transform, "phash_distance": pd, "dhash_distance": dd,
                             "geometry_status": geo["geometry_status"], "geometry_inliers": geo["inlier_count"],
                             "evidence_class": "CONFIRMED_SAME_BYTES" if exact else "PROBABLE_PHOTO_RELATION" if geo["geometry_status"] == "coherent" else "UNCERTAIN",
                             "human_review_status": "UNREVIEWED"})
        print(f"new cross-source {image_id}: {len(ordered)} candidates", flush=True)
    # Pairwise within the acquired SIIM sample: include official IDs/patients,
    # exact content, and transformed-photo candidates. Different patient IDs
    # never prove different photographs or lesions.
    ids = sorted(acquired)
    gray = {image_id: load_gray(ROOT / by_id[image_id]["local_image_path"]) for image_id in ids}
    native = {image_id: fp_array(gray[image_id]) for image_id in ids}
    native_ph = np.asarray([native[x][0] for x in ids], dtype=np.uint64)
    native_dh = np.asarray([native[x][1] for x in ids], dtype=np.uint64)
    siim_found = {}
    for a_index, image_id in enumerate(ids):
        for name, image in variants(gray[image_id]).items():
            p, d = fp_array(image)
            pd = POPCOUNT[(native_ph ^ p).view(np.uint8).reshape(-1, 8)].sum(axis=1)
            dd = POPCOUNT[(native_dh ^ d).view(np.uint8).reshape(-1, 8)].sum(axis=1)
            for index in np.flatnonzero(pd <= 10):
                j = int(index)
                if j == a_index:
                    continue
                key = tuple(sorted((image_id, ids[j])))
                value = (int(pd[j]), int(dd[j]), name)
                if key not in siim_found or value < siim_found[key]:
                    siim_found[key] = value
    for i, a in enumerate(ids):
        for b in ids[i+1:]:
            if acquired[a]["sha256"] == acquired[b]["sha256"]:
                siim_found.setdefault((a, b), (0, 0, "exact_sha256"))
    siim_order = sorted(siim_found.items(), key=lambda x: (x[1], x[0]))
    # Geometry is bounded to the three nearest per left image.
    checked_count = Counter()
    for (a, b), (pd, dd, transform) in siim_order:
        exact = acquired[a]["sha256"] == acquired[b]["sha256"]
        geo = {"geometry_status": "not_run_rank_limit", "inlier_count": ""}
        if not exact and checked_count[a] < 3:
            geo = geometric_evidence(gray[a], gray[b])
            checked_count[a] += 1
        evidence.append({"left_image_id": a, "left_path": by_id[a]["local_image_path"],
                         "right_path": by_id[b]["local_image_path"], "right_source": "SIIM-ISIC 2020 training v2",
                         "right_image_id": b, "right_patient_id": by_id[b]["patient_id"],
                         "right_lesion_id": by_id[b]["lesion_id"],
                         "relation_type": "within_siim_exact" if exact else "within_siim_transformed_perceptual",
                         "best_transform": transform, "phash_distance": pd, "dhash_distance": dd,
                         "geometry_status": geo["geometry_status"], "geometry_inliers": geo["inlier_count"],
                         "evidence_class": "CONFIRMED_SAME_BYTES" if exact else "PROBABLE_PHOTO_RELATION" if geo["geometry_status"] == "coherent" else "UNCERTAIN",
                         "human_review_status": "UNREVIEWED"})
    save_csv(OUT / "acquired_overlap_evidence_v1.csv", evidence, fields)
    linked = Counter(r["left_image_id"] for r in evidence)
    linked.update(r["right_image_id"] for r in evidence if r["right_source"] == "SIIM-ISIC 2020 training v2")
    statuses = []
    for image_id in ids:
        status = "QUARANTINE_CANDIDATE_RELATION" if linked[image_id] else "PRELIMINARY_NO_CANDIDATE_NOT_APPROVED"
        statuses.append({"image_id": image_id, "patient_id": by_id[image_id]["patient_id"],
                         "lesion_id": by_id[image_id]["lesion_id"], "candidate_relations": linked[image_id],
                         "automated_status": status, "human_review_status": "UNREVIEWED",
                         "approval_status": "NOT_APPROVED"})
    save_csv(OUT / "acquired_candidate_status_v1.csv", statuses,
             ("image_id", "patient_id", "lesion_id", "candidate_relations", "automated_status",
              "human_review_status", "approval_status"))
    summary = {"acquired": len(ids), "pilot": len(pilot_acq), "incremental": len(new_acq),
               "candidate_relations": len(evidence),
               "relation_types": dict(Counter(r["relation_type"] for r in evidence)),
               "evidence_classes": dict(Counter(r["evidence_class"] for r in evidence)),
               "automated_statuses": dict(Counter(r["automated_status"] for r in statuses)),
               "approved": 0, "human_reviewed": 0,
               "source_manifest_sha256": sha256(SOURCE),
               "candidate_manifest_sha256": sha256(manifest_path)}
    (OUT / "acquired_screen_summary_v1.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    render_gallery(evidence)


def render_gallery(evidence: list[dict]) -> None:
    # Keep an actionable gallery: three closest relations per acquired image.
    ordered = sorted(evidence, key=lambda r: (int(r["phash_distance"]), int(r["dhash_distance"]),
                                              r["left_image_id"], r["right_path"]))
    chosen, count = [], Counter()
    for row in ordered:
        if count[row["left_image_id"]] < 3:
            chosen.append(row)
            count[row["left_image_id"]] += 1
    cards = []
    for i, row in enumerate(chosen, 1):
        a, b = html.escape(row["left_path"]), html.escape(row["right_path"])
        cards.append(f'<section><h2>Candidate {i}: {html.escape(row["left_image_id"])}</h2>'
                     f'<p>{html.escape(row["relation_type"])}; pHash {row["phash_distance"]}; '
                     f'dHash {row["dhash_distance"]}; transform {html.escape(row["best_transform"])}; '
                     f'geometry {html.escape(row["geometry_status"])}. Automated only; unreviewed.</p>'
                     f'<div><figure><a href="../../{a}"><img src="../../{a}"></a><figcaption>{a}</figcaption></figure>'
                     f'<figure><a href="../../{b}"><img src="../../{b}"></a><figcaption>{b}</figcaption></figure></div></section>')
    page = '<!doctype html><meta charset="utf-8"><title>Unreviewed cohort candidates</title>' + \
           '<style>body{font:16px sans-serif;max-width:1400px;margin:auto}section{border-bottom:2px solid #777;padding:1em}' + \
           'section div{display:flex;gap:1em}figure{width:50%;margin:0}img{max-width:100%;max-height:850px;object-fit:contain}</style>' + \
           '<h1>Automated candidates requiring independent review</h1><p>Click images for original resolution. ' + \
           'This gallery shows up to three closest relations per image; the CSV holds every relation. No reviewer decision is inferred.</p>' + ''.join(cards)
    (OUT / "acquired_review_gallery_v1.html").write_text(page, encoding="utf-8")


def assign_group_partitions(group_members: dict[str, list[dict]], seed: int = SEED) -> dict[str, str]:
    """Deterministic planning allocation; returns no approval or clinical split."""
    classes = ("AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT")
    class_groups = {name: {group_id for group_id, members in group_members.items()
                           if any(r["class_name"] == name for r in members)} for name in classes}
    assigned = {group_id: "test" for group_id, members in group_members.items()
                if any(r["source_split"] == "test" for r in members)}
    for name in sorted(classes, key=lambda n: (len(class_groups[n]), n)):
        groups = class_groups[name]
        if len(groups) < 4:
            raise ValueError(f"Fewer than four known groups for {name}")
        per_holdout = max(1, round(len(groups) * .10))
        for partition in ("test", "validation", "calibration"):
            have = sum(assigned.get(g) == partition for g in groups)
            needed = max(0, per_holdout - have)
            available = sorted((g for g in groups if g not in assigned),
                key=lambda g: (hashlib.sha256(f"{seed}:{name}:{partition}:{g}".encode()).hexdigest(), g))
            for group_id in available[:needed]:
                assigned[group_id] = partition
    for group_id in group_members:
        assigned.setdefault(group_id, "train")
    if any(len({assigned[g] for g in class_groups[name]}) < 4 for name in classes):
        raise ValueError("Known group distribution cannot cover all four partitions")
    return assigned


def write_candidate_decisions() -> None:
    manifest_path, _ = current_plan_paths()
    manifest = rows(manifest_path)
    outcomes = {r["image_id"]: r for r in rows(OUT / "acquired_candidate_status_v1.csv")}
    acquisition = {r["image_id"]: r for r in rows(OUT / "incremental_acquisition_v1.csv")}
    result = []
    for r in manifest:
        image_id = r["image_id"]
        state = outcomes.get(image_id)
        result.append({**r, "actual_acquisition_status": "ACQUIRED" if state else "NOT_ACQUIRED",
                       "actual_automated_status": state["automated_status"] if state else "NOT_SCREENED",
                       "candidate_relations": state["candidate_relations"] if state else "",
                       "human_review_status": "UNREVIEWED", "approval_status": "NOT_APPROVED"})
    fields = SOURCE_FIELDS + ("actual_acquisition_status", "actual_automated_status",
                             "candidate_relations", "human_review_status", "approval_status")
    save_csv(OUT / "candidate_decision_manifest_v2.csv", result, fields)
    save_csv(OUT / "exclusion_quarantine_manifest_v2.csv",
             [r for r in result if r["actual_automated_status"] == "QUARANTINE_CANDIDATE_RELATION"], fields)
    save_csv(OUT / "unacquired_candidate_manifest_v2.csv",
             [r for r in result if r["actual_acquisition_status"] == "NOT_ACQUIRED"], fields)
    failed = [r for r in acquisition.values() if r["status"] != "acquired"]
    if failed:
        save_csv(OUT / "incremental_acquisition_exceptions_v1.csv", failed,
                 tuple(rows(OUT / "incremental_acquisition_v1.csv")[0]))


def prepare_four_way_preview() -> None:
    manifest_path, _ = current_plan_paths()
    manifest = {r["image_id"]: r for r in rows(manifest_path)}
    acquired_status = {r["image_id"]: r for r in rows(OUT / "acquired_candidate_status_v1.csv")}
    acquired_attrs = {r["image_id"]: r for r in rows(OUT / "acquired_source_attribution_v1.csv")}
    stage4 = rows(SOURCE)
    protected_groups = {r["overlap_group"] for r in stage4 if r["source_split"] == "test"}
    allowed = {"HAM_AVAILABLE_NOT_FINAL_ELIGIBLE", "BINARY_PROVISIONAL_SOURCE_TRAIN",
               "PROTECTED_SOURCE_TEST_UNADJUDICATED"}
    inventory = []
    for r in stage4:
        if r["provisional_eligibility_status"] not in allowed:
            continue
        if r["source_split"] != "test" and r["overlap_group"] in protected_groups:
            continue
        inventory.append({"image_path": r["image_path"], "source_dataset": r["source_dataset"],
                          "original_label": r["original_label"], "class_name": r["class_name"],
                          "class_index": r["class_index"], "image_id": r["image_id"],
                          "lesion_id": r["lesion_id"], "patient_id": r["patient_id"],
                          "source_split": r["source_split"], "sha256": r["sha256"],
                          "overlap_group": r["overlap_group"],
                          "automated_status": r["provisional_eligibility_status"],
                          "approval_status": "NOT_APPROVED"})
    for image_id, status in acquired_status.items():
        if status["automated_status"] != "PRELIMINARY_NO_CANDIDATE_NOT_APPROVED":
            continue
        r, attr = manifest[image_id], acquired_attrs[image_id]
        inventory.append({"image_path": r["local_image_path"], "source_dataset": "SIIM-ISIC 2020 training v2",
                          "original_label": r["original_label"], "class_name": "BENIGN", "class_index": "7",
                          "image_id": image_id, "lesion_id": r["lesion_id"], "patient_id": r["patient_id"],
                          "source_split": "2020_training", "sha256": attr["sha256"],
                          "overlap_group": "SIIM_PATIENT_" + r["patient_id"],
                          "automated_status": status["automated_status"], "approval_status": "NOT_APPROVED"})
    # Exclude any unresolved cross-source candidate from the preview. This
    # allocation is safe for known groups only; no-match is not independence.
    group_members = defaultdict(list)
    for record in inventory:
        group_members[record["overlap_group"]].append(record)
    assigned = assign_group_partitions(group_members)
    fields = ("image_path", "source_dataset", "original_label", "class_name", "class_index",
              "image_id", "lesion_id", "patient_id", "source_split", "sha256", "overlap_group",
              "automated_status", "approval_status", "proposed_partition")
    preview = [dict(record, proposed_partition=assigned[record["overlap_group"]]) for record in inventory]
    save_csv(OUT / "four_way_planning_inventory_v1.csv", inventory, fields[:-1])
    save_csv(OUT / "four_way_planning_assignment_v1.csv", preview, fields)
    for partition in ("train", "validation", "calibration", "test"):
        save_csv(OUT / f"four_way_{partition}_PLANNING_ONLY_v1.csv",
                 [r for r in preview if r["proposed_partition"] == partition], fields)
    counts = {partition: dict(Counter(r["class_name"] for r in preview if r["proposed_partition"] == partition))
              for partition in ("train", "validation", "calibration", "test")}
    source_test_violations = [r["image_path"] for r in preview
                              if r["source_split"] == "test" and r["proposed_partition"] != "test"]
    group_crossings = {group_id for group_id, members in group_members.items()
                       if len({assigned[r["overlap_group"]] for r in members}) > 1}
    if source_test_violations or group_crossings:
        raise ValueError("Preview has a known source-test or group crossing")
    report = {"status": "PLANNING_ONLY_NOT_APPROVED", "version": "four_way_preview_v1_from_candidate_v2",
              "planning_inventory_rows": len(inventory), "known_groups": len(group_members),
              "counts": counts, "source_test_violations": source_test_violations,
              "known_group_crossings": len(group_crossings),
              "siim_benign_preview_count": sum(r["class_name"] == "BENIGN" for r in preview),
              "approved_rows": 0,
              "all_nine_each_partition_numerically_present": all(all(counts[p].get(name, 0) > 0 for name in
                ("AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT"))
                for p in counts),
              "training_gate_accepts_preview": False,
              "reason": "All rows remain unapproved, SIIM no-candidate is uncalibrated, Fanconic MALIGNANT provenance/rights and patient grouping remain unresolved; the version-2 four-way Stage6 gate rejects this planning schema.",
              "planning_assignment_sha256": sha256(OUT / "four_way_planning_assignment_v1.csv")}
    (OUT / "four_way_feasibility_report_v1.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("rescreen-pilot84", "plan-acquisition", "revise-plan",
                                           "acquire-interval", "screen-acquired", "write-decisions",
                                           "plan-four-way"))
    parser.add_argument("--rank-start", type=int)
    parser.add_argument("--rank-end", type=int)
    args = parser.parse_args()
    if args.action == "acquire-interval":
        if args.rank_start is None or args.rank_end is None:
            parser.error("acquire-interval requires --rank-start and --rank-end")
        acquire_interval(args.rank_start, args.rank_end)
    else:
        {"rescreen-pilot84": rescreen_pilot84, "plan-acquisition": plan_acquisition,
         "revise-plan": revise_plan,
         "screen-acquired": screen_acquired,
         "write-decisions": write_candidate_decisions,
         "plan-four-way": prepare_four_way_preview}[args.action]()


if __name__ == "__main__":
    main()
