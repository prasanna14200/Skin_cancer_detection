from __future__ import annotations

import csv
from pathlib import Path

import streamlit as st

from showcase_data import EXPLORATORY_LABEL, project_path, relative_reference
from showcase_ui import apply_shared_style, metric_card, page_header


st.set_page_config(
    page_title="Image Quality Assessment",
    page_icon="Q",
    layout="wide",
)
apply_shared_style()

page_header(
    "Image Quality Assessment",
    "Exploratory associations between 14 raw-image engineering proxies and saved prediction correctness.",
    eyebrow="IQA · ASSOCIATION ANALYSIS",
)
st.warning(
    f"{EXPLORATORY_LABEL}. These are engineering proxy measurements, not validated "
    "clinical image-quality scores. Associations do not establish causation."
)

experiment_dir = project_path(
    "analysis/nine_class_iqa_exploratory/"
    "EXPLORATORY_ONLY_IQA_ERROR_ASSOCIATION_20261116T081438Z"
)
overall_csv = experiment_dir / "IQA_OVERALL_STATISTICS.csv"
per_image_csv = experiment_dir / "IQA_LINKED_PER_IMAGE.csv"

if not overall_csv.is_file() or not per_image_csv.is_file():
    st.error("The saved IQA statistics or linked per-image artifact is unavailable.")
    st.stop()

with overall_csv.open(newline="", encoding="utf-8") as handle:
    overall_rows = list(csv.DictReader(handle))
with per_image_csv.open(newline="", encoding="utf-8") as handle:
    per_image_reader = csv.DictReader(handle)
    per_image_fields = per_image_reader.fieldnames or []
    per_image_rows = list(per_image_reader)

metrics = st.columns(4)
metric_card = [
    ("Linked samples", "1,028", "628 correct · 400 incorrect"),
    ("Missing IQA values", "0", "0 / 14,392 measurements"),
    ("Overall BH signals", "9 / 14", "Unadjusted global comparisons"),
    ("Eligible tests", "13 / 42", "Overall and within-class tests"),
]
for column, (label, value, note) in zip(metrics, metric_card):
    with column:
        st.markdown(
            f'<section class="showcase-panel metric-card"><div class="metric-label">'
            f'{label}</div><div class="metric-value">{value}</div>'
            f'<div class="metric-note">{note}</div></section>',
            unsafe_allow_html=True,
        )

st.markdown("### Implemented 14 IQA proxy features")
feature_names = [
    "sharpness_laplacian_variance",
    "brightness_mean",
    "contrast_std",
    "underexposed_fraction",
    "overexposed_fraction",
    "rgb_mean_r",
    "rgb_mean_g",
    "rgb_mean_b",
    "rgb_std_r",
    "rgb_std_g",
    "rgb_std_b",
    "color_cast_range",
    "dark_line_fraction",
    "dark_border_fraction",
]
chips = st.columns(4)
for index, name in enumerate(feature_names):
    chips[index % 4].markdown(f'<div class="class-chip">{name}</div>', unsafe_allow_html=True)

st.markdown("### Correct versus incorrect comparison")
available_features = [row["feature"] for row in overall_rows if row["scope"] == "OVERALL"]
selected = st.selectbox("IQA proxy", available_features)
selected_row = next(row for row in overall_rows if row["feature"] == selected)
correct_mean = float(selected_row["correct_mean"])
incorrect_mean = float(selected_row["incorrect_mean"])
comparison = [
    {
        "Group": "Correct",
        "Mean": correct_mean,
        "Median": float(selected_row["correct_median"]),
    },
    {
        "Group": "Incorrect",
        "Mean": incorrect_mean,
        "Median": float(selected_row["incorrect_median"]),
    },
]
st.dataframe(comparison, hide_index=True, use_container_width=True)
maximum = max(correct_mean, incorrect_mean) or 1.0
st.markdown(
    f"""
    <section class="showcase-panel probability-chart">
      <div class="probability-row">
        <div class="probability-label"><span>Correct</span><strong>{correct_mean:.6g}</strong></div>
        <div class="probability-track"><div class="probability-fill" style="width:{correct_mean / maximum:.2%}"></div></div>
      </div>
      <div class="probability-row">
        <div class="probability-label"><span>Incorrect</span><strong>{incorrect_mean:.6g}</strong></div>
        <div class="probability-track"><div class="probability-fill" style="width:{incorrect_mean / maximum:.2%}"></div></div>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)
st.caption(
    f"Rank-biserial effect: {float(selected_row['rank_biserial_correct_minus_incorrect']):.3f}; "
    f"BH q: {float(selected_row['q_value_bh_global']):.3g}. "
    "Values come from the saved global comparison table."
)

st.markdown("### 14-feature adjusted significance summary")
summary = []
for row in overall_rows:
    if row["scope"] != "OVERALL":
        continue
    summary.append(
        {
            "Feature": row["feature"],
            "Rank-biserial": float(row["rank_biserial_correct_minus_incorrect"]),
            "BH q": float(row["q_value_bh_global"]),
            "Passed q < 0.05": float(row["q_value_bh_global"]) < 0.05,
        }
    )
st.dataframe(summary, hide_index=True, use_container_width=True)

st.markdown("### Important findings")
findings = [
    ("Color cast", "Rank-biserial 0.399; BH q 1.66e-25."),
    ("Underexposure", "Rank-biserial -0.320; BH q 1.02e-20."),
    ("Dark-line fraction", "Rank-biserial -0.321; BH q 3.27e-17."),
    ("Within-class scope", "Only BCC and NV had sufficient cases in both correctness groups."),
]
for title, body in findings:
    st.markdown(
        f'<section class="showcase-panel"><div class="eyebrow">{title}</div>'
        f'<p>{body}</p></section>',
        unsafe_allow_html=True,
    )

st.markdown("### Interpretation and limitations")
st.markdown(
    "- Association is not causation.\n"
    "- The strong NV prediction concentration confounds global comparisons.\n"
    "- There are 192 repeated overlap-group values across 429 rows.\n"
    "- Per-class tests are sparse: four NV signals and no confirmatory clinical quality interpretation.\n"
    "- All model records remain EXPLORATORY / NON-CLINICAL."
)

st.caption(
    f"Source: `{relative_reference(experiment_dir / 'IQA_EXPERIMENT_REPORT.md')}`"
)
