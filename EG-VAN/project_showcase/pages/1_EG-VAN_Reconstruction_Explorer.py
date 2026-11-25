from __future__ import annotations

import streamlit as st

from showcase_data import CLASS_NAMES, load_json, project_path
from showcase_ui import apply_shared_style, page_header, show_source_reference

st.set_page_config(
    page_title="EG-VAN Reconstruction Explorer",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="auto",
)
apply_shared_style()

page_header(
    "EG-VAN reconstruction explorer",
    "Follow the implemented forward pass from a 384×384 RGB image through paired "
    "feature scales to nine raw class logits.",
    eyebrow="ARCHITECTURE · SOURCE-VERIFIED DATAFLOW",
)
st.info(
    "Tensor shapes below come from a synthetic CPU architecture probe. They verify "
    "shape flow and finite gradients only; they are not real-image performance evidence."
)

probe = load_json("analysis/nine_class_stage5/architecture_probe.json")
if probe.get("logit_shape") != [1, 9] or probe.get("input_shape") != [1, 3, 384, 384]:
    st.error("Architecture probe does not match the documented nine-class input/output contract.")
    st.stop()

st.markdown("### Interactive forward-pass map")
nodes = {
    "Input and preprocessing": (
        "Input is converted to RGB, resized to 384×384 with OpenCV INTER_AREA, "
        "scaled to [0,1], then normalized using ImageNet mean and standard deviation. "
        "The training runner uses this raw-resize mode; Stage 4 hair removal, Gray World "
        "and Retinex are not applied in this run.",
        "Input: image · Output tensor: (1, 3, 384, 384)",
        "src/nine_class_dataset.py · config/nine_class_preprocessing_raw_v2.json",
    ),
    "EfficientNetV2-S branch": (
        "Torchvision EfficientNetV2-S produces four intermediate feature taps. Its weights "
        "are optional in code; the recorded nine-class run used random initialization.",
        "Taps: (1,48,96,96), (1,64,48,48), (1,160,24,24), (1,1280,12,12)",
        "src/models/egvan/efficientnet_branch.py",
    ),
    "Modified ResNet50 branch": (
        "Torchvision ResNet50 provides four stage outputs. The implementation inserts "
        "SCGA after stages 1–2 and non-local blocks after stages 3–4.",
        "Stages: (1,256,96,96), (1,512,48,48), (1,1024,24,24), (1,2048,12,12)",
        "src/models/egvan/modified_resnet50.py",
    ),
    "SCGA attention": (
        "Each SCGA first applies a spatial mask path, then groups channels (default 8) and "
        "uses horizontal/vertical mean and max descriptors to gate the feature groups. "
        "SCGA is also used after each MFF projection.",
        "Inserted after ResNet stages 1 and 2; MFF output tensors have 128 channels.",
        "src/models/egvan/scga.py · src/models/egvan/spatial_attention.py",
    ),
    "Non-local attention": (
        "The embedded-Gaussian block computes query/key/value interactions, subsamples "
        "keys and values by average pooling (stride 2), projects the attended map, and adds "
        "it back through a residual connection.",
        "Inserted after ResNet stages 3 and 4: nominal maps (1,1024,24,24) and (1,2048,12,12).",
        "src/models/egvan/non_local.py",
    ),
    "Four serial MFF blocks": (
        "Each block applies spatial attention to the EfficientNet map, grouped mean/max "
        "attention to the ResNet map, aligns the spatial sizes, concatenates both maps and "
        "the previous fused carry (except at the first scale), then applies depthwise/pointwise "
        "stride-2 convolution, BatchNorm and SCGA.",
        "Probe outputs: (1,128,48,48) → (1,128,24,24) → (1,128,12,12) → (1,128,6,6)",
        "src/models/egvan/mff.py · src/models/egvan/egvan.py",
    ),
    "Aggregation and class head": (
        "The four fused outputs and both terminal branch maps are resized to a common spatial "
        "size, concatenated and projected by a 1×1 convolution. Adaptive average pooling "
        "reduces the map; a Linear(128, 9) layer emits raw logits.",
        f"Combined: {tuple(probe['combined_shape'])} · logits: {tuple(probe['logit_shape'])} "
        f"· output order: {', '.join(CLASS_NAMES)}",
        "src/models/egvan/egvan.py",
    ),
}

