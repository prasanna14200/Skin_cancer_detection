"""Synthetic-only checks for the independent GPU feasibility entry point."""

import sys
from pathlib import Path

import pytest
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from models.egvan import build_nine_class_egvan
from nine_class_gpu_smoke import run_gpu_smoke, set_batchnorm_policy, synthetic_optimizer_step


class TinyNine(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 8, 3, padding=1)
        self.bn = nn.BatchNorm2d(8)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(8, 9)

    def forward(self, x):
        return self.classifier(self.pool(self.bn(self.conv(x))).flatten(1))


def test_real_factory_contract_without_weights_or_images():
    model = build_nine_class_egvan()
    assert model.classifier.out_features == 9
    assert sum(isinstance(module, nn.BatchNorm2d) for module in model.modules()) > 0
    assert not any(isinstance(module, nn.Softmax) for module in model.modules())


def test_cpu_synthetic_step_updates_and_keeps_bn_frozen():
    torch.manual_seed(17)
    model = TinyNine()
    before_affine = model.bn.weight.detach().clone()
    result = synthetic_optimizer_step(model, torch.device("cpu"), batch_size=1,
                                      batchnorm_policy="freeze_running_stats", image_size=8)
    assert result["status"] == "PASSED"
    assert result["input_shape"] == [1, 3, 8, 8]
    assert result["logits_shape"] == [1, 9]
    assert result["batchnorm_running_stats_changed"] is False
    assert result["classifier_parameters_updated"] and result["gradient_reset"]
    assert not torch.equal(model.bn.weight, before_affine)
    assert result["cuda_fp16_autocast"] is False and result["peak_allocated_bytes"] is None


def test_train_bn_requires_two_and_changes_stats():
    with pytest.raises(ValueError, match="Batch size 1"):
        set_batchnorm_policy(TinyNine(), "train_running_stats", 1)
    model = TinyNine()
    result = synthetic_optimizer_step(model, torch.device("cpu"), batch_size=2,
                                      batchnorm_policy="train_running_stats", image_size=8)
    assert result["status"] == "PASSED"
    assert result["batchnorm_running_stats_changed"] is True
    assert int(model.bn.num_batches_tracked) == 1


def test_gpu_entry_reports_unavailable_without_creating_a_checkpoint():
    result = run_gpu_smoke(try_batch_2=False, batchnorm_policy="freeze_running_stats",
                           device=torch.device("cpu"))
    assert result["status"] == "CUDA_UNAVAILABLE"
    assert result["results"] == []
    assert result["checkpoint_created"] is False
    assert result["clinical_dataset_accessed"] is False
