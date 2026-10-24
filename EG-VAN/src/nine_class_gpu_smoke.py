"""Synthetic, checkpoint-free nine-class EG-VAN GPU optimizer smoke test.

This entry point never imports dataset manifests or reads clinical images.
It deliberately does not call the Stage 6 cohort-gated training main().
"""

from __future__ import annotations

import argparse
import gc
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from torch import nn
from torch.optim import Adamax

from models.egvan import build_nine_class_egvan
from nine_class_stage4 import CLASS_NAMES
from nine_class_training import focal_loss, seed_all

BN_POLICIES = ("freeze_running_stats", "train_running_stats")


def set_batchnorm_policy(model: nn.Module, policy: str, batch_size: int) -> list[nn.modules.batchnorm._BatchNorm]:
    """Keep affine gradients; optionally stop only running-stat updates."""
    if policy not in BN_POLICIES:
        raise ValueError(f"Unknown BatchNorm policy: {policy}")
    if batch_size < 1:
        raise ValueError("Batch size must be positive")
    if policy == "train_running_stats" and batch_size < 2:
        raise ValueError("Batch size 1 cannot use train_running_stats in this smoke test")
    model.train()
    modules = [m for m in model.modules() if isinstance(m, nn.modules.batchnorm._BatchNorm)]
    if policy == "freeze_running_stats":
        for module in modules:
            module.eval()
    return modules


def _bn_snapshot(modules: list[nn.modules.batchnorm._BatchNorm]) -> list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
    return [(m.running_mean.detach().clone(), m.running_var.detach().clone(),
             m.num_batches_tracked.detach().clone()) for m in modules]


def _bn_changed(modules: list[nn.modules.batchnorm._BatchNorm], before: list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]) -> bool:
    return any(not torch.equal(old, new) for module, prior in zip(modules, before)
               for old, new in zip(prior, (module.running_mean, module.running_var, module.num_batches_tracked)))


def synthetic_optimizer_step(model: nn.Module, device: torch.device, *, batch_size: int,
                             batchnorm_policy: str = "freeze_running_stats",
                             image_size: int = 384, seed: int = 42) -> dict:
    """Run one Stage-6-style focal/Adamax update on random tensors only."""
    if image_size < 1:
        raise ValueError("Image size must be positive")
    model.to(device)
    modules = set_batchnorm_policy(model, batchnorm_policy, batch_size)
    before_bn = _bn_snapshot(modules)
    if len(CLASS_NAMES) != 9 or getattr(model, "classifier").out_features != 9:
        raise ValueError("Synthetic smoke requires the nine-output EG-VAN contract")
    optimizer = Adamax(model.parameters(), lr=0.001)
    amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", init_scale=1024.0, enabled=amp)
    scale_before = scaler.get_scale()
    if amp:
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
        baseline_allocated = torch.cuda.memory_allocated(device)
        baseline_reserved = torch.cuda.memory_reserved(device)
    else:
        baseline_allocated = baseline_reserved = None
    probe = model.classifier.weight
    before_probe = probe.detach().clone()
    generator = torch.Generator(device=device).manual_seed(seed)
    start = time.perf_counter()
    inputs = torch.randn((batch_size, 3, image_size, image_size), device=device, generator=generator)
    labels = torch.randint(0, len(CLASS_NAMES), (batch_size,), device=device, generator=generator)
    optimizer.zero_grad(set_to_none=True)
    with torch.autocast(device_type=device.type, dtype=torch.float16 if amp else torch.float32, enabled=amp):
        logits = model(inputs)
        loss = focal_loss(logits, labels, alpha=0.25, gamma=2.0)
    if tuple(logits.shape) != (batch_size, 9) or not bool(torch.isfinite(logits).all().item()):
        raise RuntimeError("Nine-logit shape or finiteness check failed")
    if not bool(torch.isfinite(loss).item()):
        raise RuntimeError("Focal loss is not finite")
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
    if not bool(torch.isfinite(gradient_norm).item()) or not any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Gradients are absent or nonfinite")
    scaler.step(optimizer)
    scaler.update()
    scale_after = scaler.get_scale()
    updated = not torch.equal(probe.detach(), before_probe)
    if not updated or not bool(torch.isfinite(probe).all().item()):
        raise RuntimeError("Classifier parameters did not update finitely")
    optimizer.zero_grad(set_to_none=True)
    if any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Optimizer gradient reset failed")
    if amp:
        torch.cuda.synchronize(device)
    duration = time.perf_counter() - start
    bn_changed = _bn_changed(modules, before_bn)
    if batchnorm_policy == "freeze_running_stats" and bn_changed:
        raise RuntimeError("Frozen BatchNorm running statistics changed")
    peak_allocated = torch.cuda.max_memory_allocated(device) if amp else None
    peak_reserved = torch.cuda.max_memory_reserved(device) if amp else None
    return {
        "status": "PASSED", "synthetic_only": True,
        "batch_size": batch_size, "input_shape": [batch_size, 3, image_size, image_size],
        "logits_shape": list(logits.shape), "label_indices": labels.tolist(),
        "focal_loss": float(loss.detach().item()), "gradient_norm": float(gradient_norm.item()),
        "classifier_parameters_updated": updated, "gradient_reset": True,
        "batchnorm_policy": batchnorm_policy, "batchnorm_modules": len(modules),
        "batchnorm_running_stats_changed": bn_changed,
        "cuda_fp16_autocast": amp, "cuda_grad_scaler": amp,
        "gradient_scale_before": scale_before, "gradient_scale_after": scale_after,
        "duration_seconds_step_only": duration,
        "baseline_allocated_bytes": baseline_allocated,
        "baseline_reserved_bytes": baseline_reserved,
        "peak_allocated_bytes": peak_allocated, "peak_reserved_bytes": peak_reserved,
        "peak_allocated_mib": round(peak_allocated / 2**20, 1) if amp else None,
        "peak_reserved_mib": round(peak_reserved / 2**20, 1) if amp else None,
    }