selected = st.selectbox("Inspect a component", tuple(nodes), index=0)
purpose, shape, reference = nodes[selected]
detail_col, shape_col = st.columns([1.4, 1], gap="large")
with detail_col:
    st.markdown(f"#### {selected}")
    st.write(purpose)
with shape_col:
    st.markdown("#### Tensor / implementation contract")
    st.code(shape, language="text")
for source_path in reference.split(" · "):
    show_source_reference(source_path)

st.markdown(
    """
    <div class="architecture-panel">
      <div class="arch-node"><strong>Input image</strong><small>RGB · 384×384</small></div>
      <div class="arch-arrow">↓</div>
      <div class="arch-node"><strong>Preprocessing</strong><small>INTER_AREA resize · [0,1] · ImageNet normalization</small></div>
      <div class="arch-arrow">↙ &nbsp;&nbsp;&nbsp; ↘</div>
      <div class="arch-branches">
        <div class="arch-branch">
          <div class="arch-branch-title">Feature branch A</div>
          <div class="arch-node"><strong>EfficientNetV2-S</strong><small>Feature taps at indices (2, 3, 5, 7)</small></div>
        </div>
        <div class="arch-branch">
          <div class="arch-branch-title">Feature branch B</div>
          <div class="arch-node"><strong>Modified ResNet50</strong><small>SCGA → SCGA → non-local → non-local</small></div>
        </div>
      </div>
      <div class="arch-arrow">↘ &nbsp;&nbsp;&nbsp; paired scale features + serial carry &nbsp;&nbsp;&nbsp; ↙</div>
      <div class="arch-node"><strong>Four serial MFF blocks</strong><small>Spatial + grouped attention → depthwise/pointwise stride-2 → SCGA</small></div>
      <div class="arch-arrow">↓</div>
      <div class="arch-node"><strong>Terminal aggregation</strong><small>4 fused maps + 2 terminal branch maps → align → concatenate → 1×1 projection</small></div>
      <div class="arch-arrow">↓</div>
      <div class="arch-node"><strong>Adaptive average pool → Linear(128, 9)</strong><small>Raw logits; softmax is used for reported probabilities</small></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Synthetic architecture-probe tensor shapes")
shape_rows = []
for branch, keys in (
    ("EfficientNetV2-S", ("efficient_shapes",)),
    ("Modified ResNet50", ("resnet_shapes",)),
    ("Serial MFF", ("mff_shapes",)),
):
    for level, tensor_shape in enumerate(probe[keys[0]], start=1):
        shape_rows.append(
            {
                "Path": branch,
                "Scale": str(level),
                "Synthetic probe output": " × ".join(str(dim) for dim in tensor_shape),
                "Evidence type": "Synthetic CPU shape/gradient check",
            }
        )
shape_rows.extend(
    [
        {
            "Path": "Terminal aggregation",
            "Scale": "combined",
            "Synthetic probe output": " × ".join(str(dim) for dim in probe["combined_shape"]),
            "Evidence type": "Synthetic CPU shape/gradient check",
        },
        {
            "Path": "Classifier",
            "Scale": "logits",
            "Synthetic probe output": " × ".join(str(dim) for dim in probe["logit_shape"]),
            "Evidence type": "Synthetic CPU shape/gradient check",
        },
    ]
)
st.dataframe(shape_rows, hide_index=True, use_container_width=True)
st.caption(
    f"Probe: input {probe['input_shape']}; {probe['total_parameters']:,} parameters; "
    f"finite logits={probe['finite_logits']}; finite watched gradients="
    f"{all(probe['watched_gradients_finite'].values())}. "
    "The probe uses synthetic input and randomly initialized weights."
)
show_source_reference("analysis/nine_class_stage5/architecture_probe.json")

st.markdown("### Original paper vs our reconstruction")
comparison = [
    {
        "Component": "Parallel EfficientNetV2-S + modified ResNet50",
        "Project evidence": "Both branches implemented; four taps per branch.",
        "Status": "PARTIALLY RECONSTRUCTED",
        "Open point": "Exact paper tap indices and layer configuration are not uniquely established.",
    },
    {
        "Component": "SCGA",
        "Project evidence": "Spatial and grouped mean/max attention implemented.",
        "Status": "PARTIALLY RECONSTRUCTED",
        "Open point": "Group count and some projection choices are local interpretations.",
    },
    {
        "Component": "Non-local attention",
        "Project evidence": "Embedded-Gaussian residual blocks after ResNet stages 3 and 4.",
        "Status": "IMPLEMENTED; PAPER DETAIL UNRESOLVED",
        "Open point": "Paper-level definition, reduction, and placement are not fully verified.",
    },
    {
        "Component": "MFF and terminal fusion",
        "Project evidence": "Four serial paired-scale blocks plus terminal feature aggregation.",
        "Status": "PARTIALLY RECONSTRUCTED",
        "Open point": "Carry, width, scale pairing, resize, and aggregation are local choices.",
    },
    {
        "Component": "Nine-class head",
        "Project evidence": "Adaptive pooling and Linear(128, 9) raw-logit head.",
        "Status": "IMPLEMENTED",
        "Open point": "Label-source semantics and final cohort mapping remain unapproved.",
    },
    {
        "Component": "Initialization and training",
        "Project evidence": "Exploratory run records random initialization; Adamax/focal/T4 plan.",
        "Status": "IMPLEMENTED; PAPER MATCH UNVERIFIED",
        "Open point": "Run settings are not verified as paper hyperparameters.",
    },
    {
        "Component": "Dataset, augmentation, and split",
        "Project evidence": "Source-defined labels and exploratory four-way assignment.",
        "Status": "UNRESOLVED FOR REPRODUCTION",
        "Open point": "Exact paper cohort, T_j operations, count bridge, and approval are missing.",
    },
]
st.dataframe(comparison, hide_index=True, use_container_width=True)

with st.expander("Implementation status and source references"):
    st.markdown(
        """
        - **Implemented** means the code exists, not that it is clinically validated.
        - **Synthetic verification** means tensor and gradient behavior was checked using synthetic input.
        - **Partially reconstructed** means implementation details or parity with the paper remain uncertain.
        - **Unresolved** means the available paper/project evidence cannot support a faithful claim.
        """
    )
    files = [
        "src/models/egvan/egvan.py",
        "src/models/egvan/efficientnet_branch.py",
        "src/models/egvan/modified_resnet50.py",
        "src/models/egvan/scga.py",
        "src/models/egvan/non_local.py",
        "src/models/egvan/mff.py",
        "src/models/egvan/spatial_attention.py",
        "src/nine_class_dataset.py",
        "src/nine_class_training.py",
        "analysis/nine_class_paper_fidelity/R3_EXISTING_PROJECT_IMPLEMENTATION_AUDIT_20261115T193843Z/R3_EGVAN_ARCHITECTURE_AUDIT.csv",
        "analysis/nine_class_paper_fidelity/R2F_FINAL_PAPER_FIDELITY_MATRIX_20261115T191502Z/R2F_FINAL_ASSESSMENT.md",
    ]
    for relative_path in files:
        exists = project_path(relative_path).is_file()
        st.markdown(f"- `{relative_path}` — {'available' if exists else 'missing'}")

st.divider()
st.caption(
    "This reconstruction is not an exact EG-VAN paper reproduction. The exploratory "
    "checkpoint is not a clinical diagnostic system."
)
