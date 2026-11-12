"""Bounded automated evidence and Colab gate checks; no real training."""

import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import nbformat
import numpy as np
import pytest
import torch
from torch import nn
from torch.optim import SGD
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nine_class_colab import (evaluation_command, gpu_memory_plan, training_command,
                              validate_cohort, validate_colab_config, validate_colab_runtime,
                              validate_resume)
from nine_class_dataset import PreprocessConfig, preprocessing_hash
from nine_class_stage11b_auto_review import (automatic_category, crop_aware_evidence,
                                             read_csv, run)
from nine_class_training import focal_loss, load_config, run_epoch


def synthetic_pair(**changes):
    row = {"exact_sha256_match": False, "geometric_status": "unreliable",
           "stage3g_transform_plausibility": "NOT_ASSESSED", "stage3g_aligned_correlation": None,
           "geometric_inliers": 0, "geometric_inlier_ratio": 0.,
           "crop_aware_correlation": .75, "phash_distance": 5, "dhash_distance": 3,
           "prior_pixel_correlation": .8, "central_structure_correlation": .7,
           "surrounding_field_correlation": .7}
    row.update(changes)
    return row


def test_automated_categories_are_separate_from_approval():
    assert automatic_category(synthetic_pair(exact_sha256_match=True))[0] == "AUTO_SAME_PHOTO"
    assert automatic_category(synthetic_pair(geometric_status="coherent",
          stage3g_transform_plausibility="plausible_geometric_mapping",
          stage3g_aligned_correlation=.99, geometric_inliers=20,
          geometric_inlier_ratio=.8, crop_aware_correlation=.96))[0] == "AUTO_SAME_PHOTO"
    assert automatic_category(synthetic_pair(phash_distance=28, dhash_distance=20,
          prior_pixel_correlation=.3, crop_aware_correlation=.4,
          central_structure_correlation=.2, surrounding_field_correlation=.3))[0] == "AUTO_DISTINCT_PHOTO"
    assert automatic_category(synthetic_pair())[0] == "AUTO_UNCERTAIN"


def test_crop_match_identity_and_weak_unsupported_evidence():
    rng = np.random.default_rng(7)
    image = rng.integers(0, 256, (64, 64), dtype=np.uint8)
    same = crop_aware_evidence(image, image)
    assert same["crop_aware_correlation"] > .99
    assert same["central_structure_correlation"] > .99
    with pytest.raises(ValueError):
        crop_aware_evidence(np.zeros((4, 4), np.uint8), image)


def test_real_bounded_outputs_preserve_blank_human_ledger():
    primary = read_csv(ROOT / "analysis/nine_class_stage11b/primary_19_auto_evidence.csv")
    additional = read_csv(ROOT / "analysis/nine_class_stage11b/additional_101_auto_evidence.csv")
    blank = read_csv(ROOT / "analysis/nine_class_stage11a/decision_ledger.csv")
    summary = json.loads((ROOT / "analysis/nine_class_stage11b/automated_review_summary.json").read_text(encoding="utf8"))
    assert len(primary) == 19 and len(additional) == 101
    assert all(r["reviewer_decision"] == "" for r in blank)
    assert all(r["human_decision_used"] == "False" and r["approved_eligible"] == "False"
               for r in primary + additional)
    assert summary["exact_sha256_pairs"] == 0 and not summary["full_nine_class_training_ready"]
    assert sum(summary["primary_automated_categories"].values()) == 19
    assert sum(summary["additional_automated_categories"].values()) == 101
    with pytest.raises(FileExistsError):
        run(ROOT)


def test_colab_config_memory_and_approval_gate(tmp_path):
    path = ROOT / "config/nine_class_training_colab_2026_07.json"
    plan = validate_colab_config(path)
    assert plan["nominal_effective_batch_size"] == 32
    assert plan["preprocess_config_sha256"] == preprocessing_hash(
        PreprocessConfig(pipeline_version="raw_resize_imagenet_v2"))
    report = gpu_memory_plan(16 * 2**30, 12 * 2**30, plan["config"])
    assert report["activation_peak_measured"] is False and report["microbatch_size"] == 4
    with pytest.raises(ValueError):
        gpu_memory_plan(0, 0, plan["config"])
    with pytest.raises(FileNotFoundError):
        validate_cohort(tmp_path, tmp_path / "missing.csv", tmp_path / "approval.json", tmp_path / "inventory.csv")
    broken = {**plan["config"], "gradient_accumulation_steps": 0}
    broken_path = tmp_path / "broken.json"
    broken_path.write_text(json.dumps(broken), encoding="utf8")
    with pytest.raises(ValueError, match="gradient_accumulation_steps"):
        load_config(broken_path)


