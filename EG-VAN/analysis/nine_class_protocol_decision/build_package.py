"""Build the compact, decision-free priority-pair review package from frozen evidence."""

import csv
import hashlib
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
COHORT = ROOT / "analysis/nine_class_final_cohort"
PAIRS = COHORT / "acquired_overlap_evidence_v1.csv"
PLAN = COHORT / "candidate_manifest_v2.csv"
ATTRIBUTION = COHORT / "acquired_source_attribution_v1.csv"
EXPECTED = (
    ("ISIC_1412350", "ISIC_3463384"),
    ("ISIC_1163624", "ISIC_2840727"),
    ("ISIC_2846882", "ISIC_8159474"),
    ("ISIC_2523776", "ISIC_8159474"),
)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    source_rows = read_csv(PAIRS)
    selected = {
        (row["left_image_id"], row["right_image_id"]): row
        for row in source_rows
        if row["evidence_class"] == "PROBABLE_PHOTO_RELATION"
        and row["relation_type"].startswith("within_siim")
    }
    if set(selected) != set(EXPECTED) or len(selected) != 4:
        raise ValueError("Priority-pair evidence changed; inspect the frozen source ledger")
    plan = {row["image_id"]: row for row in read_csv(PLAN)}
    attribution = {row["image_id"]: row for row in read_csv(ATTRIBUTION)}
    rows = []
    for index, pair in enumerate(EXPECTED, 1):
        evidence = selected[pair]
        left, right = pair
        for image_id, key in ((left, "left_path"), (right, "right_path")):
            path = ROOT / evidence[key]
            if not path.is_file():
                raise FileNotFoundError(path)
            if sha256(path) != attribution[image_id]["sha256"]:
                raise ValueError(f"Image hash differs from acquired attribution: {image_id}")
        rows.append({
            "review_id": f"P{index:02d}",
            "left_image_id": left,
            "left_path": evidence["left_path"],
            "left_patient_id": plan[left]["patient_id"],
            "left_lesion_id": plan[left]["lesion_id"],
            "right_image_id": right,
            "right_path": evidence["right_path"],
            "right_patient_id": plan[right]["patient_id"],
            "right_lesion_id": plan[right]["lesion_id"],
            "best_transform": evidence["best_transform"],
            "phash_distance": evidence["phash_distance"],
            "dhash_distance": evidence["dhash_distance"],
            "geometry_status": evidence["geometry_status"],
            "geometry_inliers": evidence["geometry_inliers"],
            "automated_evidence_class": evidence["evidence_class"],
            "human_review_status": evidence["human_review_status"],
            "reviewer_decision": "",
            "reviewer_notes": "",
            "reviewer_id": "",
            "review_date": "",
            "evidence_reference": PAIRS.relative_to(ROOT).as_posix(),
        })
    output_csv = OUT / "priority_pair_review.csv"
    if output_csv.exists():
        previous = read_csv(output_csv)
        if any(row.get(field, "").strip() for row in previous
               for field in ("reviewer_decision", "reviewer_notes", "reviewer_id", "review_date")):
            raise RuntimeError("Review ledger has entries; preserve them and do not regenerate")
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    cards = []
    for row in rows:
        def img(side):
            path = "../../" + row[f"{side}_path"]
            title = row[f"{side}_image_id"]
            return (f'<div><a href="{html.escape(path)}" target="_blank">'
                    f'<img src="{html.escape(path)}" alt="Original {title}"></a>'
                    f'<p><a href="{html.escape(path)}" target="_blank">Open original {title}</a></p>'
                    f'<code>{html.escape(row[f"{side}_path"])}</code><br>'
                    f'Patient: {html.escape(row[f"{side}_patient_id"])}; '
                    f'lesion: {html.escape(row[f"{side}_lesion_id"])}</div>')
        cards.append(
            f'<section><h2>{row["review_id"]}: {row["left_image_id"]} / {row["right_image_id"]}</h2>'
            f'<div class="pair">{img("left")}{img("right")}</div>'
            f'<p><strong>Automated, unreviewed:</strong> {html.escape(row["automated_evidence_class"])}; '
            f'pHash {row["phash_distance"]}; dHash {row["dhash_distance"]}; '
            f'best retrieval transform {html.escape(row["best_transform"])}; '
            f'geometry {html.escape(row["geometry_status"])} with {row["geometry_inliers"]} inliers. '
            'These metrics do not establish photographic or lesion identity.</p>'
            '<p><strong>Independent decision:</strong> ____________________ '
            '(SAME_PHOTO / SAME_LESION / DISTINCT / UNCERTAIN)<br>'
            'Reviewer / date: ____________________ Notes: ______________________________</p></section>'
        )
    gallery = ("<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
               "<title>Four priority SIIM image relations — unreviewed</title>"
               "<style>body{font:16px system-ui;margin:2rem;max-width:1100px}section{border-top:2px solid #555;padding:1rem 0 2rem}"
               ".pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.pair img{max-width:100%;max-height:470px;object-fit:contain}"
               "code{overflow-wrap:anywhere;font-size:12px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>"
               "<h1>Four priority SIIM image relations</h1>"
               "<p>Open each original image at full resolution. Thumbnails preserve aspect ratio and have no enhancement. "
               "Judge photographic/lesion relation, not diagnosis. All decisions remain blank. "
               "Recorded patient IDs differ for every pair; this does not resolve visual identity. "
               "Record signed decisions separately in priority_pair_review.csv.</p>"
               + "".join(cards) + "</html>")
    (OUT / "priority_pair_review.html").write_text(gallery, encoding="utf-8")

    ids = sorted({id_ for pair in EXPECTED for id_ in pair})
    with (OUT / "priority_source_attribution.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(attribution[ids[0]]))
        writer.writeheader()
        writer.writerows(attribution[id_] for id_ in ids)
    snapshot = {
        "source_evidence_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in (PAIRS, PLAN, ATTRIBUTION)},
        "priority_pair_count": len(rows),
        "distinct_image_count": len(ids),
        "human_reviewed_pair_count": 0,
        "review_status": "UNREVIEWED",
        "review_gallery": "priority_pair_review.html",
        "review_ledger": "priority_pair_review.csv",
        "aggregate_siim_2020_license": "CC BY-NC 4.0; noncommercial use and attribution required",
        "image_level_licenses": {key: sum(1 for item in attribution.values() if item["image_level_license"] == key)
                                 for key in sorted({item["image_level_license"] for item in attribution.values()})},
        "original_paper_dataset_identity": "UNVERIFIED",
        "dataset_approval": "NONE",
    }
    (OUT / "evidence_snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
