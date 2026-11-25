from __future__ import annotations

import streamlit as st

from showcase_data import EXPLORATORY_LABEL
from showcase_ui import apply_shared_style, page_header


st.set_page_config(
    page_title="Research Workflow",
    page_icon="W",
    layout="wide",
)
apply_shared_style()

page_header(
    "Research workflow and implementation",
    "A source-linked view of implemented, evaluated and blocked project stages.",
    eyebrow="WORKFLOW · DATA FLOW",
)
st.warning(
    f"{EXPLORATORY_LABEL}. This diagram describes implementation and evidence flow, "
    "not an approved clinical workflow."
)

stages = [
    ("01 · Dataset preparation", "Implemented / not approved", "Four-way exploratory source inventory and manifest preparation.", "src/nine_class_stage4.py"),
    ("02 · Preprocessing", "Implemented", "384×384 RGB, INTER_AREA resize and ImageNet normalization.", "src/nine_class_dataset.py"),
    ("03 · Nine-class labels", "Implemented / semantic gaps", "Nine source-defined labels without fabricated label equivalence.", "src/nine_class_stage4.py"),
    ("04 · EG-VAN architecture", "Implemented / partial fidelity", "EfficientNetV2-S, modified ResNet50, SCGA, non-local, MFF and nine-logit head.", "src/models/egvan/"),
    ("05 · Feature extraction", "Implemented", "Paired branch feature maps at four spatial scales.", "src/models/egvan/efficientnet_branch.py · src/models/egvan/modified_resnet50.py"),
    ("06 · Feature fusion", "Implemented / paper detail unresolved", "Serial MFF carry and terminal projection.", "src/models/egvan/mff.py · src/models/egvan/egvan.py"),
    ("07 · Model training", "Exploratory / evidence incomplete", "Adamax, focal loss and 25-epoch configuration exist; run history is incomplete.", "src/nine_class_training.py"),
    ("08 · Checkpoint generation", "Generated / frozen", "Strict checkpoint integrity verified as EXPLORATORY_ONLY.", "analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt"),
    ("09 · Validation", "Experimentally evaluated", "Saved validation-only metrics and confusion matrix.", "analysis/nine_class_validation_diagnostics/"),
    ("10 · IQA analysis", "Experimentally evaluated", "Retrospective association of 14 raw-image proxies with correctness.", "analysis/nine_class_iqa_exploratory/EXPLORATORY_ONLY_IQA_ERROR_ASSOCIATION_20261116T081438Z/"),
    ("11 · Uncertainty analysis", "Experimentally evaluated", "Saved-probability calibration, error ranking and risk coverage.", "analysis/nine_class_uncertainty_exploratory/EXPLORATORY_ONLY_UNCERTAINTY_CALIBRATION_20261116T134405Z/"),
    ("12 · External feasibility", "Assessed / blocked", "PH2, SIIM–ISIC and ISIC 2017 screened; no eligible full-nine-class cohort.", "analysis/nine_class_paper_fidelity/R8_EXTERNAL_VALIDATION_FEASIBILITY_20261116T144628Z/"),
    ("13 · Streamlit deployment", "Implemented", "Evidence display and genuine CPU checkpoint inference.", "project_showcase/"),
]

st.markdown("### End-to-end data flow")
flow = [
    "Source images",
    "384 × 384 RGB preprocessing",
    "EfficientNet / ResNet branches",
    "SCGA / non-local / MFF",
    "Nine logits",
    "Saved validation probabilities",
    "IQA + uncertainty analyses",
]
columns = st.columns(len(flow))
for index, (column, label) in enumerate(zip(columns, flow)):
    with column:
        st.markdown(
            f'<section class="showcase-panel metric-card"><div class="metric-label">'
            f'{index + 1:02d}</div><div class="metric-note">{label}</div></section>',
            unsafe_allow_html=True,
        )

st.markdown("### Component status")
for title, status, explanation, source in stages:
    with st.expander(f"{title} — {status}"):
        st.write(explanation)
        st.caption(f"Reference: `{source}`")

st.markdown("### Interpretation rules")
st.markdown(
    "- **Implemented** means code or artifacts exist; it does not imply clinical approval.\n"
    "- **Experimentally evaluated** means a completed exploratory analysis of existing evidence.\n"
    "- **Partial reconstruction** means architecture or paper details remain unresolved.\n"
    "- **Blocked** means the project lacks an approved cohort or another prerequisite."
)