def run_gpu_smoke(*, try_batch_2: bool, batchnorm_policy: str, seed: int = 42,
                  device: torch.device | None = None) -> dict:
    device = device or torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    report = {"schema_version": "nine_class_gpu_smoke_v1",
              "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "synthetic_only": True, "checkpoint_created": False,
              "clinical_dataset_accessed": False, "training_cohort_approval_required": False,
              "torch_version": torch.__version__, "torch_cuda_version": torch.version.cuda,
              "device": str(device), "batchnorm_policy": batchnorm_policy, "results": []}
    if device.type != "cuda":
        report.update(status="CUDA_UNAVAILABLE", gpu_name=None,
                      note="No GPU measurement was made; run the same command in the Colab CUDA runtime")
        return report
    report["gpu_name"] = torch.cuda.get_device_name(device)
    report["memory_total_bytes"] = torch.cuda.mem_get_info(device)[1]
    report["memory_free_before_bytes"] = torch.cuda.mem_get_info(device)[0]
    for batch_size in (1, 2) if try_batch_2 else (1,):
        effective_bn_policy = "freeze_running_stats" if batch_size == 1 else batchnorm_policy
        model = None
        try:
            torch.cuda.reset_peak_memory_stats(device)
            seed_all(seed)
            setup_start = time.perf_counter()
            model = build_nine_class_egvan(pretrained_efficient=False, pretrained_resnet=False)
            model.to(device)
            torch.cuda.synchronize(device)
            setup_seconds = time.perf_counter() - setup_start
            result = synthetic_optimizer_step(model, device, batch_size=batch_size,
                                              batchnorm_policy=effective_bn_policy, seed=seed)
            result["model_setup_seconds"] = setup_seconds
            report["results"].append(result)
        except torch.cuda.OutOfMemoryError as error:
            report["results"].append({"status": "CUDA_OOM", "batch_size": batch_size,
                                      "batchnorm_policy": effective_bn_policy,
                                      "error": str(error)[:500], "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                                      "peak_reserved_bytes": torch.cuda.max_memory_reserved(device)})
            if batch_size == 1:
                break
        finally:
            del model
            gc.collect()
            torch.cuda.empty_cache()
    passed = [r["batch_size"] for r in report["results"] if r["status"] == "PASSED"]
    report["supported_batch_sizes_observed"] = passed
    report["status"] = "PASSED" if passed else "CUDA_OOM_NO_BATCH_PASSED"
    report["oom_recommendation"] = (
        "If batch 2 OOMs, retain observed batch 1 with frozen BatchNorm running statistics; "
        "gradient accumulation is a separate future training configuration and does not reproduce batch-32 BatchNorm."
        if passed else
        "Batch 1 is already the smallest batch. No smaller safe configuration was measured; use a larger GPU "
        "or separately implement and validate activation checkpointing before training."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for smoke_result.json")
    parser.add_argument("--try-batch-2", action="store_true", help="After batch 1, also attempt batch 2")
    parser.add_argument("--batchnorm-policy", choices=BN_POLICIES, default="freeze_running_stats")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--preflight-only", action="store_true", help="Report availability without constructing or training a model")
    args = parser.parse_args()
    if args.batchnorm_policy == "train_running_stats" and not args.try_batch_2:
        parser.error("train_running_stats applies only to optional batch 2; add --try-batch-2")
    if args.output_dir.exists():
        parser.error(f"Output directory already exists: {args.output_dir}")
    if args.preflight_only:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        result = {"schema_version": "nine_class_gpu_smoke_v1", "status": "PREFLIGHT_ONLY",
                  "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                  "synthetic_only": True, "checkpoint_created": False, "clinical_dataset_accessed": False,
                  "torch_version": torch.__version__, "torch_cuda_version": torch.version.cuda,
                  "cuda_available": device.type == "cuda", "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
                  "note": "No forward, backward or optimizer step was run"}
    else:
        result = run_gpu_smoke(try_batch_2=args.try_batch_2, batchnorm_policy=args.batchnorm_policy,
                               seed=args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "smoke_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ("PREFLIGHT_ONLY", "PASSED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
