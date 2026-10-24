"""Synthetic Stage 10 preprocessing and safety checks; no clinical images or training."""

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nine_class_dataset import PreprocessConfig, image_tensor, preprocessing_for_training, preprocessing_hash
from nine_class_external_evaluation import compare_evaluation_reports
from nine_class_stage4 import CLASS_NAMES
from nine_class_stage10_audit import VARIANTS, mild_luminance_retinex, variant_rgb
from nine_class_training import load_config, main as training_main
from preprocessing import retinex


def test_retinex_numerical_stability_and_mild_gain():
    for value in (0, 128, 255):
        uniform = np.full((16, 16, 3), value, dtype=np.uint8)
        assert retinex(uniform).dtype == np.uint8
        corrected = mild_luminance_retinex(uniform)
        assert corrected.dtype == np.uint8 and np.isfinite(corrected).all()
        assert np.array_equal(corrected, uniform)
    with pytest.raises(ValueError):
        mild_luminance_retinex(np.zeros((5, 5, 3), np.float32))


def test_versioning_keeps_exact_legacy_hash_and_separates_raw():
    legacy = PreprocessConfig()
    old_settings = asdict(legacy)
    old_settings.pop("pipeline_version")
    expected = hashlib.sha256(json.dumps(old_settings, sort_keys=True).encode()).hexdigest()
    assert preprocessing_hash(legacy) == expected
    raw = preprocessing_for_training({"image_size": 384, "preprocessing_mode": "raw_resize_imagenet_v2"})
    assert raw.pipeline_version == "raw_resize_imagenet_v2"
    assert preprocessing_hash(raw) != expected
    declared = json.loads((Path(__file__).resolve().parents[1] /
                           "config/nine_class_preprocessing_raw_v2.json").read_text(encoding="utf-8"))
    assert declared["pipeline_version"] == raw.pipeline_version
    assert declared["image_size"] == raw.image_size
    assert declared["mean"] == list(raw.mean) and declared["std"] == list(raw.std)
    assert preprocessing_hash(preprocessing_for_training({"image_size": 384})) == expected
    with pytest.raises(ValueError, match="Unknown preprocessing"):
        PreprocessConfig(pipeline_version="unreviewed")


def test_rgb_bgr_and_deterministic_eval_without_changing_raw(tmp_path):
    path = tmp_path / "red.png"
    bgr = np.zeros((24, 24, 3), dtype=np.uint8)
    bgr[..., 2] = 255
    assert cv2.imwrite(str(path), bgr)
    original = path.read_bytes()
    config = PreprocessConfig(image_size=24, pipeline_version="raw_resize_imagenet_v2")
    first = image_tensor(path, config, train=False)
    torch.manual_seed(999)
    second = image_tensor(path, config, train=False)
    assert torch.equal(first, second)
    assert first.shape == (3, 24, 24) and torch.isfinite(first).all()
    assert torch.allclose(first[:, 0, 0], torch.tensor([(1-.485)/.229, (0-.456)/.224, (0-.406)/.225]))
    assert path.read_bytes() == original
    assert np.all(variant_rgb(bgr, "A_raw", config) == np.array([255, 0, 0], dtype=np.uint8))


def test_bounded_variants_are_finite_and_do_not_mutate_input():
    image = np.random.default_rng(42).integers(1, 254, size=(32, 32, 3), dtype=np.uint8)
    before = image.copy()
    for name in VARIANTS:
        result = variant_rgb(image, name, PreprocessConfig(image_size=32))
        assert result.shape == (32, 32, 3) and result.dtype == np.uint8
        assert np.isfinite(result).all()
    assert np.array_equal(image, before)


def test_training_config_and_missing_approval_fail_before_model_creation(tmp_path, monkeypatch):
    default = load_config(Path(__file__).resolve().parents[1] / "config/nine_class_training_v1.json")
    assert preprocessing_for_training(default).pipeline_version == "stage4_full_v1"
    raw = {**default, "preprocessing_mode": "raw_resize_imagenet_v2"}
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert preprocessing_for_training(load_config(path)).pipeline_version == "raw_resize_imagenet_v2"
    import nine_class_training
    monkeypatch.setattr(nine_class_training, "build_model", lambda *_: pytest.fail("model constructed"))
    monkeypatch.setattr(sys, "argv", ["training", "--root", str(tmp_path),
                    "--config", str(path), "--approved-split", str(tmp_path / "missing.csv"),
                    "--approval", str(tmp_path / "missing.json"), "--inventory", str(tmp_path / "missing_inventory.csv")])
    with pytest.raises(FileNotFoundError, match="Approved cohort input missing"):
        training_main()
    assert not list(tmp_path.rglob("*.pt"))


def test_external_comparison_uses_run_frozen_raw_version_hash():
    raw_hash = preprocessing_hash(PreprocessConfig(pipeline_version="raw_resize_imagenet_v2"))
    run = {"config_sha256": "cfg", "preprocess_config_sha256": raw_hash,
           "config": {"label_order": list(CLASS_NAMES), "image_size": 384,
                      "preprocessing_mode": "raw_resize_imagenet_v2"}}
    internal = {"split": "test", "all_nine_classes_present": True, "accuracy": .5,
                "macro_f1": .4, "per_class": {name: {"recall": .4} for name in CLASS_NAMES},
                "provenance": {"config_sha256": "cfg", "checkpoint_sha256": "ckpt"}}
    external = {"scope": "full_nine_class", "supported_classes": list(CLASS_NAMES),
                "preprocess_config_sha256": raw_hash, "full_nine_accuracy": .4,
                "macro_f1_supported": .3, "per_class": {name: {"recall": .3} for name in CLASS_NAMES},
                "provenance": {"checkpoint_sha256": "ckpt"}}
    assert compare_evaluation_reports(internal, external, run)["comparable"]
    external["preprocess_config_sha256"] = preprocessing_hash(PreprocessConfig())
    assert not compare_evaluation_reports(internal, external, run)["comparable"]
