"""Prepare a blinded 19-pair source-test review package and validate later decisions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from PIL import Image

from nine_class_stage4 import ROOT

OUTPUT = Path("analysis/nine_class_stage11a")
STRONG = Path("analysis/nine_class_recovery/stage3g/strong_pair_identity_evidence.csv")
AI = Path("analysis/nine_class_recovery/stage3i/ai_pair_review.csv")
SHEETS = Path("analysis/nine_class_recovery/stage3i/sheet_manifest.csv")
INVENTORY = Path("analysis/nine_class_stage4/nine_class_source_manifest.csv")
DECISIONS = {"SAME_PHOTO", "DISTINCT_PHOTO", "UNCERTAIN"}
LEDGER_FIELDS = ("review_id", "image_a_identifier", "image_b_identifier",
                 "reviewer_decision", "reviewer_notes", "reviewer_identity_or_code",
                 "review_date_utc", "evidence_reference")
MAPPING_FIELDS = ("review_id", "candidate_pair_id", "binary_image_path", "ham_image_path",
                  "binary_source_split", "ham_image_id", "ham_lesion_id", "binary_sha256",
                  "ham_sha256", "binary_dimensions", "ham_dimensions", "source_evidence_reference",
                  "additional_candidate_relations", "additional_uncertain_relations")
RELATION_FIELDS = ("review_id", "candidate_pair_id", "binary_image_path", "ham_candidate_path",
                   "relation_review_status", "original_evidence_reference")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def csv_text(rows: list[dict[str, str]], fields: tuple[str, ...]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def original_image(root: Path, relative: str, expected_sha: str) -> str:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or unsafe original image: {relative}")
    if sha256(path) != expected_sha:
        raise ValueError(f"Original image hash mismatch: {relative}")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        dimensions = f"{image.width}x{image.height}"
    return dimensions


def collect_pairs(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], dict]:
    strong = read_csv(root / STRONG)
    all_pairs = read_csv(root / AI)
    sheet = {r["candidate_pair_id"]: r for r in read_csv(root / SHEETS)}
    inventory = {r["image_path"]: r for r in read_csv(root / INVENTORY)}
    protected = [r for r in strong if r["source_partition"] == "test" and
                 r["binary_image_path"].startswith("data/isic/data/test/benign/")]
    if len(protected) != 19 or len({r["candidate_pair_id"] for r in protected}) != 19 or len({r["binary_image_path"] for r in protected}) != 19:
        raise ValueError("Expected exactly 19 distinct protected strong-pair records")
    by_binary = defaultdict(list)
    for pair in all_pairs:
        by_binary[pair["binary_image_path"]].append(pair)
    mapping, additional, related_issues = [], [], []
    for position, pair in enumerate(sorted(protected, key=lambda r: r["candidate_pair_id"]), 1):
        review_id = f"R{position:02d}"
        pair_id = pair["candidate_pair_id"]
        binary, ham = pair["binary_image_path"], pair["ham_candidate_path"]
        if pair_id not in sheet or sheet[pair_id]["binary_image_path"] != binary or sheet[pair_id]["candidate_path"] != ham:
            raise ValueError(f"Ambiguous Stage 3I mapping: {pair_id}")
        if binary not in inventory or ham not in inventory:
            raise ValueError(f"Missing source inventory record: {pair_id}")
        if inventory[binary]["source_split"] != "test" or inventory[binary]["class_name"] != "BENIGN" or inventory[ham]["source_dataset"] != "HAM10000":
            raise ValueError(f"Source label or partition mismatch: {pair_id}")
        binary_sha, ham_sha = sheet[pair_id]["binary_sha256"], sheet[pair_id]["candidate_sha256"]
        if binary_sha != inventory[binary]["sha256"] or ham_sha != inventory[ham]["sha256"]:
            raise ValueError(f"Frozen inventory/sheet SHA mismatch: {pair_id}")
        binary_size = original_image(root, binary, binary_sha)
        ham_size = original_image(root, ham, ham_sha)
        if binary_size != sheet[pair_id]["binary_dimensions"] or ham_size != sheet[pair_id]["candidate_dimensions"]:
            raise ValueError(f"Frozen image dimensions mismatch: {pair_id}")
        related = [r for r in by_binary[binary] if r["candidate_pair_id"] != pair_id]
        if len({r["candidate_pair_id"] for r in related}) != len(related):
            raise ValueError(f"Duplicate candidate relation: {binary}")
        for relation in related:
            candidate = relation["candidate_path"]
            if candidate not in inventory or inventory[candidate]["sha256"] != relation["original_candidate_sha256"]:
                related_issues.append({"candidate_pair_id": relation["candidate_pair_id"],
                                       "issue": "MISSING_OR_HASH_MISMATCHED_INVENTORY_RECORD"})
            else:
                try:
                    original_image(root, candidate, relation["original_candidate_sha256"])
                except (ValueError, OSError) as error:
                    related_issues.append({"candidate_pair_id": relation["candidate_pair_id"],
                                           "issue": str(error)})
            additional.append({"review_id": review_id, "candidate_pair_id": relation["candidate_pair_id"],
                               "binary_image_path": binary, "ham_candidate_path": relation["candidate_path"],
                               "relation_review_status": "NOT_REVIEWED_IN_STAGE11A",
                               "original_evidence_reference": AI.as_posix()})
        mapping.append({"review_id": review_id, "candidate_pair_id": pair_id,
                        "binary_image_path": binary, "ham_image_path": ham,
                        "binary_source_split": "test", "ham_image_id": pair["ham_image_id"],
                        "ham_lesion_id": pair["ham_lesion_id"], "binary_sha256": binary_sha,
                        "ham_sha256": ham_sha, "binary_dimensions": binary_size, "ham_dimensions": ham_size,
                        "source_evidence_reference": STRONG.as_posix(),
                        "additional_candidate_relations": str(len(related)),
                        "additional_uncertain_relations": str(sum(r["ai_assessment"] == "AI_UNCERTAIN" for r in related))})
    info = {"primary_pairs": len(mapping), "unique_protected_binary_images": len({r["binary_image_path"] for r in mapping}),
            "additional_candidate_relations_not_reviewed": len(additional),
            "additional_uncertain_relations_not_reviewed": sum(int(r["additional_uncertain_relations"]) for r in mapping),
            "binary_images_with_additional_relations": sum(int(r["additional_candidate_relations"]) > 0 for r in mapping),
            "additional_relation_evidence_issues": related_issues}
    return mapping, additional, info


def initial_ledger(mapping: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{"review_id": r["review_id"], "image_a_identifier": f"{r['review_id']}-A",
             "image_b_identifier": f"{r['review_id']}-B", "reviewer_decision": "", "reviewer_notes": "",
             "reviewer_identity_or_code": "", "review_date_utc": "",
             "evidence_reference": f"gallery.html#{r['review_id']}"} for r in mapping]


def render_gallery(mapping: list[dict[str, str]]) -> str:
    cards = []
    for row in mapping:
        rid = row["review_id"]
        a = f"originals/{rid}-A.jpg"
        b = f"originals/{rid}-B.jpg"
        cards.append(f'''<section id="{rid}"><h2>{rid}</h2><div class="pair">
<figure><figcaption>Image A · {html.escape(row['binary_dimensions'])}</figcaption><a href="{a}" target="_blank"><img src="{a}" alt="{rid} Image A original"></a></figure>
<figure><figcaption>Image B · {html.escape(row['ham_dimensions'])}</figcaption><a href="{b}" target="_blank"><img src="{b}" alt="{rid} Image B original"></a></figure></div>
<label>Decision <select data-id="{rid}"><option value="">Unreviewed</option><option value="SAME_PHOTO">SAME_PHOTO</option><option value="DISTINCT_PHOTO">DISTINCT_PHOTO</option><option value="UNCERTAIN">UNCERTAIN</option></select></label>
<label>Notes <textarea data-notes="{rid}" rows="2" placeholder="Landmarks, crop, artifacts or reason for uncertainty"></textarea></label></section>''')
    data = json.dumps(initial_ledger(mapping)).replace("<", "\\u003c")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Stage 11A blinded photo comparison</title>
<style>body{{font:16px system-ui,sans-serif;margin:2rem;background:#f5f5f5;color:#18212b}}main{{max-width:1350px;margin:auto}}section{{background:#fff;padding:1.4rem;margin:2rem 0;border:1px solid #aab3bb;border-radius:8px}}.pair{{display:flex;gap:1.5rem;align-items:flex-start;overflow-x:auto}}figure{{margin:0;flex:none}}figcaption{{font-weight:600;margin-bottom:.5rem}}img{{width:auto;height:auto;max-width:none;display:block;border:1px solid #888}}label{{display:block;margin:1rem 0}}textarea{{display:block;width:min(100%,70rem)}}button{{padding:.7rem 1.1rem}}.note{{background:#eaf1fa;padding:1rem}}</style></head><body><main><h1>Stage 11A: original-image pair review</h1>
<p class="note">Judge only whether A and B are the same photograph. View each image at native pixel dimensions; click to open its unchanged original file. Do not infer diagnosis, patient identity or dataset eligibility. Previous automated assessments are intentionally hidden. Decisions start blank.</p>
<label>Reviewer identity or code <input id="reviewer" autocomplete="off" required></label><label>Review date/time UTC (ISO 8601) <input id="reviewdate" placeholder="2026-10-22T12:00:00Z" required></label>
<button type="button" onclick="exportCsv()">Download decision CSV</button><span id="progress"></span>
{''.join(cards)}<button type="button" onclick="exportCsv()">Download decision CSV</button>
<script>const template={data};
function csvCell(v){{return '"'+String(v??'').replaceAll('"','""')+'"';}}
function updateProgress(){{document.getElementById('progress').textContent=' '+document.querySelectorAll('select[data-id] option:checked:not([value=""])').length+' / 19 decisions entered';}}
document.querySelectorAll('select[data-id]').forEach(s=>s.addEventListener('change',updateProgress));
function exportCsv(){{let reviewer=document.getElementById('reviewer').value.trim(), date=document.getElementById('reviewdate').value.trim();
let rows=template.map(r=>{{let id=r.review_id, choice=document.querySelector('select[data-id="'+id+'"]').value, notes=document.querySelector('textarea[data-notes="'+id+'"]').value;
return {{...r,reviewer_decision:choice,reviewer_notes:choice?notes:'',reviewer_identity_or_code:choice?reviewer:'',review_date_utc:choice?date:''}};}});
if(rows.some(r=>r.reviewer_decision) && (!reviewer||!date)){{alert('Enter reviewer code and UTC review date before export.');return;}}
let fields=Object.keys(template[0]), content=[fields.map(csvCell).join(','),...rows.map(r=>fields.map(f=>csvCell(r[f])).join(','))].join('\\r\\n')+'\\r\\n';
let link=document.createElement('a'), url=URL.createObjectURL(new Blob([content],{{type:'text/csv;charset=utf-8'}}));link.href=url;link.download='stage11a_completed_review.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}}
updateProgress();</script></main></body></html>'''


def copy_neutral_originals(root: Path, destination: Path, mapping: list[dict[str, str]]) -> int:
    """Copy JPEG bytes unchanged so the blinded gallery works without source paths."""
    target = destination / "originals"
    target.mkdir(parents=True, exist_ok=False)
    for row in mapping:
        for side, field, digest in (("A", "binary_image_path", "binary_sha256"),
                                    ("B", "ham_image_path", "ham_sha256")):
            source = root / row[field]
            output = target / f"{row['review_id']}-{side}.jpg"
            with source.open("rb") as input_handle, output.open("xb") as output_handle:
                shutil.copyfileobj(input_handle, output_handle)
            if sha256(output) != row[digest]:
                raise ValueError(f"Neutral original copy hash mismatch: {output}")
    return 2 * len(mapping)


def validate_decisions(ledger: list[dict[str, str]], mapping: list[dict[str, str]]) -> dict:
    expected = {r["review_id"]: r for r in mapping}
    if len(ledger) != len(expected) or set(r.get("review_id", "") for r in ledger) != set(expected):
        raise ValueError("Decision ledger must contain exactly one row per review ID")
    if any(set(row) != set(LEDGER_FIELDS) for row in ledger):
        raise ValueError("Decision ledger columns changed")
    outcomes = Counter()
    statuses = []
    for row in ledger:
        rid = row["review_id"]
        source = expected[rid]
        if (row["image_a_identifier"] != f"{rid}-A" or row["image_b_identifier"] != f"{rid}-B" or
            row["evidence_reference"] != f"gallery.html#{rid}"):
            raise ValueError(f"Decision evidence or identifiers changed: {rid}")
        decision = row["reviewer_decision"].strip()
        if decision and decision not in DECISIONS:
            raise ValueError(f"Invalid reviewer decision: {rid}")
        if decision:
            if not row["reviewer_identity_or_code"].strip() or not row["review_date_utc"].strip():
                raise ValueError(f"Reviewed row lacks reviewer or UTC date: {rid}")
            date = row["review_date_utc"].strip()
            try:
                parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError(f"Invalid UTC review date: {rid}") from error
            if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
                raise ValueError(f"Review date must be UTC: {rid}")
            outcomes[decision] += 1
        elif any(row[key].strip() for key in ("reviewer_notes", "reviewer_identity_or_code", "review_date_utc")):
            raise ValueError(f"Unreviewed row contains decision metadata: {rid}")
        statuses.append({"review_id": rid, "binary_image_path": source["binary_image_path"],
                         "primary_pair_decision": decision or "UNREVIEWED",
                         "additional_candidate_relations_not_adjudicated": int(source["additional_candidate_relations"]),
                         "remaining_photo_identity_blocker": decision != "DISTINCT_PHOTO" or
                              int(source["additional_candidate_relations"]) > 0,
                         "approved_eligible": False})
    return {"total_primary_pairs": len(expected), "reviewed_pairs": sum(outcomes.values()),
            "unreviewed_pairs": len(expected) - sum(outcomes.values()),
            "decision_counts": {name: outcomes[name] for name in sorted(DECISIONS)},
            "remaining_primary_or_related_photo_review_blockers": sum(r["remaining_photo_identity_blocker"] for r in statuses),
            "records": sorted(statuses, key=lambda r: r["review_id"]),
            "dataset_approval_created": False,
            "interpretation": "Pair decisions only; DISTINCT_PHOTO does not establish different lesions, patients, rights or dataset eligibility"}


def create_package(root: Path = ROOT, output: Path = OUTPUT) -> dict:
    root = root.resolve()
    destination = (root / output).resolve()
    if not destination.is_relative_to(root / "analysis/nine_class_stage11a"):
        raise ValueError("Stage 11A output must stay under its analysis directory")
    if destination.exists():
        raise FileExistsError(destination)
    mapping, related, info = collect_pairs(root)
    ledger = initial_ledger(mapping)
    gallery = render_gallery(mapping)
    source_hashes = {path.as_posix(): sha256(root / path) for path in (STRONG, AI, SHEETS, INVENTORY)}
    destination.mkdir(parents=True, exist_ok=False)
    neutral_copy_count = copy_neutral_originals(root, destination, mapping)
    (destination / "gallery.html").write_text(gallery, encoding="utf-8")
    (destination / "decision_ledger.csv").write_text(csv_text(ledger, LEDGER_FIELDS), encoding="utf-8")
    (destination / "review_id_mapping.csv").write_text(csv_text(mapping, MAPPING_FIELDS), encoding="utf-8")
    (destination / "additional_candidate_relations.csv").write_text(csv_text(related, RELATION_FIELDS), encoding="utf-8")
    info.update(source_sha256=source_hashes, missing_original_images=len(info["additional_relation_evidence_issues"]),
                ambiguous_primary_mappings=0,
                reviewer_decisions_recorded=0, review_gallery_has_prior_ai_assessments=False,
                neutral_original_byte_identical_copies=neutral_copy_count,
                visual_presentation="HTML displays byte-identical neutral-name JPEG copies at native pixel dimensions; no enhancement")
    (destination / "package_manifest.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    (destination / "initial_validation.json").write_text(json.dumps(validate_decisions(ledger, mapping), indent=2) + "\n", encoding="utf-8")
    if any(sha256(root / path) != digest for path, digest in source_hashes.items()):
        raise ValueError("Source evidence changed during package creation")
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--validate", type=Path, help="Validate a later reviewer-exported CSV")
    parser.add_argument("--summary-out", type=Path, help="New JSON path for a later review summary")
    args = parser.parse_args()
    if args.validate:
        if args.summary_out and args.summary_out.exists():
            raise FileExistsError(args.summary_out)
        mapping = read_csv(args.root / args.output / "review_id_mapping.csv")
        result = validate_decisions(read_csv(args.validate), mapping)
        if args.summary_out:
            args.summary_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: result[key] for key in ("total_primary_pairs", "reviewed_pairs", "unreviewed_pairs", "decision_counts", "remaining_primary_or_related_photo_review_blockers")}, indent=2))
    elif args.summary_out:
        parser.error("--summary-out requires --validate")
    else:
        print(json.dumps(create_package(args.root, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
