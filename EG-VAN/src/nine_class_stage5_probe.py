"""Synthetic, CPU-only nine-class EG-VAN architecture probe; no training."""

from __future__ import annotations

import json
from pathlib import Path

import torch

from models.egvan import build_nine_class_egvan

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/nine_class_stage5/architecture_probe.json"


def probe() -> dict:
    torch.set_num_threads(2)
    torch.manual_seed(42)
    model = build_nine_class_egvan().cpu().eval()
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    x = torch.randn(1, 3, 384, 384, device="cpu", requires_grad=True)
    features = model.forward_features(x)
    logits = model.classifier(model.pool(features["combined"]).flatten(1))
    if logits.shape != (1, 9) or not bool(torch.isfinite(logits).all()):
        raise AssertionError("Nine-class logits shape or values invalid")
    logits.square().mean().backward()
    watched = {
        "efficient_stem": model.efficient.features[0][0].weight,
        "resnet_stem": model.resnet.conv1.weight,
        "scga_spatial": model.resnet.scga1.spatial.conv64.weight,
        "scga_group": model.resnet.scga1.gma.horizontal.weight,
        "nonlocal_query": model.resnet.nonlocal3.theta.weight,
        "nonlocal_project": model.resnet.nonlocal3.project.weight,
        "mff_depthwise": model.fusions[0].depthwise.weight,
        "mff_carry": model.fusions[1].pointwise.weight,
        "aggregate": model.aggregate.weight,
        "classifier": model.classifier.weight,
    }
    gradients = {name: tensor.grad is not None and bool(torch.isfinite(tensor.grad).all())
                 for name, tensor in watched.items()}
    if not all(gradients.values()) or x.grad is None or not bool(torch.isfinite(x.grad).all()):
        raise AssertionError("Missing or non-finite architecture gradient")
    result = {
        "seed": 42,
        "device": "cpu",
        "pretrained_weights_loaded": False,
        "input_shape": list(x.shape),
        "efficient_shapes": [list(t.shape) for t in features["efficient"]],
        "resnet_shapes": [list(t.shape) for t in features["resnet"]],
        "mff_shapes": [list(t.shape) for t in features["fused"]],
        "combined_shape": list(features["combined"].shape),
        "logit_shape": list(logits.shape),
        "finite_logits": True,
        "finite_input_gradient": True,
        "watched_gradients_finite": gradients,
        "total_parameters": total,
        "trainable_parameters": trainable,
        "parameter_bytes_float32": total * 4,
        "parameter_and_gradient_bytes_float32": trainable * 8,
    }
    return result


if __name__ == "__main__":
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    result = probe()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
