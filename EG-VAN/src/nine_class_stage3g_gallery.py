#!/usr/bin/env python3
"""Create a static original/overlay/difference gallery for Stage 3G review."""

from __future__ import annotations

from html import escape
from pathlib import Path

from nine_class_benign_review import ROOT, atomic_text, read_csv
from nine_class_stage3g_verification import OUTPUT, PAIR_FILE


def run(root: Path = ROOT) -> Path:
    root = root.resolve()
    output = root / OUTPUT / "strong_pair_gallery.html"
    if output.exists():
        raise FileExistsError(f"Preserving existing gallery: {output}")
    rows = read_csv(root / OUTPUT / PAIR_FILE)
    if len(rows) != 83:
        raise ValueError("Expected 83 strong-pair report rows")
    parts = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EG-VAN Stage 3G strong-pair evidence</title><style>
body{font:15px system-ui,sans-serif;margin:1rem auto;max-width:1600px;padding:0 1rem;color:#26323b;background:#f4f6f8}
article{background:white;border:1px solid #d5dce3;margin:1rem 0;padding:1rem;border-radius:8px}
.images{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem}
figure{margin:0}img{width:100%;max-height:350px;object-fit:contain;background:#eee}
figcaption,code{overflow-wrap:anywhere}p{margin:.45rem 0}.warning{background:#fff1d0;padding:.8rem}
@media(max-width:900px){.images{grid-template-columns:1fr}}
</style></head><body><h1>Stage 3G — 83 strong BENIGN/HAM pairs</h1>
<p class="warning">All displayed evidence is provisional. The blue center box in landmark views is a location reference, not a lesion segmentation. Green dots are inside that box and red dots are outside; neither color proves lesion identity. Inspect original images at native resolution before judging a pair.</p>
<p>Three views per pair: binary / registered HAM / blend; fourfold amplified grayscale difference; and inlier locations. The original binary and HAM paths are clickable below. Human decisions remain in the separate Stage 3E ledger.</p>"""]
    for index, row in enumerate(rows, 1):
        def q(value):
            return escape(str(value), quote=True)
        def relative_artifact(field):
            return q(Path(row[field]).relative_to(OUTPUT).as_posix())
        bin_link = q("../../../" + row["original_binary_reference"])
        ham_link = q("../../../" + row["original_ham_reference"])
        parts.append(f"""<article id="pair-{index}">
<h2>{index}. {q(row['binary_image_path'])} — {q(row['ham_image_id'])}</h2>
<p>Source partition: {q(row['source_partition'])}; HAM lesion ID: {q(row['ham_lesion_id'])}; HAM recorded dx: {q(row['ham_dx'])}; original pHash/dHash: {q(row['original_phash_distance'])}/{q(row['original_dhash_distance'])}; original pixel correlation: {q(row['original_pixel_correlation'])}.</p>
<p>RANSAC inliers: {q(row['inlier_count'])}, ratio {q(row['inlier_ratio'])}; corner area ratio {q(row['corner_area_ratio'])}; aligned grayscale correlation {q(row['aligned_grayscale_correlation'])}; central inlier fraction {q(row['central_inlier_fraction'])}. Geometry: <strong>{q(row['transformation_plausibility'])}</strong>. Identity: <strong>{q(row['identity_conclusion_status'])}</strong>. Prior human decision: {q(row['prior_human_decision'] or 'none')}.</p>
<div class="images"><figure><a href="{relative_artifact('overlay_reference')}"><img loading="lazy" src="{relative_artifact('overlay_reference')}" alt="Aligned overlay"></a><figcaption>Binary / registered HAM / blend</figcaption></figure>
<figure><a href="{relative_artifact('difference_reference')}"><img loading="lazy" src="{relative_artifact('difference_reference')}" alt="Amplified grayscale difference"></a><figcaption>Difference, amplified fourfold; gray border is outside valid warp</figcaption></figure>
<figure><a href="{relative_artifact('landmark_reference')}"><img loading="lazy" src="{relative_artifact('landmark_reference')}" alt="Inlier landmark positions"></a><figcaption>Inliers and center-location guide; lesion structure not independently verified</figcaption></figure></div>
<p><a href="{bin_link}">Open original binary image</a> · <a href="{ham_link}">Open original HAM image</a> · Pair ID: <code>{q(row['candidate_pair_id'])}</code></p>
<p>{q(row['review_requirement'])}</p>
</article>""")
    parts.append("</body></html>\n")
    atomic_text(output, "\n".join(parts))
    return output


if __name__ == "__main__":
    print(run())
