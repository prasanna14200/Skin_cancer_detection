#!/usr/bin/env python3
"""Bounded SIIM 2020 benign pilot. No clinical eligibility decisions are made here."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import requests

from nine_class_similarity_audit import POPCOUNT, fingerprint
from nine_class_geometric_verification import geometric_evidence, load_gray

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/nine_class_siim2020_pilot"
META = ROOT / "analysis/nine_class_dataset_recovery/ISIC_2020_Training_GroundTruth_v2.csv"
DUPS = ROOT / "analysis/nine_class_dataset_recovery/ISIC_2020_Training_Duplicates.csv"
SOURCE = ROOT / "analysis/nine_class_stage4/nine_class_source_manifest.csv"
FINGERPRINTS = ROOT / "analysis/nine_class_similarity/fingerprints.csv"
ID_PATTERN = re.compile(r"ISIC_\d{7}\Z")
SEED = 42
LIMIT = 100
MANIFEST_FIELDS = ("selection_rank", "image_id", "patient_id", "lesion_id", "duplicate_component",
                   "duplicate_component_size", "official_duplicate_listed", "source_dataset",
                   "original_label", "original_target", "original_diagnosis", "selection_seed",
                   "metadata_sha256", "duplicates_sha256", "official_record_url", "local_image_path")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def save_csv(path: Path, records: list[dict], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def duplicate_components(metadata: list[dict], duplicate_rows: list[dict]) -> tuple[dict, set]:
    ids = {r["image_name"] for r in metadata}
    parent = {image_id: image_id for image_id in ids}
    listed = set()

    def find(x):
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for row in duplicate_rows:
        a, b = row["image_name_1"], row["image_name_2"]
        if a not in ids or b not in ids:
            raise ValueError("Duplicate list refers to missing metadata ID")
        listed.update((a, b))
        parent[find(b)] = find(a)
    members = {}
    for image_id in ids:
        members.setdefault(find(image_id), []).append(image_id)
    components = {image_id: (min(group), len(group)) for group in members.values() for image_id in group}
    return components, listed


def select(metadata: list[dict], duplicate_rows: list[dict], seed: int = SEED,
           limit: int = LIMIT) -> list[dict]:
    if not 1 <= limit <= 100:
        raise ValueError("Pilot limit must be 1..100")
    components, listed = duplicate_components(metadata, duplicate_rows)
    candidates = [r for r in metadata if r["benign_malignant"].lower() == "benign"
                  and r["target"] == "0" and r["patient_id"] and r["lesion_id"]
                  and r["image_name"] not in listed]
    candidates.sort(key=lambda r: (hashlib.sha256(f"siim2020-pilot-v1:{seed}:{r['image_name']}".encode()).hexdigest(),
                                   r["image_name"]))
    selected, patients = [], set()
    for r in candidates:
        if r["patient_id"] in patients:
            continue
        image_id = r["image_name"]
        if not ID_PATTERN.fullmatch(image_id):
            raise ValueError(f"Invalid ISIC ID {image_id}")
        patients.add(r["patient_id"])
        component, size = components[image_id]
        selected.append({"selection_rank": len(selected) + 1, "image_id": image_id,
                         "patient_id": r["patient_id"], "lesion_id": r["lesion_id"],
                         "duplicate_component": component, "duplicate_component_size": size,
                         "official_duplicate_listed": "false", "source_dataset": "SIIM-ISIC 2020 training v2",
                         "original_label": r["benign_malignant"], "original_target": r["target"],
                         "original_diagnosis": r["diagnosis"], "selection_seed": seed,
                         "official_record_url": f"https://api.isic-archive.com/api/v2/images/{image_id}/",
                         "local_image_path": f"analysis/nine_class_siim2020_pilot/images/{image_id}.jpg"})
        if len(selected) == limit:
            break
    if len(selected) != limit:
        raise ValueError(f"Only {len(selected)} distinct eligible patients")
    return selected


def freeze_manifest() -> None:
    output = OUT / "pilot_manifest.csv"
    if output.exists():
        raise FileExistsError(output)
    manifest = select(rows(META), rows(DUPS))
    for row in manifest:
        row["metadata_sha256"] = sha256(META)
        row["duplicates_sha256"] = sha256(DUPS)
    save_csv(output, manifest, MANIFEST_FIELDS)
    (OUT / "selection_summary.json").write_text(json.dumps({
        "manifest_sha256": sha256(output), "seed": SEED, "requested": len(manifest),
        "distinct_patients": len({r['patient_id'] for r in manifest}),
        "official_duplicate_listed_excluded": True,
        "selection_rule": "SHA256 rank of siim2020-pilot-v1:42:image_id; first image per patient; exclude both ends of official duplicate pairs",
        "metadata_sha256": sha256(META), "duplicates_sha256": sha256(DUPS)}, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {len(manifest)} records: {output}")


def acquire() -> None:
    manifest = rows(OUT / "pilot_manifest.csv")
    if not 1 <= len(manifest) <= LIMIT or len({r['image_id'] for r in manifest}) != len(manifest):
        raise ValueError("Invalid bounded manifest")
    if sha256(OUT / "pilot_manifest.csv") != json.loads((OUT / "selection_summary.json").read_text())["manifest_sha256"]:
        raise ValueError("Frozen manifest hash changed")
    ledger_path = OUT / "acquisition.csv"
    fields = ("image_id", "status", "api_url", "file_url", "license", "attribution", "source_file_size",
              "api_size_matches_download",
              "download_bytes", "sha256", "width", "height", "error")
    previous = {r["image_id"]: r for r in rows(ledger_path)} if ledger_path.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = "EG-VAN-SIIM2020-bounded-research-pilot/1.0"
    for index, entry in enumerate(manifest, 1):
        image_id = entry["image_id"]
        if not ID_PATTERN.fullmatch(image_id):
            raise ValueError(f"Invalid ID {image_id}")
        target = ROOT / entry["local_image_path"]
        if image_id in previous and previous[image_id]["status"] == "acquired" and target.exists():
            if sha256(target) == previous[image_id]["sha256"]:
                continue
            raise ValueError(f"Existing acquired image checksum changed: {target}")
        record = {"image_id": image_id, "status": "failed", "api_url": entry["official_record_url"]}
        try:
            response = session.get(record["api_url"], timeout=30)
            response.raise_for_status()
            info = response.json()
            if info.get("isic_id") != image_id or not info.get("public"):
                raise ValueError("API identity/public flag mismatch")
            record["license"] = info.get("copyright_license", "")
            record["attribution"] = info.get("attribution", "")
            if record["license"] not in {"CC0", "CC-0", "CC-BY", "CC-BY-NC"}:
                raise ValueError(f"Unreviewed image-level license: {record['license']}")
            full = info.get("files", {}).get("full", {})
            url = full.get("url", "")
            if not url.startswith("https://isic-archive.s3.amazonaws.com/images/") or not url.endswith(f"/{image_id}.jpg"):
                raise ValueError("Unexpected official full-image URL")
            record["file_url"] = url
            record["source_file_size"] = full.get("size", "")
            if not isinstance(full.get("size"), int) or full["size"] > 30_000_000:
                raise ValueError("Unexpected source image size")
            with session.get(url, timeout=90, stream=True) as image_response:
                image_response.raise_for_status()
                content = b"".join(image_response.iter_content(1024 * 1024))
            if not content.startswith(b"\xff\xd8") or len(content) > 30_000_000:
                raise ValueError("JPEG signature or bounded size invalid")
            record["api_size_matches_download"] = len(content) == full["size"]
            image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("JPEG decode failed")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise FileExistsError(target)
            target.write_bytes(content)
            record.update(status="acquired", download_bytes=len(content), sha256=sha256(target),
                          width=image.shape[1], height=image.shape[0])
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        previous[image_id] = record
        save_csv(ledger_path, [previous[r["image_id"]] for r in manifest if r["image_id"] in previous], fields)
        print(f"{index}/{len(manifest)} {image_id}: {record['status']} {record.get('error', '')}", flush=True)
        time.sleep(0.1)


def verify_archive_metadata() -> None:
    """Compare challenge v2 identity fields with per-image Archive records."""
    manifest = rows(OUT / "pilot_manifest.csv")
    acquisition = {r["image_id"]: r for r in rows(OUT / "acquisition.csv")}
    fields = ("image_id", "challenge_patient_id", "archive_patient_id", "patient_id_match",
              "challenge_lesion_id", "archive_lesion_id", "lesion_id_match",
              "archive_license", "acquisition_license_match", "archive_attribution_match",
              "archive_full_url_match", "status", "error")
    output = OUT / "archive_metadata_verification.csv"
    verified = {r["image_id"]: r for r in rows(output)} if output.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = "EG-VAN-SIIM2020-bounded-research-pilot/1.0"
    for index, entry in enumerate(manifest, 1):
        image_id = entry["image_id"]
        if image_id in verified and verified[image_id]["status"] == "matched":
            continue
        row = {"image_id": image_id, "challenge_patient_id": entry["patient_id"],
               "challenge_lesion_id": entry["lesion_id"], "status": "failed"}
        try:
            response = session.get(entry["official_record_url"], timeout=30)
            response.raise_for_status()
            info = response.json()
            clinical = info.get("metadata", {}).get("clinical", {})
            record = acquisition[image_id]
            row.update(archive_patient_id=clinical.get("patient_id", ""),
                       archive_lesion_id=clinical.get("lesion_id", ""),
                       patient_id_match=clinical.get("patient_id") == entry["patient_id"],
                       lesion_id_match=clinical.get("lesion_id") == entry["lesion_id"],
                       archive_license=info.get("copyright_license", ""),
                       acquisition_license_match=info.get("copyright_license") == record["license"],
                       archive_attribution_match=info.get("attribution") == record["attribution"],
                       archive_full_url_match=info.get("files", {}).get("full", {}).get("url") == record["file_url"])
            if info.get("isic_id") == image_id and all(row.get(k) is True for k in
                  ("patient_id_match", "lesion_id_match", "acquisition_license_match",
                   "archive_attribution_match", "archive_full_url_match")):
                row["status"] = "matched"
            else:
                row["status"] = "mismatch"
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        verified[image_id] = row
        save_csv(output, [verified[r["image_id"]] for r in manifest if r["image_id"] in verified], fields)
        print(f"metadata {index}/{len(manifest)} {image_id}: {row['status']}", flush=True)


def verify_s3_etags() -> None:
    """Record S3 object ETags; single-part MD5 agreement is source-byte evidence."""
    acquisition = rows(OUT / "acquisition.csv")
    fields = ("image_id", "s3_etag", "etag_is_plain_md5", "local_md5", "etag_matches_local_md5",
              "head_content_length", "head_length_matches_local", "status", "error")
    output = OUT / "source_object_checksums.csv"
    previous = {r["image_id"]: r for r in rows(output)} if output.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = "EG-VAN-SIIM2020-bounded-research-pilot/1.0"
    for index, record in enumerate(acquisition, 1):
        image_id = record["image_id"]
        if image_id in previous and previous[image_id]["status"] == "matched":
            continue
        result = {"image_id": image_id, "status": "failed"}
        try:
            response = session.head(record["file_url"], timeout=30)
            response.raise_for_status()
            etag = response.headers.get("ETag", "").strip('"')
            local_md5 = hashlib.md5((OUT / "images" / f"{image_id}.jpg").read_bytes()).hexdigest()
            size = response.headers.get("Content-Length", "")
            result.update(s3_etag=etag, etag_is_plain_md5=bool(re.fullmatch(r"[0-9a-f]{32}", etag)),
                          local_md5=local_md5, etag_matches_local_md5=etag == local_md5,
                          head_content_length=size,
                          head_length_matches_local=size.isdigit() and int(size) == int(record["download_bytes"]))
            result["status"] = "matched" if all(result[k] for k in
                ("etag_is_plain_md5", "etag_matches_local_md5", "head_length_matches_local")) else "mismatch"
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        previous[image_id] = result
        save_csv(output, [previous[r["image_id"]] for r in acquisition if r["image_id"] in previous], fields)
        print(f"S3 HEAD {index}/{len(acquisition)} {image_id}: {result['status']}", flush=True)


def verify_canonical_source() -> None:
    """Check that frozen Stage 4 SHA-256 values still describe local source files."""
    source = rows(SOURCE)
    missing, mismatches = [], []
    start = time.monotonic()
    for index, record in enumerate(source, 1):
        path = ROOT / record["image_path"]
        if not path.exists():
            missing.append(record["image_path"])
        elif sha256(path) != record["sha256"]:
            mismatches.append(record["image_path"])
        if index % 3000 == 0:
            print(f"verified {index}/{len(source)}", flush=True)
    result = {"entries": len(source), "missing": missing, "sha256_mismatches": mismatches,
              "source_manifest_sha256": sha256(SOURCE),
              "elapsed_seconds": round(time.monotonic() - start, 1)}
    (OUT / "canonical_source_integrity.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if missing or mismatches:
        raise ValueError("Canonical source no longer matches its frozen hash manifest")


def screen() -> None:
    manifest = rows(OUT / "pilot_manifest.csv")
    acquired = {r["image_id"]: r for r in rows(OUT / "acquisition.csv") if r["status"] == "acquired"}
    integrity = json.loads((OUT / "canonical_source_integrity.json").read_text(encoding="utf-8"))
    if integrity["missing"] or integrity["sha256_mismatches"] or integrity["source_manifest_sha256"] != sha256(SOURCE):
        raise ValueError("Canonical source integrity preflight failed")
    source = rows(SOURCE)
    prints = rows(FINGERPRINTS)
    by_path = {r["image_path"]: r for r in prints}
    if len(source) != 13312 or len(by_path) != 13312 or set(by_path) != {r["image_path"] for r in source}:
        raise ValueError("Existing canonical source or fingerprints changed")
    source_ph = np.array([int(by_path[r["image_path"]]["phash64"], 16) for r in source], dtype=np.uint64)
    source_dh = np.array([int(by_path[r["image_path"]]["dhash64"], 16) for r in source], dtype=np.uint64)
    hashes = {}
    for record in source:
        hashes.setdefault(record["sha256"], []).append(record)
    candidates = []
    outcomes = []
    for entry in manifest:
        image_id = entry["image_id"]
        if image_id not in acquired:
            outcomes.append({"image_id": image_id, "status": "not_acquired", "candidate_count": 0})
            continue
        path = ROOT / entry["local_image_path"]
        if sha256(path) != acquired[image_id]["sha256"]:
            raise ValueError(f"Acquired bytes changed: {image_id}")
        ph, dh = fingerprint(path)
        p_dist = POPCOUNT[(source_ph ^ ph).view(np.uint8).reshape(-1, 8)].sum(axis=1)
        d_dist = POPCOUNT[(source_dh ^ dh).view(np.uint8).reshape(-1, 8)].sum(axis=1)
        # Requiring agreement of both hashes limits dHash's many generic-skin
        # false candidates. This retrieval rule has no calibrated sensitivity.
        indices = set(int(i) for i in np.flatnonzero((p_dist <= 10) & (d_dist <= 10)))
        exact = hashes.get(acquired[image_id]["sha256"], [])
        index_by_path = {r["image_path"]: i for i, r in enumerate(source)}
        indices.update(index_by_path[r["image_path"]] for r in exact)
        image_rows = []
        for rank, i in enumerate(sorted(indices, key=lambda i: (int(p_dist[i] + d_dist[i]),
                                                            int(p_dist[i]), source[i]["image_path"]))):
            other = source[i]
            other_path = ROOT / other["image_path"]
            is_exact = acquired[image_id]["sha256"] == other["sha256"]
            geometry = {"geometry_status": "not_run", "method": "", "inlier_count": "", "inlier_ratio": "", "failure_reason": ""}
            if is_exact and sha256(other_path) != other["sha256"]:
                raise ValueError(f"Canonical source hash changed: {other_path}")
            if not is_exact and rank < 5:
                geometry = geometric_evidence(load_gray(path), load_gray(other_path))
            status = "confirmed" if is_exact else "probable" if geometry["geometry_status"] == "coherent" else "uncertain"
            image_rows.append({"pilot_image_id": image_id, "pilot_image_path": entry["local_image_path"],
                               "comparison_path": other["image_path"], "comparison_source": other["source_dataset"],
                               "comparison_image_id": other["image_id"], "comparison_lesion_id": other["lesion_id"],
                               "comparison_patient_id": other["patient_id"], "exact_sha256": is_exact,
                               "phash_distance": int(p_dist[i]), "dhash_distance": int(d_dist[i]),
                               "geometry_status": geometry["geometry_status"], "geometry_method": geometry["method"],
                               "geometry_inliers": geometry["inlier_count"], "geometry_inlier_ratio": geometry["inlier_ratio"],
                               "geometry_failure_reason": geometry["failure_reason"], "classification": status,
                               "human_review_status": "unreviewed"})
        candidates += image_rows
        priority = ("confirmed", "probable", "uncertain")
        status = next((s for s in priority if any(r["classification"] == s for r in image_rows)), "no_candidate")
        outcomes.append({"image_id": image_id, "status": status, "candidate_count": len(image_rows),
                         "phash_nearest": int(p_dist.min()), "dhash_nearest": int(d_dist.min())})
        print(f"screened {image_id}: {status} ({len(image_rows)})", flush=True)
    fields = ("pilot_image_id", "pilot_image_path", "comparison_path", "comparison_source", "comparison_image_id",
              "comparison_lesion_id", "comparison_patient_id", "exact_sha256", "phash_distance", "dhash_distance",
              "geometry_status", "geometry_method", "geometry_inliers", "geometry_inlier_ratio",
              "geometry_failure_reason", "classification", "human_review_status")
    save_csv(OUT / "overlap_candidates.csv", candidates, fields)
    save_csv(OUT / "overlap_by_image.csv", outcomes,
             ("image_id", "status", "candidate_count", "phash_nearest", "dhash_nearest"))
    counts = Counter(r["status"] for r in outcomes)
    (OUT / "overlap_summary.json").write_text(json.dumps({"manifest_sha256": sha256(OUT / "pilot_manifest.csv"),
         "source_manifest_sha256": sha256(SOURCE), "source_fingerprints_sha256": sha256(FINGERPRINTS),
         "acquired": len(acquired), "candidate_pairs": len(candidates), "status_counts": counts,
         "provisionally_usable": counts["no_candidate"],
         "method": "Pilot SHA256 versus frozen Stage4 canonical hashes; pHash<=10 AND dHash<=10; ORB/SIFT RANSAC on five nearest candidates per pilot image. Automated status is provisional; retrieval sensitivity is uncalibrated."}, indent=2) + "\n", encoding="utf-8")
    gallery(candidates)


def gallery(candidates: list[dict]) -> None:
    cards = []
    for i, row in enumerate(candidates, 1):
        a = html.escape(row["pilot_image_path"])
        b = html.escape(row["comparison_path"])
        cards.append(f'<section><h2>Pair {i}: {html.escape(row["classification"])}</h2>'
                     f'<p>pHash {row["phash_distance"]}; dHash {row["dhash_distance"]}; '
                     f'geometry {html.escape(str(row["geometry_status"]))}; inliers {row["geometry_inliers"]}. '
                     f'Automated evidence only; human status: unreviewed.</p>'
                     f'<div class="pair"><figure><a href="../../{a}" target="_blank"><img src="../../{a}"></a><figcaption>{a}</figcaption></figure>'
                     f'<figure><a href="../../{b}" target="_blank"><img src="../../{b}"></a><figcaption>{b}</figcaption></figure></div></section>')
    page = '<!doctype html><meta charset="utf-8"><title>SIIM 2020 pilot candidate review</title>' + \
           '<style>body{font:16px sans-serif;max-width:1400px;margin:auto}.pair{display:flex;gap:1em}' + \
           'figure{width:50%;margin:0}img{max-width:100%;max-height:850px;object-fit:contain}' + \
           'section{border-bottom:2px solid #777;padding:1em}</style><h1>Provisional photographic candidates</h1>' + \
           '<p>Open this file from the repository. Images retain original bytes. Review against the source paths; no decisions are recorded here.</p>' + ''.join(cards)
    (OUT / "review_gallery.html").write_text(page, encoding="utf-8")


def finalize_record() -> None:
    manifest_path = OUT / "pilot_manifest.csv"
    manifest = rows(manifest_path)
    acquisition = rows(OUT / "acquisition.csv")
    verification = rows(OUT / "archive_metadata_verification.csv")
    object_checksums = rows(OUT / "source_object_checksums.csv")
    outcomes = rows(OUT / "overlap_by_image.csv")
    if len(manifest) != 100 or len(acquisition) != 100 or len(outcomes) != 100:
        raise ValueError("Incomplete pilot artifacts")
    attribution = [{"image_id": r["image_id"], "image_level_license": r["license"],
                    "image_level_attribution": r["attribution"], "archive_image_url": r["api_url"],
                    "official_full_image_url": r["file_url"], "download_sha256": r["sha256"]}
                   for r in acquisition]
    save_csv(OUT / "attribution.csv", attribution,
             ("image_id", "image_level_license", "image_level_attribution", "archive_image_url",
              "official_full_image_url", "download_sha256"))
    record = {
        "record_created_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Official SIIM-ISIC 2020 training metadata v2 IDs; official ISIC Archive per-image full URLs",
        "fixed_challenge_jpeg_package_downloaded": False,
        "fixed_package_byte_identity_verified": False,
        "official_challenge_package_cryptographic_checksums_found": False,
        "s3_object_etag_md5_matches": sum(r["status"] == "matched" for r in object_checksums),
        "image_sha256_are_local_download_checksums": True,
        "manifest_sha256": sha256(manifest_path),
        "requested": len(manifest),
        "acquired": sum(r["status"] == "acquired" for r in acquisition),
        "total_download_bytes": sum(int(r["download_bytes"]) for r in acquisition if r["status"] == "acquired"),
        "api_file_size_mismatches": sum(r["api_size_matches_download"] == "False" for r in acquisition),
        "image_level_licenses": dict(Counter(r["license"] for r in acquisition)),
        "archive_metadata_records_matched": sum(r["status"] == "matched" for r in verification),
        "archive_metadata_records_other": len(verification) - sum(r["status"] == "matched" for r in verification),
        "patient_groups": len({r["patient_id"] for r in manifest}),
        "photographic_status_counts": dict(Counter(r["status"] for r in outcomes)),
        "source_manifest_sha256": sha256(SOURCE),
        "source_fingerprints_sha256": sha256(FINGERPRINTS),
        "license_note": "Challenge aggregate CC BY-NC 4.0; per-image Archive rights also recorded. Retain attribution and use only for permitted noncommercial research.",
        "required_aggregate_citation": "International Skin Imaging Collaboration. SIIM-ISIC 2020 Challenge Dataset. International Skin Imaging Collaboration. https://doi.org/10.34970/2020-ds01 (2020).",
    }
    (OUT / "acquisition_and_attribution_record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("select", "acquire", "verify-archive", "verify-s3",
                                           "verify-source", "screen", "finalize"))
    args = parser.parse_args()
    {"select": freeze_manifest, "acquire": acquire, "verify-archive": verify_archive_metadata,
     "verify-s3": verify_s3_etags, "verify-source": verify_canonical_source,
     "screen": screen, "finalize": finalize_record}[args.action]()


if __name__ == "__main__":
    main()
