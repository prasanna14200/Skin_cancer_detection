from __future__ import annotations

import csv

import streamlit as st

from showcase_data import EXPLORATORY_LABEL, project_path, relative_reference
from showcase_ui import apply_shared_style, page_header


st.set_page_config(
    page_title="External Validation",
    page_icon="E",
    layout="wide",
)
apply_shared_style()

page_header(
    "External validation feasibility",
    "Local evidence assessed for an independent, genuinely external nine-class evaluation.",
    eyebrow="EXTERNAL VALIDATION · NOT PERFORMED",
)
st.warning(
    f"{EXPLORATORY_LABEL}. A feasibility audit was completed; external model "
    "evaluation was not performed."
)

experiment_dir = project_path(
    "analysis/nine_class_paper_fidelity/"
    "R8_EXTERNAL_VALIDATION_FEASIBILITY_20261116T144628Z"
)
inventory_csv = experiment_dir / "R8_EXTERNAL_DATASET_INVENTORY.csv"
if not inventory_csv.is_file():
    st.error("The external dataset inventory is unavailable.")
    st.stop()

with inventory_csv.open(newline="", encoding="utf-8") as handle:
    inventory = list(csv.DictReader(handle))

status_columns = st.columns(3)
statuses = [
    ("Feasibility audit", "COMPLETED"),
    ("Full external evaluation", "NOT PERFORMED"),
    ("Approved nine-class cohort", "UNAVAILABLE"),
]
for column, (label, value) in zip(status_columns, statuses):
    with column:
        st.markdown(
            f'<section class="showcase-panel metric-card"><div class="metric-label">'
            f'{label}</div><div class="metric-value">{value}</div></section>',
            unsafe_allow_html=True,
        )

st.markdown("### Candidate sources")
for row in inventory:
    dataset = row["dataset"]
    if dataset not in (
        "PH2",
        "SIIM-ISIC 2020 bounded pilot",
        "ISIC 2017 Task 3 metadata",
    ):
        continue
    st.markdown(
        f'<section class="showcase-panel"><div class="eyebrow">{dataset}</div>'
        f'<p><strong>Local status:</strong> {row["local_status"]}</p>'
        f'<p><strong>Source identity:</strong> {row["source_version_or_identity"]}</p>'
        f'<p><strong>Counts:</strong> {row["image_or_metadata_count"]}</p>'
        f'<p><strong>Labels:</strong> {row["source_label_counts"]}</p>'
        f'<p><strong>Candidate mappings:</strong> {row["candidate_mapping_counts"]}</p>'
        f'<p><strong>Rights:</strong> {row["rights_and_use_scope"]}</p>'
        f'<p><strong>Identity / overlap:</strong> {row["identity_and_overlap_status"]}</p>'
        f'<p><strong>Decision:</strong> {row["external_feasibility_decision"]}</p>'
        '</section>',
        unsafe_allow_html=True,
    )

st.markdown("### Why full external validation is blocked")
st.markdown(
    "- No candidate covers all nine EG-VAN source-defined classes.\n"
    "- PH2 has 200 cases: 80 common nevi, 80 atypical nevi and 40 melanomas.\n"
    "- The SIIM–ISIC 2020 pilot has 100 images: 82 unknown diagnoses, 17 nevi and 1 seborrheic keratosis.\n"
    "- ISIC 2017 has 2,750 metadata IDs but no matching local image files.\n"
    "- Perceptual candidate retrieval is not confirmed duplicate adjudication.\n"
    "- Patient/lesion identity bridges and licensing/source receipts are incomplete."
)

st.markdown("### PH2 and SIIM overlap screen")
st.dataframe(
    [
        {"Source": "PH2", "Screened": 200, "Candidate images": 99, "Candidate relations": 580, "Exact overlaps": 0},
        {"Source": "SIIM–ISIC 2020", "Screened": 100, "Candidate images": 68, "Candidate relations": 6448, "Exact overlaps": 0},
        {"Source": "ISIC 2017", "Screened": 2750, "Candidate images": 0, "Candidate relations": 0, "Exact overlaps": 0},
    ],
    hide_index=True,
    use_container_width=True,
)

st.markdown("### Minimum future-study requirements")
st.markdown(
    "1. Pin source versions and permitted-use records.\n"
    "2. Independently review all label mappings.\n"
    "3. Resolve exact and perceptual overlap candidates.\n"
    "4. Establish a genuinely independent all-nine-class cohort.\n"
    "5. Obtain explicit external-validation approval before frozen-checkpoint inference."
)
st.caption(
    f"Source: `{relative_reference(experiment_dir / 'R8_EXTERNAL_FEASIBILITY_REPORT.md')}`"
)
