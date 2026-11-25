from __future__ import annotations

import streamlit as st

from nine_class_inference import (
    ALLOWED_IMAGE_FORMATS,
    MAX_IMAGE_PIXELS,
    load_predictor,
    predict_upload,
)
from showcase_data import CLASS_NAMES, EXPLORATORY_LABEL
from showcase_ui import apply_shared_style, page_header


st.set_page_config(
    page_title="Image Prediction Demo",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="auto",
)
apply_shared_style()

page_header(
    "Nine-class image prediction demo",
    "A technical demonstration using the frozen exploratory EG-VAN checkpoint.",
    eyebrow="MODEL INFERENCE · EXPERIMENTAL",
)
st.warning(
    f"{EXPLORATORY_LABEL}. This model is not clinically validated or approved for "
    "medical use. Predictions must not be used for diagnosis, treatment, or care decisions."
)
st.markdown(
    "The nine outputs preserve source-defined labels. In particular, BENIGN and "
    "MALIGNANT are not treated as interchangeable or equivalent to the HAM diagnosis labels."
)

try:
    predictor = load_predictor()
except (FileNotFoundError, OSError, ValueError, KeyError, RuntimeError, TypeError) as exc:
    st.error(f"Nine-class inference is unavailable: {exc}")
    st.stop()

st.caption(
    "Checkpoint SHA-256 verified: "
    f"`{predictor.checkpoint_sha256}` · strict state-dictionary load · CPU inference"
)
uploaded_file = st.file_uploader(
    "Choose a lesion image (JPEG or PNG)",
    type=("jpg", "jpeg", "png"),
    help=(
        "Files are processed in memory and are not written to the project. "
        "Limits: 20 MiB and 25 megapixels."
    ),
)

if uploaded_file is not None:
    try:
        preview, probabilities = predict_upload(uploaded_file.getvalue())
    except (OSError, ValueError, RuntimeError) as exc:
        st.error(f"Unable to run this image: {exc}")
    else:
        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        image_column, results_column = st.columns([1, 1.2], gap="large")
        with image_column:
            st.image(
                preview,
                caption="RGB image after the checkpoint's resize preprocessing",
                use_container_width=True,
            )
        with results_column:
            st.markdown("### Predicted class")
            st.metric(ranked[0][0], f"{ranked[0][1]:.1%}")
            st.markdown("### Top three outputs")
            top_columns = st.columns(3)
            for column, (class_name, probability) in zip(top_columns, ranked[:3]):
                column.metric(class_name, f"{probability:.1%}")

        st.markdown("### All nine class probabilities")
        st.markdown('<div class="probability-chart">', unsafe_allow_html=True)
        for class_name, probability in sorted(
            probabilities.items(), key=lambda item: item[1], reverse=True
        ):
            st.markdown(
                f"""
                <div class="probability-row">
                  <div class="probability-label">
                    <span>{class_name}</span><strong>{probability:.2%}</strong>
                  </div>
                  <div class="probability-track">
                    <div class="probability-fill" style="width:{probability:.2%}"></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.dataframe(
            [
                {"Class": class_name, "Probability": f"{probability:.2%}"}
                for class_name, probability in ranked
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "Probabilities are model softmax outputs, not calibrated clinical risks. "
            f"Accepted image formats: {', '.join(sorted(ALLOWED_IMAGE_FORMATS))}; "
            f"maximum dimensions: {MAX_IMAGE_PIXELS:,} pixels."
        )
