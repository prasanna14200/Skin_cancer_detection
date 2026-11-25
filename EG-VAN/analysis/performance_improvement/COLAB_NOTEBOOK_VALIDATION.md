# Colab Notebook Validation

**Status: Generated and locally checked; not executed in Colab**

Updated: 2026-11-22. No GPU training, Colab benchmark, or new model result is
claimed.

## Local checks

- Notebook JSON parsed successfully: 25 cells (13 code, 12 markdown).
- All 13 code cells compiled with the local Python parser.
- The first notebook cell mounts Google Drive and configures the direct project
  root `/content/drive/MyDrive/EG-VAN`.
- Notebook outputs are isolated in
  `/content/drive/MyDrive/EG-VAN/colab_runs/egvan_gpu_training/`; the ZIP is
  written in `colab_runs/` and does not include unrelated sibling outputs.
- Existing local `colab_runs/` content was left untouched.
- The local source manifest contains 13,312 image records and the exploratory
  split contains 10,234 records; all referenced manifest paths existed in the
  local project tree.
- Both manifest and split contain the expected nine source-defined class names.
- A local simulation of the grouped development-split code produced 9,131
  development rows with all nine classes in train and validation. It used the
  split CSV identity/hash metadata; it did not decode or re-hash all image bytes.
- The existing `NineClassDataset` decoded and preprocessed one real validation
  image to `(3, 384, 384)` on CPU; no model training was run.
- The historical split remains unapproved. Its saved provenance notes unknown
  patient/photo identity and other cohort limitations.
- The frozen checkpoint SHA-256 still matches the recorded value
  `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`.
- No local model training or GPU benchmark was started. No checkpoint,
  historical split, or research evidence was modified.

## Notebook behavior and limitations

- On Colab execution, the inventory cell resolves and verifies every manifest
  image, image format, source label/index and recorded SHA-256 before training.
- The grouped development split unions lesion, patient, overlap-group and
  verified exact-image hashes; the historical test partition is excluded and
  the notebook blocks its evaluation.
- GPU availability and the PyTorch/Torchvision version pair are checked before
  any training. Pretrained weights are disabled.
- Training requires explicit opt-in and a second confirmation after reviewing
  the benchmark estimate; checkpoints are saved after each epoch with resume
  metadata.
- Exported checkpoints are research artifacts and are not accepted by the
  existing Streamlit inference loader's frozen-checkpoint hash/provenance
  checks without separate verification and a deliberate loader change.

The notebook still requires an actual Colab run to verify Drive access, GPU
compatibility, full image/hash preflight, training, checkpoint export and ZIP
creation.