def test_accumulation_matches_true_effective_batch_update():
    torch.manual_seed(9)
    x = torch.randn(5, 3)
    y = torch.tensor([0, 1, 2, 3, 4])
    model = nn.Linear(3, 9)
    expected = nn.Linear(3, 9)
    expected.load_state_dict(model.state_dict())
    opt = SGD(model.parameters(), lr=.01)
    manual = SGD(expected.parameters(), lr=.01)
    cfg = load_config(ROOT / "config/nine_class_training_colab_2026_07.json")
    cfg.update(gradient_clip_norm=None, mixed_precision="off")
    for start, end in ((0, 4), (4, 5)):
        manual.zero_grad(set_to_none=True)
        focal_loss(expected(x[start:end]), y[start:end], alpha=cfg["focal_alpha"],
                   gamma=cfg["focal_gamma"]).backward()
        manual.step()
    run_epoch(model, DataLoader(TensorDataset(x, y), batch_size=2), torch.device("cpu"),
              {**cfg, "gradient_accumulation_steps": 2}, optimizer=opt)
    assert torch.allclose(model.weight, expected.weight, atol=1e-7)
    assert torch.allclose(model.bias, expected.bias, atol=1e-7)


def test_colab_runtime_accepts_cuda_build_suffix_without_exact_pin():
    cuda = SimpleNamespace(is_available=lambda: True, get_device_capability=lambda index: (7, 5),
                           get_device_name=lambda index: "Tesla T4")
    fake_torch = SimpleNamespace(__version__="2.11.0+cu130", version=SimpleNamespace(cuda="13.0"),
                                 cuda=cuda, autocast=lambda **kwargs: None,
                                 amp=SimpleNamespace(GradScaler=lambda **kwargs: None))
    models = SimpleNamespace(efficientnet_v2_s=lambda weights: SimpleNamespace(features=[]),
                             resnet50=lambda weights: SimpleNamespace(layer4=[]),
                             EfficientNet_V2_S_Weights=object(), ResNet50_Weights=object())
    fake_vision = SimpleNamespace(__version__="0.26.0+cu130", models=models)
    result = validate_colab_runtime(fake_torch, fake_vision)
    assert result["torch"] == "2.11.0+cu130" and result["gpu"] == "Tesla T4"
    fake_torch.cuda = SimpleNamespace(is_available=lambda: False)
    with pytest.raises(RuntimeError, match="CUDA-enabled"):
        validate_colab_runtime(fake_torch, fake_vision)
    fake_torch.cuda = cuda
    fake_vision.models = SimpleNamespace()
    with pytest.raises(RuntimeError, match="Torchvision lacks"):
        validate_colab_runtime(fake_torch, fake_vision)
    fake_vision.models = models
    fake_vision.models.resnet50 = lambda weights: (_ for _ in ()).throw(RuntimeError("bad wheel"))
    with pytest.raises(RuntimeError, match="construction failed"):
        validate_colab_runtime(fake_torch, fake_vision)


def test_resume_commands_persist_and_notebook_is_gated(tmp_path):
    run_dir = tmp_path / "runs" / "run1"
    run_dir.mkdir(parents=True)
    last = run_dir / "last.pt"
    last.write_bytes(b"synthetic-only placeholder")
    (run_dir / "run_provenance.json").write_text("{}", encoding="utf8")
    assert validate_resume(last, tmp_path / "runs") == last
    with pytest.raises(ValueError):
        validate_resume(tmp_path / "outside.pt", tmp_path / "runs")
    cmd = training_command(ROOT, ROOT / "config/nine_class_training_colab_2026_07.json",
                           tmp_path / "split.csv", tmp_path / "approval.json", tmp_path / "inventory.csv",
                           tmp_path / "runs", resume=last)
    assert "--resume" in cmd and cmd[-1] == str(last)
    evaluation = evaluation_command(ROOT, tmp_path / "split.csv", tmp_path / "approval.json",
                                    tmp_path / "inventory.csv", last, tmp_path / "evaluation", final_test=True)
    assert "--final-test" in evaluation and evaluation[evaluation.index("--split") + 1] == "test"
    notebook = nbformat.read(ROOT / "notebooks/nine_class_colab_training.ipynb", as_version=4)
    nbformat.validate(notebook)
    sources = "\n".join(cell.source for cell in notebook.cells)
    assert "validate_colab_runtime(torch, torchvision)" in sources
    assert "nine_class_training_t4_v1.json" in sources
    assert "2.11.0+cu128" not in sources
    assert "RUN_TRAINING = False" in sources and "RUN_RESUME = False" in sources
    assert "RUN_FINAL_TEST = False" in sources and "validate_cohort(" in sources
    assert "--validate-only" not in sources or "validate_only=True" in sources
    assert not any(cell.outputs or cell.execution_count is not None for cell in notebook.cells if cell.cell_type == "code")
    for cell in notebook.cells:
        if cell.cell_type == "code":
            compile(cell.source, "<notebook>", "exec")
