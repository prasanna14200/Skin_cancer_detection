# Nine-class EG-VAN synthetic GPU training smoke

This smoke test checks **computational feasibility only**. It uses the real [Stage 5 nine-logit factory](../src/models/egvan/egvan.py) and [Stage 6 focal loss](../src/nine_class_training.py), but creates random `(B, 3, 384, 384)` tensors and random integer targets in `0..8`. It reads no patient image, manifest, split, approval, checkpoint or pretrained weight; it writes only a new JSON result directory. It does **not** authorize or start full dataset training. The nine label order remains `AKIEC, BCC, BKL, DF, MEL, NV, VASC, BENIGN, MALIGNANT`.

The [entry point](../src/nine_class_gpu_smoke.py) constructs 58,087,667-parameter EG-VAN with `pretrained_efficient=False` and `pretrained_resnet=False`. On CUDA it uses FP16 autocast, `torch.amp.GradScaler("cuda")` with initial scale 1024, Stage 6 focal loss (`alpha=0.25`, `gamma=2`), Adamax (`lr=0.001`), gradient unscaling, norm check/clipping at 1, optimizer step and `zero_grad(set_to_none=True)`. It requires finite `(B,9)` raw logits, loss, unscaled gradient norm and updated finite classifier weights. [PyTorch's AMP guidance](https://docs.pytorch.org/docs/stable/notes/amp_examples.html) specifies unscaling before inspecting/clipping gradients and stepping the scaler after the optimizer step. This script follows that order.

## BatchNorm policy

The current architecture contains **167 BatchNorm modules**. For batch size **1**, the smoke sets the whole model to train mode and sets BatchNorm modules alone to evaluation mode. Thus their running means/variances stay fixed, while their affine weights and the rest of the model remain trainable. This explicit `freeze_running_stats` policy avoids a single synthetic image defining BatchNorm statistics and avoids potential failures at a one-value spatial map. The smoke verifies that running buffers did not change. It does not replace BatchNorm layers or alter the architecture.

The optional batch **2** attempt also defaults to frozen running statistics, permitting a clean memory comparison. For a separate exploratory batch-2 trial, `--batchnorm-policy train_running_stats --try-batch-2` still runs batch 1 with frozen statistics first, then lets batch 2 update BatchNorm buffers; the report records the actual policy per step. Batch-2 training statistics would still be noisy. The Stage 6 full runner is unchanged and currently uses ordinary training-mode BatchNorm. A future approved-data run must choose and document its own microbatch/BatchNorm policy; gradient accumulation does **not** turn batch-1 or batch-2 BatchNorm into batch-32 BatchNorm.

## Exact Colab commands after uploading the current code

The current local source files are uncommitted; upload/synchronize **this version** of the repository, not just an older GitHub checkout. In Colab, put it at the Drive path below or replace the path with the actual mounted location. With the user's reported Tesla T4, 14.46 GiB free VRAM and `torch==2.11.0+cu130`, use the installed compatible `torchvision`; this direct smoke entry point does **not** use the older notebook's `+cu128` version check. The required repository imports also need installed NumPy, Pillow, OpenCV, pandas and scikit-learn. Do not reinstall CUDA PyTorch merely to run this test.

```python
from google.colab import drive
drive.mount('/content/drive')
%cd /content/drive/MyDrive/EG-VAN
!python -c "import torch, torchvision; print(torch.__version__, torchvision.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO_CUDA')"
!python src/nine_class_gpu_smoke.py --output-dir analysis/nine_class_gpu_smoke/t4_batch1_001
```

After reading the batch-1 result, **optionally** try batch 2 in a new directory; the entry point repeats batch 1 first and then attempts batch 2:

```python
!python src/nine_class_gpu_smoke.py --output-dir analysis/nine_class_gpu_smoke/t4_batch1_then_2_001 --try-batch-2
```

Use a fresh output name for each run; the script refuses an existing directory. `smoke_result.json` records device and torch/CUDA versions, synthetic targets, BatchNorm mode and buffer behavior, finite checks, loss, unscaled gradient norm, parameter update, model setup time, synchronized optimizer-step wall time, baseline allocated/reserved bytes and **peak allocated/reserved bytes/MiB**. PyTorch allocated and reserved peaks are process allocator measures, not system-wide VRAM use or a full training memory guarantee. No T4 result has been generated in this workspace. The [local preflight record](../analysis/nine_class_gpu_smoke/local_preflight/smoke_result.json) says `torch==2.11.0+cpu` and `cuda_available=false`; it contains **no** forward/backward step or GPU timing.

If batch 2 runs out of memory after batch 1 succeeds, the JSON retains batch-1 success and reports batch 1 as the observed fallback. If batch 1 itself runs out of memory, **no smaller batch exists at 384×384**; the script reports that no safe smaller configuration was measured. A larger GPU or separately implemented and validated activation checkpointing would be needed before an approved full run. It does not silently lower resolution, alter the model or create a checkpoint. A successful one-step smoke does not establish that full-epoch training will fit: data loading, validation, optimizer history, retained tensors and variable runtime availability still matter.

## Local verification and limits

`python -m pytest tests/test_nine_class_gpu_smoke.py tests/test_nine_class_stage5.py tests/test_nine_class_stage6.py -q` returned **13 passed** with the existing optional Windows torchvision image-extension warning. Tests use a tiny nine-output synthetic network to check optimizer update, gradient reset, frozen BatchNorm affine training and batch-2 running-stat change; the real factory's nine-logit head and BatchNorm presence are checked without a clinical image. The local preflight was run using `--preflight-only`, so it did not simulate a T4 result. GPU FP16 backward, T4 peak allocated/reserved memory, wall time and batch-2 support remain **unmeasured until the Colab commands run**. Dataset eligibility and full-training readiness remain blocked under the [research completion plan](NINE_CLASS_RESEARCH_COMPLETION_PLAN.md).
