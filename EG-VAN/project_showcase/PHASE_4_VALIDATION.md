# EG-VAN Showcase — Phase 4 Validation

**Status:** EXPLORATORY / NON-CLINICAL

This report documents the real nine-class model-inference implementation and
the Streamlit validation performed on 2026-11-22.

## Environment discovered

- Project environment: `project_showcase/.venv`
- Python: 3.13.5
- Platform execution: Windows CPU
- Torch: 2.14.0+cpu
- Torchvision: 0.29.0+cpu
- NumPy: 2.2.6
- OpenCV: 5.0.0.93
- Pillow: 11.3.0
- Streamlit: 1.45.1
- PyTorch CUDA availability: false

The original training Python/Torch/Torchvision versions are not recoverable
from the saved run provenance. The old project `.venv` was unusable because it
referenced a removed interpreter and its packages were CPython 3.10 wheels.
Dependencies were installed only in the dedicated showcase environment.

## Checkpoint loading result

- Checkpoint:
  `analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt`
- Verified SHA-256:
  `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`
- Training configuration hash matched run provenance.
- Preprocessing hash matched run provenance.
- Canonical class order matched:
  `AKIEC, BCC, BKL, DF, MEL, NV, VASC, BENIGN, MALIGNANT`
- The checkpoint loaded with `torch.load(..., weights_only=True, mmap=True)`
  and the actual nine-class EG-VAN model's `load_state_dict(..., strict=True)`.
- No missing or unexpected state-dictionary keys were reported.

## Real-image inference result

One controlled CPU smoke test used the existing authorized validation image
`data/raw/HAM10000_images_part_1/ISIC_0025837.jpg`.

- Preprocessed input shape: `(1, 3, 384, 384)`
- Logit shape: `(1, 9)`
- Probability shape: `(1, 9)`
- Probability sum: `1.0`
- All logits and probabilities finite: yes
- Top result: `NV`, `29.93937134742737%`
- Top three: `NV 29.9394%`, `AKIEC 13.4209%`, `BCC 11.6781%`

This smoke test demonstrates technical loading and inference only. It is not a
new held-out accuracy measurement and does not establish clinical validity.

## Image Prediction Demo

The new page:

- accepts JPEG and PNG uploads;
- enforces a 20 MiB application limit and a 25-megapixel dimension guard;
- processes images in memory;
- uses the exact raw RGB 384×384/ImageNet preprocessing configuration;
- displays the uploaded preview, predicted class, top three outputs, nine
  probability bars, and a nine-row probability table;
- shows an explicit EXPLORATORY / NON-CLINICAL disclaimer.

The demo does not use the seven-class application inference module or its
checkpoint.

## Tests and outcomes

- Showcase test suite: **9 passed**
- Dependency consistency: `pip check` reported no broken requirements.
- Tests cover:
  - saved evidence and source paths;
  - preprocessing parity with `nine_class_dataset.image_tensor`;
  - invalid/empty uploads;
  - unsupported image formats;
  - oversized file and dimension rejection;
  - strict checkpoint loading;
  - canonical nine-class order;
  - finite nine-class probability output and sum.

## UI contrast and layout

The main EG-VAN heading and the prediction-page heading computed to
`rgb(255, 255, 255)` on the dark theme. Navigation labels retain white text.
Muted body text remains distinct from the dark background.

Browser validation used a live 1280×900 desktop viewport and 390×844 mobile
viewport:

- desktop horizontal overflow: none;
- mobile horizontal overflow: none;
- the Upload interface rendered;
- a controlled real image produced the predicted class and nine probability bars;
- the page retained the experimental disclaimer.

Screenshots:

- `screenshots/phase4_prediction_desktop.png`
- `screenshots/phase4_prediction_mobile.png`

## Integrity

The checkpoint SHA-256 remained unchanged. No source image, split, checkpoint,
validation prediction, or existing experiment evidence was modified by Phase 4.
The temporary `.install-tmp` directory is targeted for cleanup after package
installation. The isolated `.venv` remains available for local execution.

Verified Phase 4 evidence hashes:

- validation predictions:
  `fb46054fa919de0b3f9774f2e6a97546900c2e0edbde584125e622cf253f1b96`
- controlled validation image:
  `45747fb90400d33085cce05fb2298b7c8a6aa06d52e29860fc2c7219798ced98`
- desktop screenshot:
  `7d5c74c9362e4699943266ba4f0b9a678660ef53fc9dbc67daffb755d0a91451`
- mobile screenshot:
  `eeee571347bece96861e248fdf6bf2efe045b073a8b5b77ac8a8201df887ace5`

## Remaining blockers

- Original training runtime versions remain unavailable.
- Local inference is CPU-only.
- Uploaded-image predictions are exploratory and unapproved.
- No clinical calibration or independent external validation is claimed.
- No GPU training or retraining was performed.
