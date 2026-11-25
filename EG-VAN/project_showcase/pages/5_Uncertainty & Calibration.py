from __future__ import annotations

import csv

import streamlit as st

from showcase_data import EXPLORATORY_LABEL, project_path, relative_reference
from showcase_ui import apply_shared_style, page_header


st.set_page_config(
    page_title="Uncertainty & Calibration",
    page_icon="U",
    layout="wide",
)
apply_shared_style()

page_header(
    "Uncertainty and calibration",
    "Retrospective confidence, entropy, calibration and error-ranking evidence from saved validation probabilities.",
    eyebrow="UNCERTAINTY · SAVED-PROBABILITY ANALYSIS",
)
st.warning(
    f"{EXPLORATORY_LABEL}. These thresholds are descriptive retrospective results, "
    "not validated clinical safety thresholds."
)

experiment_dir = project_path(
    "analysis/nine_class_uncertainty_exploratory/"
    "EXPLORATORY_ONLY_UNCERTAINTY_CALIBRATION_20261116T134405Z"
)
threshold_csv = experiment_dir / "UNCERTAINTY_FIXED_CONFIDENCE_THRESHOLDS.csv"
error_csv = experiment_dir / "UNCERTAINTY_ERROR_DETECTION.csv"
class_csv = experiment_dir / "UNCERTAINTY_CLASSWISE_METRICS.csv"

if not threshold_csv.is_file() or not error_csv.is_file() or not class_csv.is_file():
    st.error("A required uncertainty artifact is unavailable.")
    st.stop()

with threshold_csv.open(newline="", encoding="utf-8") as handle:
    threshold_rows = list(csv.DictReader(handle))
with error_csv.open(newline="", encoding="utf-8") as handle:
    error_rows = list(csv.DictReader(handle))
with class_csv.open(newline="", encoding="utf-8") as handle:
    class_rows = list(csv.DictReader(handle))

st.markdown("### Verified calibration metrics")
metric_values = [
    ("Accuracy", "61.09%", "628 / 1,028"),
    ("ECE", "0.0431", "10-bin equal-width top-label"),
    ("Brier score", "0.5177", "Multiclass"),
    ("NLL", "1.1513", "nats"),
    ("Mean confidence", "0.5824", "Saved probabilities"),
    ("Mean entropy", "1.2414", "nats"),
]
for start in range(0, len(metric_values), 3):
    columns = st.columns(3)
    for column, (label, value, note) in zip(columns, metric_values[start:start + 3]):
        with column:
            st.markdown(
                f'<section class="showcase-panel metric-card"><div class="metric-label">'
                f'{label}</div><div class="metric-value">{value}</div>'
                f'<div class="metric-note">{note}</div></section>',
                unsafe_allow_html=True,
            )

st.markdown("### Error-detection performance")
error_summary = []
for row in error_rows:
    error_summary.append(
        {
            "Score": row["uncertainty_score"].replace("_", " ").title(),
            "AUROC": float(row["error_detection_auroc"]),
            "Average precision": float(row["error_detection_average_precision"]),
        }
    )
st.dataframe(error_summary, hide_index=True, use_container_width=True)

st.markdown("### Confidence retention")
chart_rows = {
    "Retained": [
        int(row["accepted"]) for row in threshold_rows
        if float(row["threshold"]) in (0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
    ],
    "Selective accuracy": [
        float(row["selective_accuracy"]) for row in threshold_rows
        if float(row["threshold"]) in (0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
    ],
}
threshold_table = [
    {
        "Confidence threshold": float(row["threshold"]),
        "Retained": int(row["accepted"]),
        "Coverage": float(row["coverage"]),
        "Selective accuracy": float(row["selective_accuracy"]),
    }
    for row in threshold_rows
]
st.dataframe(threshold_table, hide_index=True, use_container_width=True)
st.caption(
    "Fixed thresholds are loaded from UNCERTAINTY_FIXED_CONFIDENCE_THRESHOLDS.csv."
)

st.markdown("### Key retrospective operating points")
point_columns = st.columns(2)
with point_columns[0]:
    st.markdown(
        '<section class="showcase-panel"><div class="eyebrow">Confidence >= 0.8</div>'
        '<div class="metric-value">310 / 1,028</div>'
        '<div class="metric-note">30.2% coverage · 95.8% observed accuracy</div></section>',
        unsafe_allow_html=True,
    )
with point_columns[1]:
    st.markdown(
        '<section class="showcase-panel"><div class="eyebrow">Confidence >= 0.9</div>'
        '<div class="metric-value">36 / 1,028</div>'
        '<div class="metric-note">3.5% coverage · 100% observed accuracy</div></section>',
        unsafe_allow_html=True,
    )

st.markdown("### Class-wise uncertainty")
class_summary = []
for row in class_rows:
    class_summary.append(
        {
            "Class": row["class_name"],
            "True support": int(row["true_support"]),
            "Predicted count": int(row["predicted_as_class"]),
            "Recall": float(row["recall"]) if row["recall"] else None,
            "Mean confidence": float(row["mean_top_confidence_on_true_class"]),
            "Mean entropy": float(row["mean_entropy_nats_on_true_class"]),
        }
    )
st.dataframe(class_summary, hide_index=True, use_container_width=True)

st.markdown("### Calibration limitations")
st.markdown(
    "- No temperature scaling or calibration fitting was performed.\n"
    "- The 1,023 calibration-partition records have no saved probabilities and remain NOT_APPROVED.\n"
    "- MC dropout was not run; the implementation has no supported dropout layers.\n"
    "- 1,012 / 1,028 images are predicted as NV, dominating aggregate calibration.\n"
    "- ECE depends on top-label binning and is not a clinical risk estimate."
)
st.caption(
    f"Source: `{relative_reference(experiment_dir / 'UNCERTAINTY_EXPERIMENT_REPORT.md')}`"
)
