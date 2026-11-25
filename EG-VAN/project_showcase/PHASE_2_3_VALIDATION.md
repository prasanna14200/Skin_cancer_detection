# Phase 2/3 Validation

**Scope:** Streamlit foundation, Overview, EG-VAN Reconstruction Explorer, and
Phase 4 environment/checkpoint feasibility inspection. Experiment, workflow,
and results pages remain out of scope for this phase.

## Implemented

- `Home.py`: Streamlit entry point and project Overview.
- `pages/1_EG-VAN_Reconstruction_Explorer.py`: interactive component selection,
  forward-pass diagram, synthetic tensor-shape table, and paper/reconstruction
  comparison.
- `showcase_data.py`, `showcase_ui.py`, and `assets/style.css`: shared evidence
  loading, layout, and styling.
- `README.md`, `requirements.txt`, and focused tests.

## Source-grounded architecture checks

- `EGVAN.forward_features()` runs the EfficientNet and modified ResNet branches
  in parallel, then four paired-scale MFF blocks serially with a carry tensor.
- ResNet stages 1/2 use SCGA; stages 3/4 use non-local blocks.
- MFF uses spatial attention on the EfficientNet feature and grouped mean/max
  attention on the ResNet feature, then concatenates them with the optional
  previous fused feature.
- Aggregation aligns and concatenates all four fused outputs and both terminal
  branch maps, projects to 128 channels, globally pools, and applies
  `Linear(128, 9)`.
- Shapes are displayed only with the explicit synthetic-probe qualification.
- The source references and architecture probe are checked for presence at
  runtime and in unit tests.

## Phase 4 inference investigation

- Selected/discovered environment: `E:\Cancerdetection\.venv\Scripts\python.exe`.
- Environment configuration records Python 3.10.11, but its `pyvenv.cfg`
  references the missing base interpreter `E:\AgenticAiCourse\python3.10`.
- The environment's activation command fails (`python` is not recognized), and
  the configured Python executable reports `No Python at
  E:\AgenticAiCourse\python3.10\python.exe`.
- Default Anaconda (`D:\anaconda3\python.exe`) has Streamlit 1.45.1 and Pandas
  2.2.3 but no PyTorch or Torchvision.
- The available standalone uv Python 3.10.16 and 3.12.12 installations have no
  installed PyTorch, Torchvision, Streamlit, or project runtime dependencies.
- The nine-class checkpoint SHA-256 matches the expected
  `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`.
- Checkpoint loading, architecture metadata, class-order runtime verification,
  and real-image inference could not be performed without a working compatible
  Python/PyTorch/Torchvision environment.
- Upload inference is intentionally not exposed. The existing Stage 23 app is
  a different seven-class model and is not substituted.

## Validation status

- Focused data-loader tests: **3 passed** with the available Anaconda Python.
- Syntax check: **5 website Python files parsed successfully**; Pylance reported
  no syntax errors in the entry point, explorer, shared utilities, or test.
- Local Streamlit health endpoint: **HTTP 200 / `ok`**.
- Browser: Overview and Reconstruction Explorer both rendered; sidebar/page
  navigation worked; selecting Non-local attention changed the component
  explanation and source reference; no upload control is present.
- Responsive check at 390×844: both page headings remained visible in the
  browser; a fresh mobile viewport reported a 1px collapsed sidebar and a
  390px main container.
- Screenshots: `screenshots/overview.png`,
  `screenshots/overview_mobile.png`, and
  `screenshots/architecture_explorer.png`.
- An initial mixed-type DataFrame serialization warning was corrected by
  normalizing scale values to strings; the updated page rendered successfully.
- Research images, labels, splits, checkpoints, and experiment evidence were
  not modified by the showcase implementation.
