from __future__ import annotations

import streamlit as st

from showcase_data import EXPLORATORY_LABEL, get_validation_metrics, project_path, relative_reference
from showcase_ui import apply_shared_style, page_header


st.set_page_config(
    page_title="Results & Limitations",
    page_icon="R",
    layout="wide",
)
apply_shared_style()

page_header(
    "Results, research evidence and limitations",
    "The verified exploratory result set and the unresolved questions that prevent stronger claims.",
    eyebrow="FINAL RESEARCH SUMMARY",
)
st.warning(
    f"{EXPLORATORY_LABEL}. These are validation-only results, not clinical evidence "
    "or exact EG-VAN paper reproduction."
)

metrics = get_validation_metrics()
r9_dir = project_path(
    "analysis/nine_class_paper_fidelity/"
    "R9_COMPARATIVE_EVIDENCE_ANALYSIS_20261117T015005Z"
)

st.markdown("### Model performance")
performance = [
    ("Accuracy", f"{metrics['accuracy']:.2%}", "Saved validation partition"),
    ("Macro-F1", f"{metrics['macro_f1']:.2%}", "Across nine classes"),
    ("Weighted-F1", f"{metrics['weighted_f1']:.2%}", "Saved validation partition"),
    ("Balanced accuracy", f"{metrics['balanced_accuracy']:.2%}", "Mean class recall"),
]
columns = st.columns(4)
for column, (label, value, note) in zip(columns, performance):
    with column:
        st.markdown(
            f'<section class="showcase-panel metric-card"><div class="metric-label">'
            f'{label}</div><div class="metric-value">{value}</div>'
            f'<div class="metric-note">{note}</div></section>',
            unsafe_allow_html=True,
        )

st.markdown("### Validation counts")
count_columns = st.columns(3)
for column, (label, value) in zip(count_columns, [
    ("Validation samples", metrics["n_samples"]),
    ("Correct predictions", metrics["correct"]),
    ("Incorrect predictions", metrics["incorrect"]),
]):
    with column:
        st.markdown(
            f'<section class="showcase-panel metric-card"><div class="metric-label">'
            f'{label}</div><div class="metric-value">{value}</div></section>',
            unsafe_allow_html=True,
        )

st.markdown("### Class prediction distribution")
predicted_counts = []
if "per_class" in metrics:
    pass
validation_metrics = project_path(
    "analysis/nine_class_validation_diagnostics/"
    "EXPLORATORY_ONLY_VALIDATION_20261112T154709Z_1dca162c/"
    "validation_metrics.json"
)
import json
with validation_metrics.open("r", encoding="utf-8") as handle:
    validation = json.load(handle)
for class_index, class_name in enumerate(validation["label_order"]):
    predicted_counts.append(
        sum(row[class_index] for row in validation["confusion_matrix"])
    )
st.dataframe(
    [
        {"Class": class_name, "Predicted count": count}
        for class_name, count in zip(validation["label_order"], predicted_counts)
    ],
    hide_index=True,
    use_container_width=True,
)
maximum_count = max(predicted_counts) or 1
st.markdown(
    '<section class="showcase-panel probability-chart">',
    unsafe_allow_html=True,
)
for class_name, count in zip(validation["label_order"], predicted_counts):
    st.markdown(
        f"""
        <div class="probability-row">
          <div class="probability-label"><span>{class_name}</span><strong>{count}</strong></div>
          <div class="probability-track"><div class="probability-fill" style="width:{count / maximum_count:.2%}"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</section>", unsafe_allow_html=True)
st.markdown(
    f"NV received **{metrics['predicted_nv']} / {metrics['n_samples']} predictions "
    f"({metrics['predicted_nv'] / metrics['n_samples']:.1%})**. "
    "This severe concentration is a class-collapse concern and makes accuracy alone misleading."
)

st.markdown("### Research evidence")
evidence = [
    ("Architecture reconstruction", "Dual-branch implementation exists; paper fidelity remains partial."),
    ("IQA association", "1,028 linked samples; 9 / 14 overall BH-significant proxy comparisons."),
    ("Uncertainty", "ECE 0.0431; entropy error-detection AUROC 0.798."),
    ("External feasibility", "No full-nine-class approved external cohort established."),
    ("Paper fidelity", "Exact paper reproduction not established."),
]
for title, body in evidence:
    st.markdown(
        f'<section class="showcase-panel"><div class="eyebrow">{title}</div>'
        f'<p>{body}</p></section>',
        unsafe_allow_html=True,
    )

st.markdown("### Research limitations")
st.markdown(
    "- Exploratory validation only; split approval and leakage-safe status are not established.\n"
    "- No eligible full-nine-class external evaluation was performed.\n"
    "- 192 repeated overlap-group values cover 429 of 1,028 validation rows.\n"
    "- Patient independence and 471 source-test conflicts remain unresolved.\n"
    "- Six source classes have zero recall; BENIGN/MALIGNANT source semantics remain unapproved.\n"
    "- Exact paper implementation and reported paper results are not reproduced."
)

st.markdown("### Conclusion and future work")
st.markdown(
    "The project accomplished a source-grounded nine-class reconstruction, frozen-checkpoint "
    "validation, IQA association analysis, uncertainty/calibration analysis and external-source "
    "feasibility assessment. The next work requires a protected, independent patient/lesion-safe "
    "cohort, approved label mappings, resolved overlap relationships, frozen calibration setup "
    "and a separately approved external study."
)

st.caption(
    f"Source: `{relative_reference(r9_dir / 'COMPARATIVE_ANALYSIS_REPORT.md')}`"
)
