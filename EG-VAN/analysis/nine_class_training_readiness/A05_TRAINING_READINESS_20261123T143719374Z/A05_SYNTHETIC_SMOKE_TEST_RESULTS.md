# A05 Synthetic-Only Pipeline Smoke Results

**Result:** `PASS_SYNTHETIC_ONLY`  
**This is not model training, dataset evaluation, inference on lesions, or a performance result.**

## Scope and runtime

- Generated random CPU tensor: batch 1, shape `[1, 3, 64, 64]`; synthetic label index `8`.
- Constructed the existing nine-output EG-VAN with random initialization. No dataset images, source metadata, labels, split, or external data were read.
- Python 3.10.16; PyTorch 2.14.0+cpu; torchvision 0.29.0+cpu; CUDA unavailable.
- One forward/backward optimizer update was exercised, plus a separate same-seed forward replay for reproducibility.
- No FP16/CUDA behavior, 384x384 training, data loader, epoch, or clinical workflow was exercised.

## Assertions

| Check | Result | Evidence |
|---|---|---|
| Output dimension | PASS | Model returned finite logits with shape `[1, 9]`. |
| Focal loss | PASS | Alpha 0.25, gamma 2.0; loss was finite. |
| Gradient propagation | PASS | At least one gradient existed and all gradients were finite. |
| Adamax step | PASS | Classifier parameters changed; gradients were cleared after the update. |
| Frozen BatchNorm | PASS | Running means, variances, and batch counters did not change. |
| Seed reproducibility | PASS | Replayed training-mode forward with the same CPU RNG state produced exactly equal logits. |
| Checkpoint round-trip | PASS | Existing atomic checkpoint helper saved and reloaded model state; all parameters matched. Temporary checkpoint size: 233,667,914 bytes. |

Elapsed update/replay/checkpoint smoke time reported by the runtime: 0.747 seconds. This is not a throughput estimate.

The first reproducibility attempt compared forwards without aligning training-mode stochastic state and failed its equality assertion. The check was corrected to put both models in training mode and replay the captured CPU RNG state; the exact equality assertion then passed. The temporary smoke checkpoints were removed after verification.

## Hardware evidence and limits

This machine's PyTorch build is CPU-only (`torch.cuda.is_available() == False`); no CUDA device or FP16 test was run. A separate, pre-existing synthetic T4 evidence record reports 384x384 one-step passes for microbatches 1, 2, 4, and 8, with 4,262 MiB peak reserved at batch 8. That record is not a full-epoch capacity test, does not establish dataset eligibility, and is not an A05 training run.

## Additional test logs

- `python -m pytest -q tests/test_nine_class_authorized_training.py`: exit 0; 9 passed.
- `python -m pytest -q tests/test_nine_class_stage6.py tests/test_nine_class_shape_contract.py tests/test_nine_class_gpu_smoke.py`: exit 1; 17 passed, 1 failed. The remaining test could not import `nine_class_exploratory` because `src/nine_class_iqa.py` imports a missing environment dependency: `ModuleNotFoundError: No module named 'matplotlib'`. No dataset image was read by these tests; fixture files are synthetic temporary byte strings.
- Actual current checklist probe: ran the new launcher with `--launch` against the real `NOT_APPROVED` checklist; it exited 2 with `TRAINING AUTHORIZATION BLOCKED: Approval checklist status is 'NOT_APPROVED'; expected APPROVED`. No Stage 6 process was started.

The temporary pytest dependency was installed outside the repository only to run the focused tests; the project dependency manifests were not changed.
