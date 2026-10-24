"""Synthetic Stage 5 architecture contract without data or pretrained weights."""

import sys
from pathlib import Path

import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from models.egvan import EGVAN, build_nine_class_egvan
from models.egvan.mff import MFF
from models.egvan.non_local import NonLocalBlock
from models.egvan.scga import SCGA
from nine_class_stage4 import CLASS_NAMES


def test_explicit_nine_class_factory_and_legacy_default():
    torch.set_num_threads(2)
    assert CLASS_NAMES == ("AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC", "BENIGN", "MALIGNANT")
    torch.manual_seed(42)
    model = build_nine_class_egvan().eval()
    assert model.classifier.out_features == len(CLASS_NAMES)
    assert not any(isinstance(module, nn.Softmax) for module in model.modules())
    assert model.efficient.output_channels == (48, 64, 160, 1280)
    assert model.resnet.output_channels == (256, 512, 1024, 2048)
    assert len(model.fusions) == 4
    assert [module.carry_channels for module in model.fusions] == [0, 128, 128, 128]
    with torch.no_grad():
        output = model(torch.randn(1, 3, 64, 64))
    assert output.shape == (1, 9)
    assert torch.isfinite(output).all()
    assert EGVAN().classifier.out_features == 7


def test_reproducible_random_initialization():
    torch.manual_seed(112)
    first = build_nine_class_egvan().classifier.weight.detach().clone()
    torch.manual_seed(112)
    second = build_nine_class_egvan().classifier.weight.detach().clone()
    assert torch.equal(first, second)


def test_attention_fusion_and_nonlocal_residual_path():
    x = torch.randn(1, 64, 9, 11, requires_grad=True)
    attended = SCGA(64)(x)
    assert attended.shape == x.shape
    block = NonLocalBlock(64)
    with torch.no_grad():
        block.project.weight.zero_()
    assert torch.equal(block(x), x)
    fused = MFF(48, 256, out_channels=64, carry_channels=64).eval()(
        torch.randn(1, 48, 24, 24), torch.randn(1, 256, 24, 24),
        torch.randn(1, 64, 24, 24))
    assert fused.shape == (1, 64, 12, 12)
    attended.mean().backward()
    assert x.grad is not None and torch.isfinite(x.grad).all()
