# EG-VAN Project Showcase

Local-first Streamlit overview, architecture explorer, and experimental
nine-class image prediction demo. The demo uses the existing frozen checkpoint;
it does not train, fine-tune, or change research artifacts.

## Windows PowerShell setup and launch

From `E:\Cancerdetection\EG-VAN`, using the available Python 3.13.5 installation:

```powershell
& "D:\anaconda3\python.exe" -m venv ".\project_showcase\.venv"
& ".\project_showcase\.venv\Scripts\python.exe" -m pip install -r ".\project_showcase\requirements.txt"
& ".\project_showcase\.venv\Scripts\python.exe" -m streamlit run ".\project_showcase\Home.py" --server.address 127.0.0.1 --server.port 8501 --server.maxUploadSize 20
```

Open `http://127.0.0.1:8501`. In the environment used for Phase 4, the venv
already exists; do not recreate it while the site is running. To run tests:

```powershell
& ".\project_showcase\.venv\Scripts\python.exe" -m pip install -r ".\project_showcase\requirements-dev.txt"
& ".\project_showcase\.venv\Scripts\python.exe" -m pytest ".\project_showcase\tests"
```

## Pages

- **Overview** — project objective, reconstruction scope, saved exploratory
  evidence, additional investigations, and current status.
- **EG-VAN Reconstruction Explorer** — source-grounded forward-pass diagram,
  module explanations, synthetic tensor-shape evidence, and paper-fidelity gaps.
- **Image Prediction Demo** — CPU inference using the frozen nine-class model.
  JPEG and PNG uploads are limited to 20 MiB and 25 megapixels.

The demo loads the model only after verifying the checkpoint SHA-256, recorded
run provenance, configuration and preprocessing hashes, exact class order, and
strict state-dictionary compatibility. It uses the project preprocessing
implementation and performs inference in memory; uploaded images are not saved
to project files. All nine softmax probabilities and the top three outputs are
shown. These values are not calibrated clinical risks.

## Verified runtime

The Phase 4 isolated environment uses Python 3.13.5 on Windows, CPU-only:

| Package | Version |
|---|---:|
| NumPy | 2.2.6 |
| OpenCV headless | 5.0.0.93 |
| Pillow | 11.3.0 |
| Streamlit | 1.45.1 |
| PyTorch | 2.14.0+cpu |
| Torchvision | 0.29.0+cpu |

`requirements.txt` pins the direct runtime dependencies. PyTorch and Torchvision
were installed as a matching CPU wheel pair; no pretrained weights, GPU
packages, paid APIs, or external services are used. The exact Python/PyTorch
versions used for the original training run are not recorded in its provenance.

## Evidence, status, and limitations

Saved validation metrics are read-only and labelled EXPLORATORY / NON-CLINICAL.
The architecture explorer's tensor shapes are synthetic architecture checks,
not model performance. The prediction demo is a technical inference interface
for an unapproved research cohort. It is not an exact reproduction of the
EG-VAN paper, does not establish clinical validity, and must not be used for
diagnosis or care decisions. Source-defined BENIGN/MALIGNANT labels remain
separate from HAM diagnosis labels.

The frozen checkpoint is
`analysis/nine_class_exploratory/runs/EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt`;
its verified SHA-256 is
`3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`.
The Phase 4 environment, strict checkpoint load, and a single real-image smoke
inference are documented in [PHASE_4_VALIDATION.md](./PHASE_4_VALIDATION.md).
