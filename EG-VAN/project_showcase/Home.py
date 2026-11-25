from __future__ import annotations

import streamlit as st

from showcase_data import (
    CLASS_NAMES,
    EXPLORATORY_LABEL,
    project_path,
    relative_reference,
)
from showcase_ui import apply_shared_style, metric_card, page_header

st.set_page_config(
    page_title="EG-VAN Research Showcase",
    page_icon="EV",
    layout="wide",
    initial_sidebar_state="auto",
)
apply_shared_style()

page_header(
    "EG-VAN — Nine-Class Skin Lesion Classification",
    "An evidence-led tour of the reconstruction, saved exploratory evaluation, "
    "and the limits that still matter.",
    eyebrow="PROJECT SHOWCASE · RESEARCH PROTOTYPE",
)

st.warning(
    f"{EXPLORATORY_LABEL} — not clinically validated, not approved as a leakage-safe "
    "evaluation, and not an exact reproduction of the EG-VAN paper. Do not use for diagnosis."
)

summary_path = project_path(
    "analysis/nine_class_paper_fidelity/"
    "R9_COMPARATIVE_EVIDENCE_ANALYSIS_20261117T015005Z/"
    "COMPARATIVE_ANALYSIS_REPORT.md"
)

hero_left, hero_right = st.columns([1.2, 0.8], gap="large")
with hero_left:
    st.markdown(
        """
        <section class="showcase-panel hero-panel">
          <div class="eyebrow">THE PROJECT IN ONE SENTENCE</div>
          <h2>Reconstruct the model, measure what the saved evidence supports, and make uncertainty visible.</h2>
          <p>
            This project implements an EG-VAN-inspired dual-branch architecture and
            investigates image-quality associations, prediction uncertainty, and
            whether external validation is currently feasible.
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
with hero_right:
    st.markdown(
        """
        <section class="showcase-panel status-panel">
          <div class="eyebrow">CURRENT RESEARCH STATUS</div>
          <h3>Implementation and exploratory evidence exist.</h3>
          <p>Dataset approval, paper fidelity, and independent validation remain incomplete.</p>
          <div class="status-pills">
            <span>IMPLEMENTED</span><span>EXPLORATORY</span><span>NOT APPROVED</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

_, accuracy_column, _ = st.columns([1, 2, 1])
with accuracy_column:
    metric_card(
        "Model Accuracy",
        "61.09%",
        "Verified exploratory validation accuracy · 1,028 samples · not clinically validated.",
    )

st.markdown("### Illustrative Presentation Demo — Not Actual Measured Accuracy")
st.markdown(
    """
    <section class="showcase-panel illustrative-demo"
             aria-label="Illustrative Presentation Demo — Not Actual Measured Accuracy">
      <div class="eyebrow">PRESENTATION MOCKUP · ILLUSTRATIVE ONLY</div>
      <div class="illustrative-layout">
        <div class="illustrative-summary">
          <div class="metric-label">Illustrative accuracy</div>
          <div class="metric-value">80%</div>
          <div class="metric-note">Mockup value only · not measured model performance.</div>
          <div class="illustrative-progress" role="meter" aria-label="Illustrative progress"
               aria-valuemin="0" aria-valuemax="100" aria-valuenow="80">
            <div class="illustrative-progress-fill"></div>
          </div>
          <div class="illustrative-progress-label"><span>0%</span><strong>80%</strong><span>100%</span></div>
        </div>
        <div class="illustrative-ring" role="img" aria-label="Illustrative indicator: 80 percent">
          <div class="illustrative-ring-center"><strong>80%</strong><span>ILLUSTRATIVE</span></div>
        </div>
        <div class="illustrative-chart" role="img" aria-label="Illustrative chart: presentation demo, 80 percent">
          <div class="metric-label">Presentation demo</div>
          <div class="illustrative-chart-row">
            <div class="illustrative-chart-track"><div class="illustrative-chart-fill"></div></div>
            <strong>80%</strong>
          </div>
          <div class="illustrative-chart-axis">
            <span>0%</span><span>20%</span><span>40%</span><span>60%</span><span>80%</span><span>100%</span>
          </div>
          <div class="metric-note">Illustrative scale · not an evaluation result.</div>
        </div>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown("### What we reconstructed")
paper_col, project_col = st.columns(2, gap="large")
with paper_col:
    st.markdown(
        """
        <section class="showcase-panel">
          <div class="eyebrow">PAPER MOTIVATION</div>
          <h3>Combine complementary visual features</h3>
          <p>
            The paper describes parallel EfficientNetV2-S and modified ResNet50
            feature extraction, attention, and multi-feature fusion for skin-lesion
            classification. The source paper reports results; those values are not
            measurements from this project.
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
with project_col:
    st.markdown(
        """
        <section class="showcase-panel">
          <div class="eyebrow">OUR RECONSTRUCTION</div>
          <h3>Implement and test the dataflow</h3>
          <p>
            The nine-class implementation has four paired-scale MFF blocks, SCGA
            and non-local modules in the ResNet branch, plus a nine-logit head.
            Synthetic probes verify tensor shapes and finite gradients—not clinical
            behavior or exact paper parity.
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Nine source-defined output labels")
class_columns = st.columns(9)
for column, name in zip(class_columns, CLASS_NAMES):
    column.markdown(f'<div class="class-chip">{name}</div>', unsafe_allow_html=True)
st.caption(
    "The seven HAM diagnosis labels and the source-defined BENIGN/MALIGNANT labels "
    "are preserved as separate label sources; clinical equivalence is not assumed."
)

st.markdown("### Three additional investigations")
experiments = st.columns(3, gap="medium")
cards = [
    (
        "01 · Image quality",
        "14 raw-image engineering proxies were linked to the saved validation predictions. "
        "Observed associations are not causal findings.",
        "IQA package · 1,028 rows",
    ),
    (
        "02 · Uncertainty",
        "Saved probabilities were used for calibration and error-ranking summaries. "
        "No independent approved calibration set or safe threshold was established.",
        "Uncertainty package · 1,028 rows",
    ),
    (
        "03 · External feasibility",
        "PH2 and a SIIM-ISIC pilot were screened for label compatibility and overlap. "
        "No external model evaluation was performed.",
        "R8 package · feasibility only",
    ),
]
for column, (title, body, footer) in zip(experiments, cards):
    with column:
        st.markdown(
            f"""
            <section class="showcase-panel experiment-card">
              <div class="eyebrow">{title}</div>
              <p>{body}</p>
              <div class="card-foot">{footer}</div>
            </section>
            """,
            unsafe_allow_html=True,
        )

st.markdown("### Project flow")
flow = [
    "Dataset\nand labels",
    "EG-VAN\nreconstruction",
    "Exploratory\nvalidation",
    "IQA",
    "Uncertainty",
    "External\nfeasibility",
    "Comparative\nevidence",
]
flow_columns = st.columns(len(flow))
for index, (column, stage) in enumerate(zip(flow_columns, flow)):
    with column:
        st.markdown(
            f'<div class="flow-step"><span>{index + 1:02d}</span><br>{stage}</div>',
            unsafe_allow_html=True,
        )
        if index < len(flow) - 1:
            st.markdown('<div class="flow-arrow">→</div>', unsafe_allow_html=True)

st.markdown("### Explore the implementation")
st.page_link(
    "pages/1_EG-VAN_Reconstruction_Explorer.py",
    label="Open the EG-VAN reconstruction explorer",
    icon="🧩",
    help="Inspect the source-verified architecture, tensor shapes, and fidelity gaps.",
)
st.markdown("### Research evidence pages")
navigation = st.columns(3)
for column, (path, label) in zip(navigation, [
    ("pages/2_Image_Prediction_Demo.py", "Image Prediction Demo"),
    ("pages/4_Image_Quality_Assessment.py", "Image Quality Assessment"),
    ("pages/5_Uncertainty & Calibration.py", "Uncertainty & Calibration"),
]):
    with column:
        st.page_link(path, label=label)
navigation = st.columns(3)
for column, (path, label) in zip(navigation, [
    ("pages/6_External_Validation.py", "External Validation"),
    ("pages/7_Research_Workflow.py", "Research Workflow"),
    ("pages/8_Results_and_Limitations.py", "Results & Limitations"),
]):
    with column:
        st.page_link(path, label=label)

with st.expander("Evidence and source files"):
    st.markdown(
        f"""
        - Comparative report: `{relative_reference(summary_path)}`
        - Validation metrics: `{relative_reference(project_path('analysis/nine_class_validation_diagnostics/EXPLORATORY_ONLY_VALIDATION_20261112T154709Z_1dca162c/validation_metrics.json'))}`
        - Nine-class implementation: `src/models/egvan/`
        - Synthetic architecture probe: `analysis/nine_class_stage5/architecture_probe.json`
        - Paper-fidelity assessment: `analysis/nine_class_paper_fidelity/R2F_FINAL_PAPER_FIDELITY_MATRIX_20261115T191502Z/R2F_FINAL_ASSESSMENT.md`
        """
    )

st.divider()
st.caption(
    "Evidence is loaded read-only from the repository. This showcase does not train, "
    "fine-tune, approve data, or alter experiment outputs."
)
