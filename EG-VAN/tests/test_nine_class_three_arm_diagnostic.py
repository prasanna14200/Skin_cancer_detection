import csv
import json
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import nine_class_exploratory as exploratory_module
import nine_class_three_arm_diagnostic as diagnostic
import nine_class_stage4 as stage4_module
import nine_class_training as training_module
from nine_class_training import configure_batchnorm_mode
import nine_class_dataset as dataset_module
from nine_class_dataset import (
    NineClassDataset,
    PreprocessConfig,
    augmentation_generator,
    apply_training_augmentations,
    derive_augmentation_seed,
)
from nine_class_stage4 import CLASS_NAMES


def test_model_state_hash_is_order_independent_and_binds_tensor_metadata():
    first = {
        "weight": torch.tensor([[1.0, 2.0]], dtype=torch.float32),
        "counter": torch.tensor(3, dtype=torch.int64),
    }
    reversed_order = {"counter": first["counter"], "weight": first["weight"]}
    assert diagnostic.model_state_sha256(first) == diagnostic.model_state_sha256(reversed_order)

    changed_value = dict(first, weight=torch.tensor([[1.0, 2.5]], dtype=torch.float32))
    changed_shape = dict(first, weight=torch.tensor([1.0, 2.0], dtype=torch.float32))
    assert diagnostic.model_state_sha256(first) != diagnostic.model_state_sha256(changed_value)
    assert diagnostic.model_state_sha256(first) != diagnostic.model_state_sha256(changed_shape)


def test_augmentation_is_repeatable_from_seed_epoch_and_sample():
    tensor = torch.arange(3 * 7 * 9, dtype=torch.float32).reshape(3, 7, 9)
    first_generator = augmentation_generator(42, 2, 11)
    second_generator = augmentation_generator(42, 2, 11)

    first = apply_training_augmentations(tensor.clone(), generator=first_generator)
    second = apply_training_augmentations(tensor.clone(), generator=second_generator)

    assert torch.equal(first, second)
    assert derive_augmentation_seed(42, 2, 11) != derive_augmentation_seed(42, 2, 12)
    assert derive_augmentation_seed(42, 2, 11) != derive_augmentation_seed(42, 3, 11)


def test_repeated_training_sample_access_is_deterministic_without_reading_images(
    tmp_path, monkeypatch
):
    split_csv = tmp_path / "synthetic_split.csv"
    with split_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=("image_path", "class_name", "class_index", "split")
        )
        writer.writeheader()
        writer.writerow({
            "image_path": "synthetic/train_sample.jpg",
            "class_name": CLASS_NAMES[0],
            "class_index": "0",
            "split": "train",
        })

    def synthetic_image_tensor(path, config, *, train=False, generator=None):
        source = torch.arange(3 * 5 * 7, dtype=torch.float32).reshape(3, 5, 7)
        return apply_training_augmentations(source, generator=generator) if train else source

    monkeypatch.setattr(dataset_module, "image_tensor", synthetic_image_tensor)
    dataset = NineClassDataset(
        tmp_path, split_csv, "train", PreprocessConfig(image_size=4), augmentation_seed=42
    )
    first_epoch_first = dataset[0][0]
    first_epoch_repeat = dataset[0][0]
    assert torch.equal(first_epoch_first, first_epoch_repeat)

    dataset.set_epoch(1)
    second_epoch_first = dataset[0][0]
    second_epoch_repeat = dataset[0][0]
    assert torch.equal(second_epoch_first, second_epoch_repeat)
    assert derive_augmentation_seed(42, 0, 0) != derive_augmentation_seed(42, 1, 0)


def test_inverse_sqrt_weights_use_training_rows_and_have_mean_one():
    rows = []
    expected_counts = {}
    for index, name in enumerate(CLASS_NAMES, start=1):
        expected_counts[name] = index
        rows.extend({"split": "train", "class_name": name} for _ in range(index))

    counts, weights = diagnostic.inverse_sqrt_class_weights(rows)
    raw = {name: 1.0 / np.sqrt(count) for name, count in expected_counts.items()}
    mean_raw = sum(raw.values()) / len(CLASS_NAMES)

    assert counts == expected_counts
    assert np.mean(list(weights.values())) == pytest.approx(1.0)
    for name in CLASS_NAMES:
        assert weights[name] == pytest.approx(raw[name] / mean_raw)
    sample_weighted_mean = diagnostic.training_sample_weighted_mean(counts, weights)
    assert sample_weighted_mean == pytest.approx(
        sum(expected_counts[name] * weights[name] for name in CLASS_NAMES)
        / sum(expected_counts.values())
    )

    with pytest.raises(ValueError, match="training rows only"):
        diagnostic.inverse_sqrt_class_weights(
            [*rows, {"split": "validation", "class_name": CLASS_NAMES[0]}]
        )
    with pytest.raises(ValueError, match="all nine classes"):
        diagnostic.inverse_sqrt_class_weights(
            [row for row in rows if row["class_name"] != CLASS_NAMES[-1]]
        )


def test_base_configuration_is_preserved_and_diagnostic_overrides_are_explicit():
    base_config = {
        "label_order": CLASS_NAMES,
        "batch_size": 8,
        "gradient_accumulation_steps": 4,
        "optimizer": "Adamax",
        "learning_rate": 0.001,
        "mixed_precision": "cuda_if_available",
        "num_workers": 0,
        "epochs": 25,
        "batchnorm_policy": "freeze_running_stats",
        "class_weighting": False,
        "focal_alpha": 0.25,
        "focal_gamma": 2.0,
        "initialization": {"mode": "random"},
    }
    original = {**base_config, "initialization": dict(base_config["initialization"])}

    diagnostic._validate_base_configuration(base_config)
    for arm in diagnostic.ARM_DEFINITIONS:
        config = diagnostic._arm_configuration(base_config, arm)
        overrides = config["diagnostic_overrides"]
        assert config["learning_rate"] == 0.0001
        assert config["mixed_precision"] == "off"
        assert config["epochs"] == 5
        assert overrides["base_learning_rate"] == 0.001
        assert overrides["learning_rate"] == 0.0001
        assert overrides["base_mixed_precision"] == "cuda_if_available"
        assert overrides["mixed_precision"] == "off"
        assert overrides["grad_scaler_enabled"] is False
        assert config["batch_size"] == 8
        assert config["gradient_accumulation_steps"] == 4
        assert base_config == original

    with pytest.raises(ValueError, match="Base configuration"):
        diagnostic._validate_base_configuration({**base_config, "learning_rate": 0.0001})
    with pytest.raises(ValueError, match="Base configuration"):
        diagnostic._validate_base_configuration({**base_config, "mixed_precision": "off"})


def test_focal_loss_distinguishes_invalid_targets_hyperparameters_and_logits():
    logits = torch.zeros((2, len(CLASS_NAMES)))
    valid_targets = torch.tensor([0, 8], dtype=torch.long)

    with pytest.raises(ValueError, match="torch.long vector"):
        training_module.focal_loss(logits, valid_targets.float())
    with pytest.raises(ValueError, match=r"indices in \[0, 8\]"):
        training_module.focal_loss(logits, torch.tensor([0, 9], dtype=torch.long))
    with pytest.raises(ValueError, match="hyperparameters"):
        training_module.focal_loss(logits, valid_targets, gamma=float("nan"))
    with pytest.raises(FloatingPointError, match="Focal loss is non-finite"):
        training_module.focal_loss(logits, valid_targets, alpha=1e308)
    with pytest.raises(FloatingPointError, match="logits contain non-finite"):
        training_module.focal_loss(
            torch.tensor([[float("nan")] + [0.0] * 8, [0.0] * 9]),
            valid_targets,
        )


def test_focal_loss_rejects_nonfinite_reduced_scalar(monkeypatch):
    logits = torch.zeros((2, len(CLASS_NAMES)))
    targets = torch.tensor([0, 8], dtype=torch.long)
    original_mean = torch.Tensor.mean
    reduced_values = []

    def nonfinite_reduction(values, *args, **kwargs):
        if values.ndim == 1 and values.shape == targets.shape:
            assert torch.isfinite(values).all().item()
            reduced = torch.full((), float("inf"), dtype=values.dtype, device=values.device)
            reduced_values.append(reduced)
            return reduced
        return original_mean(values, *args, **kwargs)

    with monkeypatch.context() as scoped_patch:
        scoped_patch.setattr(torch.Tensor, "mean", nonfinite_reduction)
        with pytest.raises(FloatingPointError, match="Reduced focal loss is non-finite"):
            training_module.focal_loss(logits, targets)

    assert len(reduced_values) == 1
    assert not torch.isfinite(reduced_values[0]).item()


def _training_config():
    return {
        "mixed_precision": "off",
        "focal_alpha": 0.25,
        "focal_gamma": 2.0,
        "gradient_accumulation_steps": 1,
        "batchnorm_policy": "train_running_stats",
    }


class _InfiniteGradient(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value):
        return value

    @staticmethod
    def backward(ctx, gradient):
        return torch.full_like(gradient, float("inf"))


class _InfiniteGradientModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones((2, 9)))

    def forward(self, inputs):
        return _InfiniteGradient.apply(inputs @ self.weight)


def test_run_epoch_rejects_nonfinite_gradients_before_optimizer_step():
    model = _InfiniteGradientModel()
    before = model.weight.detach().clone()
    optimizer = torch.optim.Adamax(model.parameters(), lr=0.001)
    loader = DataLoader(
        TensorDataset(torch.ones((1, 2)), torch.tensor([0], dtype=torch.long)),
        batch_size=1,
    )

    with pytest.raises(FloatingPointError, match="gradients contain non-finite"):
        training_module.run_epoch(
            model, loader, torch.device("cpu"), _training_config(), optimizer=optimizer
        )

    assert torch.equal(model.weight, before)
    assert not optimizer.state


def test_run_epoch_records_a_finite_optimizer_update():
    model = torch.nn.Linear(2, 9)
    optimizer = torch.optim.Adamax(model.parameters(), lr=0.001)
    loader = DataLoader(
        TensorDataset(torch.ones((2, 2)), torch.tensor([0, 1], dtype=torch.long)),
        batch_size=2,
    )

    report = training_module.run_epoch(
        model, loader, torch.device("cpu"), _training_config(), optimizer=optimizer
    )

    assert report["optimizer_steps"] == 1
    assert report["scaler_skipped_steps"] == 0
    assert np.isfinite(report["max_gradient_norm"])


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ("parameter", "Model parameters contain non-finite values before the epoch"),
        ("parameter_after_step", "Model parameters contain non-finite values after optimizer step"),
        ("optimizer_state", "Optimizer state contains non-finite values after optimizer step"),
    ],
)
def test_run_epoch_rejects_nonfinite_parameters_and_optimizer_state(
    failure, message
):
    model = torch.nn.Linear(2, 9)
    optimizer = torch.optim.Adamax(model.parameters(), lr=0.001)
    if failure == "parameter":
        with torch.no_grad():
            model.weight[0, 0] = float("nan")
    elif failure == "parameter_after_step":
        original_step = optimizer.step

        def step_with_invalid_parameter(*args, **kwargs):
            result = original_step(*args, **kwargs)
            with torch.no_grad():
                model.weight[0, 0] = float("inf")
            return result

        optimizer.step = step_with_invalid_parameter
    else:
        original_step = optimizer.step

        def step_with_invalid_state(*args, **kwargs):
            result = original_step(*args, **kwargs)
            parameter = next(iter(optimizer.state))
            optimizer.state[parameter]["synthetic_invalid_state"] = torch.tensor(float("nan"))
            return result

        optimizer.step = step_with_invalid_state
    loader = DataLoader(
        TensorDataset(torch.ones((1, 2)), torch.tensor([0], dtype=torch.long)),
        batch_size=1,
    )

    with pytest.raises(FloatingPointError, match=message):
        training_module.run_epoch(
            model, loader, torch.device("cpu"), _training_config(), optimizer=optimizer
        )


def test_epoch_sample_order_and_hash_are_repeatable():
    first = diagnostic.epoch_sample_order(37, 42, 3)
    second = diagnostic.epoch_sample_order(37, 42, 3)

    assert first == second
    assert len(set(first)) == 37
    assert diagnostic.sample_order_sha256(first) == diagnostic.sample_order_sha256(second)
    assert diagnostic.sample_order_sha256(first) != diagnostic.sample_order_sha256(
        diagnostic.epoch_sample_order(37, 42, 4)
    )


def test_dataset_constructor_guard_rejects_non_diagnostic_splits(monkeypatch, tmp_path):
    calls = []

    class DatasetSpy:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

    monkeypatch.setattr(diagnostic, "NineClassDataset", DatasetSpy)
    with pytest.raises(ValueError, match="only train and validation"):
        diagnostic.construct_diagnostic_dataset(
            tmp_path, tmp_path / "split.csv", "test", PreprocessConfig(), 42
        )
    assert calls == []


def test_diagnostic_dataset_factory_requests_only_train_and_validation(monkeypatch, tmp_path):
    observed = []

    def dataset_factory(root, split_csv, split, preprocess, seed):
        observed.append(split)
        return type("Dataset", (), {"split": split})()

    monkeypatch.setattr(diagnostic, "construct_diagnostic_dataset", dataset_factory)
    train, validation = diagnostic._create_datasets(
        tmp_path, tmp_path / "synthetic.csv", PreprocessConfig(), 42
    )
    assert train.split == "train"
    assert validation.split == "validation"
    assert observed == ["train", "validation"]
    assert diagnostic.ALLOWED_IMAGE_PARTITIONS == frozenset({"train", "validation"})


def test_validation_predictions_require_sequential_label_alignment():
    class Dataset:
        rows = [
            {"image_path": "synthetic/a.jpg", "class_index": "0"},
            {"image_path": "synthetic/b.jpg", "class_index": "1"},
        ]

    probabilities = np.zeros((2, len(CLASS_NAMES)), dtype=np.float32)
    probabilities[0, 0] = 1.0
    probabilities[1, 1] = 1.0
    records = diagnostic._validation_prediction_rows(
        Dataset(), probabilities, np.asarray([0, 1], dtype=np.int64), 1
    )
    assert [record["true_class"] for record in records] == list(CLASS_NAMES[:2])
    assert all(f"prob_{name}" in records[0] for name in CLASS_NAMES)

    with pytest.raises(ValueError, match="dataset row order"):
        diagnostic._validation_prediction_rows(
            Dataset(), probabilities, np.asarray([1, 0], dtype=np.int64), 1
        )


def test_numpy_metrics_are_json_serializable_and_confusion_csv_is_nine_by_nine(tmp_path):
    payload = {
        "array": np.asarray([[1, 2]], dtype=np.int64),
        "scalar": np.float32(0.5),
    }
    encoded = json.dumps(diagnostic._safe_json_value(payload), allow_nan=False)
    assert json.loads(encoded) == {"array": [[1, 2]], "scalar": pytest.approx(0.5)}

    matrix = [[row * len(CLASS_NAMES) + column for column in range(len(CLASS_NAMES))]
              for row in range(len(CLASS_NAMES))]
    path = tmp_path / "confusion.csv"
    diagnostic._write_confusion_matrix(path, matrix, epoch=1)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(CLASS_NAMES)
    assert list(rows[0]) == [
        "research_status", "cohort_status", "epoch", "true_class", *CLASS_NAMES
    ]
    assert int(rows[8][CLASS_NAMES[8]]) == matrix[8][8]


def test_experiment_directory_is_exclusive(tmp_path):
    first = diagnostic.create_experiment_directory(tmp_path, "diagnostic_fixture")
    assert first.is_dir()
    with pytest.raises(FileExistsError):
        diagnostic.create_experiment_directory(tmp_path, "diagnostic_fixture")


def test_experiment_lock_prevents_concurrent_runs_and_requires_stale_confirmation(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        diagnostic, "_process_is_alive", lambda pid: pid == diagnostic.os.getpid()
    )
    experiment_dir = tmp_path / "experiment"
    experiment_dir.mkdir()
    owner = diagnostic.ExperimentLock(experiment_dir)
    contender = diagnostic.ExperimentLock(experiment_dir)
    owner.acquire()
    with pytest.raises(RuntimeError, match="already locked"):
        contender.acquire()
    with pytest.raises(RuntimeError, match="active owner"):
        contender.acquire(resume=True, confirm_stale=True)
    owner.release()

    stale = {
        "token": "synthetic-stale-token",
        "pid": 999999,
        "host": diagnostic.platform.node(),
    }
    (experiment_dir / ".diagnostic.lock").write_text(json.dumps(stale), encoding="utf-8")
    with pytest.raises(RuntimeError, match="explicit stale-lock confirmation"):
        contender.acquire(resume=True)
    contender.acquire(resume=True, confirm_stale=True)
    contender.release()
    assert not (experiment_dir / ".diagnostic.lock").exists()


def test_windows_missing_process_is_stale(monkeypatch):
    error = OSError(22, "invalid process id")
    error.winerror = 87

    def missing_process(pid, signal):
        raise error

    monkeypatch.setattr(
        diagnostic, "os",
        type("OSProbe", (), {"name": "nt", "kill": staticmethod(missing_process)})(),
    )
    assert not diagnostic._process_is_alive(999999)


def _synthetic_checkpoint(
    arm_dir, *, arm_name, epoch, initial_hash, config_hash, split_hash, preprocess_hash,
    order_hashes, value,
):
    manifest_path = arm_dir / f"epoch_{epoch:02d}_manifest.json"
    manifest_path.write_text(json.dumps({"epoch": epoch}), encoding="utf-8")
    manifest_hash = diagnostic._sha256_file(manifest_path)
    model_state = {"weight": torch.tensor([float(value)], dtype=torch.float32)}
    return {
        "format_version": 2,
        "research_status": diagnostic.RESEARCH_STATUS,
        "cohort_status": diagnostic.COHORT_STATUS,
        "arm": arm_name,
        "completed_epochs": epoch,
        "model_state": model_state,
        "model_state_sha256": diagnostic.model_state_sha256(model_state),
        "optimizer_state": {"state": {}, "param_groups": []},
        "scheduler_state": None,
        "scaler_state": {},
        "initial_model_state_sha256": initial_hash,
        "configuration_sha256": config_hash,
        "split_sha256": split_hash,
        "preprocessing_fingerprint": preprocess_hash,
        "sample_order_sha256": order_hashes[epoch - 1],
        "epoch_manifest_sha256": manifest_hash,
    }


def _save_synthetic_checkpoint(arm_dir, *, epoch, value):
    arm_name = "arm_A_reference"
    order_hashes = tuple(
        diagnostic.sample_order_sha256((index,)) for index in range(5)
    )
    arguments = {
        "arm_name": arm_name,
        "initial_state_sha256": "a" * 64,
        "arm_config_sha256": "b" * 64,
        "split_sha256": "c" * 64,
        "preprocess_sha256": "d" * 64,
        "order_hashes": order_hashes,
    }
    payload = _synthetic_checkpoint(
        arm_dir,
        arm_name=arm_name,
        epoch=epoch,
        initial_hash=arguments["initial_state_sha256"],
        config_hash=arguments["arm_config_sha256"],
        split_hash=arguments["split_sha256"],
        preprocess_hash=arguments["preprocess_sha256"],
        order_hashes=order_hashes,
        value=value,
    )
    pointer = diagnostic._save_rolling_checkpoint(
        arm_dir,
        payload,
        arm_name=arm_name,
        initial_state_sha256=arguments["initial_state_sha256"],
        arm_config_sha256=arguments["arm_config_sha256"],
        split_sha256=arguments["split_sha256"],
        preprocess_sha256=arguments["preprocess_sha256"],
        order_hashes=order_hashes,
    )
    return pointer, arguments


def test_rolling_checkpoint_interruption_keeps_previous_valid_generation(
    tmp_path, monkeypatch
):
    arm_dir = tmp_path / "arm_A_reference"
    arm_dir.mkdir()
    first_pointer, arguments = _save_synthetic_checkpoint(
        arm_dir, epoch=1, value=1
    )
    first_path = arm_dir / first_pointer["filename"]
    original_write_json = diagnostic._write_json

    def interrupt_pointer_write(path, value, *, replace=False):
        if path.name == "last_checkpoint.json":
            raise OSError("synthetic pointer-write interruption")
        return original_write_json(path, value, replace=replace)

    monkeypatch.setattr(diagnostic, "_write_json", interrupt_pointer_write)
    with pytest.raises(OSError, match="pointer-write interruption"):
        _save_synthetic_checkpoint(arm_dir, epoch=2, value=2)
    monkeypatch.setattr(diagnostic, "_write_json", original_write_json)

    pointer_after = json.loads(
        (arm_dir / "last_checkpoint.json").read_text(encoding="utf-8")
    )
    assert pointer_after == first_pointer
    assert first_path.is_file()
    payload, _ = diagnostic._load_rolling_checkpoint(arm_dir, **arguments)
    assert payload["completed_epochs"] == 1
    assert int(payload["model_state"]["weight"].item()) == 1


def test_rolling_checkpoint_hash_mismatch_is_rejected(tmp_path):
    arm_dir = tmp_path / "arm_A_reference"
    arm_dir.mkdir()
    pointer, arguments = _save_synthetic_checkpoint(arm_dir, epoch=1, value=1)
    checkpoint_path = arm_dir / pointer["filename"]
    checkpoint_path.write_bytes(checkpoint_path.read_bytes() + b"corruption")

    with pytest.raises(ValueError, match="file hash mismatch"):
        diagnostic._load_rolling_checkpoint(arm_dir, **arguments)


def test_partial_checkpoint_write_does_not_replace_previous_generation(
    tmp_path, monkeypatch
):
    arm_dir = tmp_path / "arm_A_reference"
    arm_dir.mkdir()
    pointer, arguments = _save_synthetic_checkpoint(arm_dir, epoch=1, value=1)
    original_save = diagnostic.torch.save

    def interrupt_save(value, path, *args, **kwargs):
        Path(path).write_bytes(b"partial checkpoint")
        raise OSError("synthetic checkpoint-write interruption")

    monkeypatch.setattr(diagnostic.torch, "save", interrupt_save)
    with pytest.raises(OSError, match="checkpoint-write interruption"):
        _save_synthetic_checkpoint(arm_dir, epoch=2, value=2)
    monkeypatch.setattr(diagnostic.torch, "save", original_save)

    assert json.loads(
        (arm_dir / "last_checkpoint.json").read_text(encoding="utf-8")
    ) == pointer
    assert not list(arm_dir.glob(".rolling_checkpoint.*.tmp"))
    assert diagnostic._load_rolling_checkpoint(arm_dir, **arguments)[0][
        "completed_epochs"
    ] == 1


def test_output_root_rejects_protected_overlap_in_both_directions(tmp_path):
    protected = tmp_path / "protected"
    separate = tmp_path / "separate"
    assert diagnostic.validate_output_root(separate, [protected]) == separate.resolve()

    for candidate in (protected, protected / "child", tmp_path):
        with pytest.raises(ValueError, match="overlaps protected directory"):
            diagnostic.validate_output_root(candidate, [protected])


def test_production_protected_roots_cover_project_data_and_run_artifacts(tmp_path):
    from nine_class_stage4 import (
        DATA_RAW_RELATIVE,
        ISIC_DATA_RELATIVE,
        OUT as STAGE4_OUT,
        OVERLAP_COMPLETION_RELATIVE,
        RECOVERY_STAGE3I_RELATIVE,
        VALIDATION_DIAGNOSTICS_ROOT,
    )

    source_root = stage4_module.ROOT.resolve()

    def relocate(path):
        return (tmp_path / Path(path).resolve().relative_to(source_root)).resolve()

    protected = set(diagnostic.protected_output_roots(tmp_path))
    expected = {
        (tmp_path / "data").resolve(),
        (tmp_path / DATA_RAW_RELATIVE).resolve(),
        (tmp_path / ISIC_DATA_RELATIVE).resolve(),
        relocate(exploratory_module.OUT),
        relocate(exploratory_module.RUNS_ROOT),
        relocate(training_module.DEFAULT_RUNS_ROOT.parent),
        relocate(VALIDATION_DIAGNOSTICS_ROOT),
        relocate(STAGE4_OUT),
        relocate(exploratory_module.PREVIEW.parent),
        relocate(exploratory_module.CONFIG.parent),
        relocate(training_module.DEFAULT_CONFIG.parent),
        relocate(training_module.DEFAULT_INVENTORY.parent),
        (tmp_path / OVERLAP_COMPLETION_RELATIVE).resolve(),
        (tmp_path / RECOVERY_STAGE3I_RELATIVE).resolve(),
        (tmp_path / "checkpoints").resolve(),
        (tmp_path / "src").resolve(),
        (tmp_path / "tests").resolve(),
        (tmp_path / "notebooks").resolve(),
    }
    assert expected <= protected

    diagnostic_root = tmp_path / "analysis" / "nine_class_three_arm_diagnostics"
    assert diagnostic.validate_output_root(
        diagnostic_root, tuple(protected), project_root=tmp_path
    ) == diagnostic_root.resolve()

    for protected_root in protected:
        for candidate in (protected_root, protected_root / "child", protected_root.parent):
            with pytest.raises(ValueError):
                diagnostic.validate_output_root(
                    candidate, tuple(protected), project_root=tmp_path
                )


def test_actual_project_checkpoint_and_analysis_roots_are_protected():
    project_root = stage4_module.ROOT.resolve()
    protected = set(diagnostic.protected_output_roots(project_root))
    assert (project_root / "checkpoints").resolve() in protected
    analysis_roots = {
        path.resolve()
        for path in (project_root / "analysis").iterdir()
        if path.is_dir() and path.name != "nine_class_three_arm_diagnostics"
    }
    assert analysis_roots <= protected
    diagnostic_root = project_root / "analysis" / "nine_class_three_arm_diagnostics"
    assert diagnostic.validate_output_root(
        diagnostic_root, tuple(protected), project_root=project_root
    ) == diagnostic_root.resolve()

    protected_candidates = {
        project_root / "checkpoints",
        project_root / "checkpoints" / "new",
        *analysis_roots,
        *(path / "new" for path in analysis_roots),
    }
    for candidate in protected_candidates:
        with pytest.raises(ValueError, match="overlaps protected directory"):
            diagnostic.validate_output_root(
                candidate, tuple(protected), project_root=project_root
            )


def test_colab_notebooks_use_project_shortcut_and_diagnostic_only_entrypoint():
    notebooks = Path(__file__).resolve().parents[1] / "notebooks"
    project_path = (
        "/content/drive/.shortcut-targets-by-id/"
        "1O_G4-Fo1RGgNekg9RSyjdipPkUnylKh4/EG-VAN"
    )
    exploratory = json.loads(
        (notebooks / "nine_class_exploratory_colab.ipynb").read_text(encoding="utf-8")
    )
    exploratory_source = "\n".join(
        line
        for cell in exploratory["cells"]
        for line in (
            cell["source"] if isinstance(cell["source"], list) else [cell["source"]]
        )
    )
    assert project_path in exploratory_source
    assert "preflight_diagnostic(PROJECT)" in exploratory_source
    assert "src/nine_class_three_arm_diagnostic.py" in exploratory_source
    assert "RUN_DIAGNOSTIC = False" in exploratory_source
    assert "RUN_RESUME = False" in exploratory_source
    assert "nine_class_exploratory.py" not in exploratory_source
    assert "/content/drive/MyDrive/EG-VAN" not in exploratory_source

    approved = json.loads(
        (notebooks / "nine_class_colab_training.ipynb").read_text(encoding="utf-8")
    )
    approved_source = "\n".join(
        cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])
        for cell in approved["cells"]
    )
    assert project_path in approved_source
    assert "/content/drive/MyDrive/EG-VAN" not in approved_source
    assert "RUN_TRAINING = False" in approved_source


def test_output_root_rejects_traversal_and_symlink_escape(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    protected = diagnostic.protected_output_roots(project_root)

    with pytest.raises(ValueError, match="parent traversal"):
        diagnostic.validate_output_root(
            project_root / "safe" / ".." / "output",
            protected,
            project_root=project_root,
        )
    for unsafe in (Path(r"C:\outside\output"), Path(r"\\server\share\output")):
        with pytest.raises(ValueError):
            diagnostic.validate_output_root(
                unsafe, protected, project_root=project_root
            )

    candidate = project_root / "linked-output" / "runs"
    outside = tmp_path / "outside" / "runs"
    original_resolve = Path.resolve

    def resolve_with_symlink_escape(path, *args, **kwargs):
        if path == candidate:
            return outside
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_with_symlink_escape)
    with pytest.raises(ValueError, match="project root"):
        diagnostic.validate_output_root(
            candidate, protected, project_root=project_root
        )


def test_status_lifecycle_does_not_complete_partial_work(tmp_path):
    status_path = tmp_path / "status.json"
    diagnostic.update_status(status_path, "created", 0, 5, progress_name="completed_epochs")
    diagnostic.update_status(status_path, "running", 0, 5, progress_name="completed_epochs")
    with pytest.raises(ValueError, match="incomplete work"):
        diagnostic.update_status(status_path, "completed", 2, 5,
                                 progress_name="completed_epochs")

    diagnostic.update_status(status_path, "running", 2, 5, progress_name="completed_epochs")
    diagnostic.update_status(status_path, "interrupted", 2, 5,
                              progress_name="completed_epochs", error="synthetic interruption")
    with pytest.raises(ValueError, match="Invalid status transition"):
        diagnostic.update_status(status_path, "completed", 5, 5,
                                 progress_name="completed_epochs")


def test_status_required_progress_cannot_change(tmp_path):
    status_path = tmp_path / "status.json"
    diagnostic.update_status(status_path, "created", 0, 5, progress_name="completed_epochs")

    with pytest.raises(ValueError, match="required progress cannot change"):
        diagnostic.update_status(
            status_path, "running", 0, 4, progress_name="completed_epochs"
        )
    diagnostic.update_status(
        status_path, "running", 1, 5, progress_name="completed_epochs"
    )

    with pytest.raises(ValueError, match="required progress cannot change"):
        diagnostic.update_status(
            status_path, "completed", 2, 2, progress_name="completed_epochs"
        )

    record = json.loads(status_path.read_text(encoding="utf-8"))
    assert record["status"] == "running"
    assert record["required_progress"] == 5


@pytest.mark.parametrize(
    ("progress", "required_progress"),
    [
        (True, 5),
        (1.5, 5),
        (0, True),
        (0, 5.5),
    ],
)
def test_status_progress_requires_integer_values(
    tmp_path, progress, required_progress
):
    status_path = tmp_path / "status.json"
    with pytest.raises(ValueError, match="Invalid status or progress"):
        diagnostic.update_status(
            status_path,
            "created",
            progress,
            required_progress,
            progress_name="completed_epochs",
        )
    assert not status_path.exists()


def test_status_normal_completion_and_interrupted_resume_still_work(tmp_path):
    completed_path = tmp_path / "completed.json"
    diagnostic.update_status(
        completed_path, "created", 0, 2, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        completed_path, "running", 1, 2, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        completed_path, "completed", 2, 2, progress_name="completed_epochs"
    )
    assert json.loads(completed_path.read_text(encoding="utf-8"))["status"] == "completed"

    resumed_path = tmp_path / "resumed.json"
    diagnostic.update_status(
        resumed_path, "created", 0, 2, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        resumed_path, "running", 1, 2, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        resumed_path, "interrupted", 1, 2, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        resumed_path,
        "running",
        1,
        2,
        progress_name="completed_epochs",
        allow_resume=True,
    )
    diagnostic.update_status(
        resumed_path, "running", 2, 2, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        resumed_path, "completed", 2, 2, progress_name="completed_epochs"
    )
    assert json.loads(resumed_path.read_text(encoding="utf-8"))["status"] == "completed"


def test_experiment_failure_and_interruption_status_are_persisted(tmp_path):
    for terminal_status in ("failed", "interrupted"):
        status_path = tmp_path / f"{terminal_status}.json"
        diagnostic._persist_experiment_terminal_status(
            status_path,
            terminal_status,
            3,
            progress_name="completed_arms",
            error="synthetic setup failure",
        )
        record = json.loads(status_path.read_text(encoding="utf-8"))
        assert record["status"] == terminal_status
        assert record["completed_arms"] == 0
        assert record["error"] == "synthetic setup failure"


def test_arm_failure_handler_preserves_existing_terminal_status(tmp_path):
    status_path = tmp_path / "arm_status.json"
    diagnostic.update_status(
        status_path, "created", 0, 5, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        status_path, "running", 0, 5, progress_name="completed_epochs"
    )
    diagnostic.update_status(
        status_path, "completed", 5, 5, progress_name="completed_epochs"
    )

    diagnostic._persist_arm_terminal_status(
        status_path, "failed", 5, error="late synthetic failure"
    )
    record = json.loads(status_path.read_text(encoding="utf-8"))
    assert record["status"] == "completed"
    assert record["completed_epochs"] == 5
    assert "error" not in record


@pytest.mark.parametrize(
    ("failure_point", "expected_status"),
    [
        ("arm_setup", "failed"),
        ("initialization", "failed"),
        ("initial_state", "failed"),
        ("manifest", "failed"),
        ("interruption", "interrupted"),
        ("initial_arm_status", "failed"),
        ("initial_arm_interrupt", "interrupted"),
        ("initial_arm_status_write_failure", "failed"),
        ("later_arm_execution", "failed"),
    ],
)
def test_experiment_setup_failures_persist_parent_status(
    tmp_path, monkeypatch, failure_point, expected_status
):
    root = tmp_path / "project"
    root.mkdir()
    base_config = {
        "label_order": CLASS_NAMES,
        "batch_size": 8,
        "gradient_accumulation_steps": 4,
        "optimizer": "Adamax",
        "learning_rate": 0.001,
        "mixed_precision": "cuda_if_available",
        "num_workers": 0,
        "epochs": 25,
        "batchnorm_policy": "freeze_running_stats",
        "class_weighting": False,
        "focal_alpha": 0.25,
        "focal_gamma": 2.0,
        "initialization": {"mode": "random"},
        "seed": 42,
        "image_size": 384,
    }

    exploratory = ModuleType("nine_class_exploratory")
    exploratory.CONFIG = exploratory_module.CONFIG
    exploratory.OUT = exploratory_module.OUT
    exploratory.PREVIEW = exploratory_module.PREVIEW
    exploratory.REPORT = exploratory_module.REPORT
    exploratory.RUNS_ROOT = exploratory_module.RUNS_ROOT
    exploratory.SIIM_DECISIONS = exploratory_module.SIIM_DECISIONS
    exploratory.SPLIT = root / "synthetic_split.csv"
    exploratory.validate_frozen = lambda *args, **kwargs: (
        [{"approval_status": "NOT_APPROVED"}],
        {
            "status": diagnostic.RESEARCH_STATUS,
            "config_sha256": "a" * 64,
            "split_sha256": "b" * 64,
        },
    )
    training = ModuleType("nine_class_training")
    training.DEFAULT_CONFIG = training_module.DEFAULT_CONFIG
    training.DEFAULT_INVENTORY = training_module.DEFAULT_INVENTORY
    training.DEFAULT_RUNS_ROOT = training_module.DEFAULT_RUNS_ROOT
    training.load_config = lambda path: base_config
    training.run_epoch = lambda *args, **kwargs: None
    training.seed_all = lambda seed: None

    def fail_initialization(config, model_root):
        raise RuntimeError("synthetic initialization failure")

    training.build_model = (
        fail_initialization if failure_point == "initialization"
        else lambda config, model_root: (_SyntheticModel(), {})
    )
    monkeypatch.setitem(sys.modules, "nine_class_exploratory", exploratory)
    monkeypatch.setitem(sys.modules, "nine_class_training", training)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)

    class Dataset(_SyntheticDataset):
        def __init__(self, split):
            super().__init__(split)
            self.rows = [
                {"split": split, "class_name": name, "class_index": str(index),
                 "image_path": f"synthetic/{split}_{index}.jpg"}
                for index, name in enumerate(CLASS_NAMES)
            ]

    monkeypatch.setattr(
        diagnostic, "_create_datasets",
        lambda *args: (Dataset("train"), Dataset("validation")),
    )
    monkeypatch.setattr(diagnostic, "_runtime_metadata", lambda device: {"synthetic": True})
    if failure_point in ("arm_setup", "interruption"):
        def fail_arm_setup(config, arm):
            if failure_point == "interruption":
                raise KeyboardInterrupt("synthetic setup interruption")
            raise RuntimeError("synthetic arm setup failure")
        monkeypatch.setattr(diagnostic, "_arm_configuration", fail_arm_setup)
    elif failure_point in (
        "initial_arm_status",
        "initial_arm_interrupt",
        "initial_arm_status_write_failure",
    ):
        original_update_status = diagnostic.update_status
        initial_transition_seen = False

        def fail_initial_arm_transition(path, status, progress, required_progress, *,
                                        progress_name, error=None, allow_resume=False):
            nonlocal initial_transition_seen
            is_initial_arm = (
                path.parent.name == diagnostic.ARM_DEFINITIONS[0][0]
                and status == "running"
                and not initial_transition_seen
            )
            if is_initial_arm:
                initial_transition_seen = True
                if failure_point == "initial_arm_interrupt":
                    raise KeyboardInterrupt("synthetic initial arm interruption")
                raise RuntimeError("synthetic initial arm status transition failure")
            if (
                failure_point == "initial_arm_status_write_failure"
                and path.parent.name == diagnostic.ARM_DEFINITIONS[0][0]
                and status == "failed"
            ):
                raise OSError("synthetic arm status persistence failure")
            return original_update_status(
                path, status, progress, required_progress,
                progress_name=progress_name, error=error, allow_resume=allow_resume,
            )

        monkeypatch.setattr(diagnostic, "update_status", fail_initial_arm_transition)
    elif failure_point == "later_arm_execution":
        training_epochs = 0

        def fail_during_arm_execution(*args, **kwargs):
            nonlocal training_epochs
            if kwargs.get("optimizer") is not None:
                training_epochs += 1
                if training_epochs == 3:
                    raise RuntimeError("synthetic later arm execution failure")
                return _synthetic_epoch_report(include_predictions=False)
            return _synthetic_epoch_report(
                include_predictions=kwargs.get("include_predictions", False)
            )

        training.run_epoch = fail_during_arm_execution
        monkeypatch.setattr(torch.nn.Module, "to", lambda self, *args, **kwargs: self)
        monkeypatch.setattr(
            diagnostic.torch.amp, "GradScaler", lambda *args, **kwargs: _SyntheticScaler()
        )
    elif failure_point == "initial_state":
        def fail_initial_state(experiment_dir, state_dict):
            raise RuntimeError("synthetic initial-state failure")
        monkeypatch.setattr(diagnostic, "_write_initial_state", fail_initial_state)
    elif failure_point == "manifest":
        original_write_json = diagnostic._write_json

        def fail_manifest(path, value, *, replace=False):
            if Path(path).name == "experiment_manifest.json":
                raise RuntimeError("synthetic manifest failure")
            return original_write_json(path, value, replace=replace)

        monkeypatch.setattr(diagnostic, "_write_json", fail_manifest)

    expected_exception = (
        KeyboardInterrupt
        if failure_point in ("interruption", "initial_arm_interrupt")
        else RuntimeError
    )
    with pytest.raises(expected_exception, match="synthetic") as caught:
        diagnostic.run_experiment(
            root=root,
            runs_root=root / "runs",
            experiment_id=f"failure-{failure_point}",
        )

    status_path = root / "runs" / f"failure-{failure_point}" / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    parent_status = (
        "interrupted"
        if failure_point in ("interruption", "initial_arm_interrupt")
        else "failed"
    )
    assert status["status"] == parent_status
    assert status["completed_arms"] == 0
    assert "synthetic" in status["error"]
    if failure_point.startswith("initial_arm_status"):
        arm_status_path = (
            root / "runs" / f"failure-{failure_point}"
            / diagnostic.ARM_DEFINITIONS[0][0] / "status.json"
        )
        arm_status = json.loads(arm_status_path.read_text(encoding="utf-8"))
        expected_arm_status = (
            "created" if failure_point == "initial_arm_status_write_failure"
            else expected_status
        )
        assert arm_status["status"] == expected_arm_status
        if failure_point == "initial_arm_status_write_failure":
            assert isinstance(caught.value.__cause__, OSError)
    elif failure_point == "later_arm_execution":
        arm_status_path = (
            root / "runs" / f"failure-{failure_point}"
            / diagnostic.ARM_DEFINITIONS[0][0] / "status.json"
        )
        arm_status = json.loads(arm_status_path.read_text(encoding="utf-8"))
        assert arm_status["status"] == "failed"
        assert arm_status["completed_epochs"] == 2
        manifest = json.loads(
            (status_path.parent / "experiment_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        assert manifest["diagnostic_overrides"] == {
            "base_learning_rate": 0.001,
            "learning_rate": 0.0001,
            "base_mixed_precision": "cuda_if_available",
            "mixed_precision": "off",
            "grad_scaler_enabled": False,
            "adaptive_scheduler": False,
        }


class _SyntheticDataset:
    def __init__(self, split):
        self.split = split
        self.augmentation_seed = 42
        self.rows = [
            {"image_path": f"synthetic/{index}.jpg", "class_index": str(index)}
            for index in range(len(CLASS_NAMES))
        ]
        self.epoch = 0

    def __len__(self):
        return len(self.rows)

    def set_epoch(self, epoch):
        self.epoch = epoch


class _SyntheticModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.bn = torch.nn.BatchNorm1d(2)
        self.head = torch.nn.Linear(2, 2)


class _SyntheticScaler:
    def __init__(self):
        self.state = {"updates": 0}

    def state_dict(self):
        return dict(self.state)

    def load_state_dict(self, state):
        self.state = dict(state)


def _synthetic_epoch_report(include_predictions):
    report = {
        "confusion_matrix": np.eye(len(CLASS_NAMES), dtype=np.int64).tolist(),
        "per_class": {
            name: {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 1}
            for name in CLASS_NAMES
        },
        "accuracy": 1.0,
        "macro_f1": 1.0,
        "weighted_f1": 1.0,
        "loss": 0.25,
    }
    if include_predictions:
        report["probabilities"] = np.eye(len(CLASS_NAMES), dtype=np.float32)
        report["targets"] = np.arange(len(CLASS_NAMES), dtype=np.int64)
    return report


def test_arm_resume_is_independent_and_replays_deterministic_epoch_inputs(
    tmp_path, monkeypatch
):
    image_operations = []
    original_resolve = Path.resolve
    original_is_file = Path.is_file
    original_open = Path.open
    original_stat = Path.stat

    def is_image_path(path):
        return path.suffix.lower() in {".jpg", ".jpeg", ".png"}

    def track_path_operation(operation, original, path, *args, **kwargs):
        if is_image_path(path):
            image_operations.append((operation, str(path)))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(
        Path, "resolve",
        lambda path, *args, **kwargs: track_path_operation(
            "resolve", original_resolve, path, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        Path, "is_file",
        lambda path: track_path_operation("is_file", original_is_file, path),
    )
    monkeypatch.setattr(
        Path, "open",
        lambda path, *args, **kwargs: track_path_operation(
            "open", original_open, path, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        Path, "stat",
        lambda path, *args, **kwargs: track_path_operation(
            "stat", original_stat, path, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        diagnostic.torch.amp, "GradScaler", lambda *args, **kwargs: _SyntheticScaler()
    )
    initial_model = _SyntheticModel()
    initial_state = {
        name: tensor.detach().clone()
        for name, tensor in initial_model.state_dict().items()
    }
    initial_state_path = tmp_path / "initial_model_state.pt"
    initial_hash = diagnostic._write_initial_state(tmp_path, initial_state)
    train_dataset = _SyntheticDataset("train")
    validation_dataset = _SyntheticDataset("validation")
    epoch_orders = tuple(
        diagnostic.epoch_sample_order(len(train_dataset), 42, epoch)
        for epoch in range(diagnostic.DIAGNOSTIC_EPOCHS)
    )
    order_hashes = tuple(diagnostic.sample_order_sha256(order) for order in epoch_orders)
    class_counts = {name: 1 for name in CLASS_NAMES}
    class_weights = {name: 1.0 for name in CLASS_NAMES}
    observations = {"A": [], "B": []}
    stop_epochs = {
        "arm_A_reference": 2,
        "arm_B_bn_update": 1,
    }

    def build_model(config, root):
        return _SyntheticModel(), {}

    def run_epoch_stub(model, loader, device, config, *, optimizer=None, scaler=None,
                       class_weights=None, include_predictions=False):
        arm_name = config["diagnostic_overrides"]["arm"]
        record = observations[arm_name]
        if optimizer is None:
            assert class_weights is None
            return _synthetic_epoch_report(include_predictions=include_predictions)

        dataset = loader.dataset
        epoch = dataset.epoch
        arm_directory = config["diagnostic_overrides"]["arm"]
        arm_directory = next(
            definition[0] for definition in diagnostic.ARM_DEFINITIONS
            if definition[1] == arm_directory
        )
        if stop_epochs[arm_directory] == epoch:
            raise KeyboardInterrupt("synthetic epoch interruption")
        record.append({
            "epoch": epoch,
            "sample_order": tuple(iter(loader.sampler)),
            "augmentation_seeds": tuple(
                derive_augmentation_seed(dataset.augmentation_seed, epoch, index)
                for index in range(len(dataset))
            ),
            "model_hash_before_step": diagnostic.model_state_sha256(model.state_dict()),
            "optimizer_restored": bool(optimizer.state),
            "scaler_updates_before_step": scaler.state["updates"],
        })
        optimizer.zero_grad()
        sum(parameter.sum() for parameter in model.parameters()).backward()
        optimizer.step()
        scaler.state["updates"] += 1
        record[-1]["model_hash_after_step"] = diagnostic.model_state_sha256(
            model.state_dict()
        )
        return _synthetic_epoch_report(include_predictions=False)

    arm_dirs = {}
    arm_configs = {}
    arm_hashes = {}
    for arm in diagnostic.ARM_DEFINITIONS[:2]:
        arm_name = arm[0]
        arm_dir = tmp_path / arm_name
        arm_dir.mkdir()
        arm_dirs[arm_name] = arm_dir
        diagnostic.update_status(
            arm_dir / "status.json", "created", 0, 5, progress_name="completed_epochs"
        )
        arm_config = diagnostic._arm_configuration(
            {
                "seed": 42,
                "batch_size": len(CLASS_NAMES),
                "learning_rate": 0.001,
                "mixed_precision": "cuda_if_available",
            },
            arm,
        )
        arm_configs[arm_name] = arm_config
        arm_hashes[arm_name] = diagnostic.hashlib.sha256(
            diagnostic.canonical_json_bytes(arm_config)
        ).hexdigest()

    common = {
        "root": tmp_path,
        "train_dataset": train_dataset,
        "validation_dataset": validation_dataset,
        "initial_state_path": initial_state_path,
        "initial_state_sha256": initial_hash,
        "epoch_orders": epoch_orders,
        "order_hashes": order_hashes,
        "class_counts": class_counts,
        "class_weights_by_name": class_weights,
        "sample_weighted_mean": 1.0,
        "split_sha256": "b" * 64,
        "preprocess_sha256": "c" * 64,
        "runtime": {"synthetic": True},
        "device": torch.device("cpu"),
        "build_model": build_model,
        "run_epoch": run_epoch_stub,
        "seed_all": lambda seed: None,
    }
    for arm in diagnostic.ARM_DEFINITIONS[:2]:
        arm_name = arm[0]
        with pytest.raises(KeyboardInterrupt, match="synthetic epoch interruption"):
            diagnostic._run_arm(
                arm=arm,
                arm_dir=arm_dirs[arm_name],
                arm_config=arm_configs[arm_name],
                arm_config_sha256=arm_hashes[arm_name],
                resume=False,
                **common,
            )
        status = json.loads((arm_dirs[arm_name] / "status.json").read_text())
        assert status["status"] == "interrupted"

    arm_b = arm_dirs["arm_B_bn_update"]
    arm_b_pointer_before = (arm_b / "last_checkpoint.json").read_bytes()
    arm_b_status_before = (arm_b / "status.json").read_bytes()
    stop_epochs["arm_A_reference"] = None
    arm_a = diagnostic.ARM_DEFINITIONS[0]
    diagnostic._run_arm(
        arm=arm_a,
        arm_dir=arm_dirs[arm_a[0]],
        arm_config=arm_configs[arm_a[0]],
        arm_config_sha256=arm_hashes[arm_a[0]],
        resume=True,
        **common,
    )

    arm_a_observations = observations["A"]
    assert [entry["epoch"] for entry in arm_a_observations] == list(range(5))
    assert [entry["sample_order"] for entry in arm_a_observations] == list(epoch_orders)
    assert [entry["augmentation_seeds"] for entry in arm_a_observations] == [
        tuple(derive_augmentation_seed(42, epoch, index) for index in range(len(train_dataset)))
        for epoch in range(5)
    ]
    assert arm_a_observations[0]["model_hash_before_step"] == initial_hash
    assert arm_a_observations[2]["optimizer_restored"]
    assert arm_a_observations[2]["scaler_updates_before_step"] == 2
    assert json.loads(
        (arm_dirs[arm_a[0]] / "status.json").read_text()
    )["status"] == "completed"
    with (arm_dirs[arm_a[0]] / "history.csv").open(newline="", encoding="utf-8") as handle:
        history = list(csv.DictReader(handle))
    assert [int(row["epoch"]) for row in history] == [1, 2, 3, 4, 5]
    assert (arm_b / "last_checkpoint.json").read_bytes() == arm_b_pointer_before
    assert (arm_b / "status.json").read_bytes() == arm_b_status_before
    assert json.loads((arm_b / "status.json").read_text())["completed_epochs"] == 1
    assert image_operations == []


def test_three_arm_synthetic_integration_preserves_shared_state_and_arm_isolation(
    tmp_path, monkeypatch
):
    scaler_enabled = []

    def make_scaler(*args, **kwargs):
        scaler_enabled.append(kwargs["enabled"])
        return _SyntheticScaler()

    monkeypatch.setattr(
        diagnostic.torch.amp, "GradScaler", make_scaler
    )
    experiment_dir = tmp_path / "synthetic_experiment"
    experiment_dir.mkdir()
    initial_model = _SyntheticModel()
    initial_state = {
        name: tensor.detach().clone()
        for name, tensor in initial_model.state_dict().items()
    }
    initial_state_path = experiment_dir / "initial_model_state.pt"
    initial_hash = diagnostic._write_initial_state(experiment_dir, initial_state)
    epoch_orders = tuple(tuple(range(len(CLASS_NAMES))) for _ in range(5))
    order_hashes = tuple(diagnostic.sample_order_sha256(order) for order in epoch_orders)
    class_counts = {name: 1 for name in CLASS_NAMES}
    class_weights = {name: float(index + 1) for index, name in enumerate(CLASS_NAMES)}
    train_dataset = _SyntheticDataset("train")
    validation_dataset = _SyntheticDataset("validation")
    observations = {}

    def build_model(config, root):
        model = _SyntheticModel()
        observations.setdefault(config["diagnostic_overrides"]["arm"], {
            "model_hashes": [],
            "training_weights": [],
            "training_bn_modes": [],
            "validation_bn_modes": [],
            "augmentation_seed_sequences": [],
        })
        return model, {}

    def run_epoch_stub(model, loader, device, config, *, optimizer=None, scaler=None,
                       class_weights=None, include_predictions=False):
        arm_key = config["diagnostic_overrides"]["arm"]
        record = observations[arm_key]
        training = optimizer is not None
        configure_batchnorm_mode(model, training, config["batchnorm_policy"])
        if training:
            synthetic_loader_dataset = loader.dataset
            record["augmentation_seed_sequences"].append(tuple(
                derive_augmentation_seed(
                    synthetic_loader_dataset.augmentation_seed,
                    synthetic_loader_dataset.epoch,
                    sample_index,
                )
                for sample_index in range(3)
            ))
            record["model_hashes"].append(
                diagnostic.model_state_sha256(model.state_dict())
            )
            record["training_weights"].append(
                None if class_weights is None else class_weights.detach().cpu().tolist()
            )
            record["training_bn_modes"].append(model.bn.training)
            assert model.bn.weight.requires_grad and model.bn.bias.requires_grad
        else:
            record["validation_bn_modes"].append(model.bn.training)
            assert class_weights is None
        return _synthetic_epoch_report(include_predictions)

    for arm in diagnostic.ARM_DEFINITIONS:
        arm_name = arm[0]
        arm_dir = experiment_dir / arm_name
        arm_dir.mkdir()
        diagnostic.update_status(
            arm_dir / "status.json", "created", 0, 5, progress_name="completed_epochs"
        )
        arm_config = diagnostic._arm_configuration(
            {
                "seed": 42,
                "batch_size": len(CLASS_NAMES),
                "learning_rate": 0.001,
                "mixed_precision": "cuda_if_available",
            },
            arm,
        )
        diagnostic._run_arm(
            arm=arm,
            arm_dir=arm_dir,
            arm_config=arm_config,
            arm_config_sha256="a" * 64,
            root=tmp_path,
            train_dataset=train_dataset,
            validation_dataset=validation_dataset,
            initial_state_path=initial_state_path,
            initial_state_sha256=initial_hash,
            epoch_orders=epoch_orders,
            order_hashes=order_hashes,
            class_counts=class_counts,
            class_weights_by_name=class_weights,
            sample_weighted_mean=diagnostic.training_sample_weighted_mean(
                class_counts, class_weights
            ),
            split_sha256="b" * 64,
            preprocess_sha256="c" * 64,
            runtime={"synthetic": True},
            device=torch.device("cpu"),
            build_model=build_model,
            run_epoch=run_epoch_stub,
            seed_all=lambda seed: None,
        )

        assert json.loads((arm_dir / "status.json").read_text())["status"] == "completed"
        expected_files = {
            "class_weights.json",
            "history.csv",
            "provenance.json",
            "sample_order_hashes.csv",
            "batchnorm_epoch_00_initial.json",
        }
        for epoch in range(1, 6):
            expected_files.update({
                f"epoch_{epoch:02d}_manifest.json",
                f"epoch_{epoch:02d}_train_metrics.json",
                f"epoch_{epoch:02d}_validation_metrics.json",
                f"epoch_{epoch:02d}_validation_predictions.csv",
                f"epoch_{epoch:02d}_validation_confusion_matrix.csv",
                f"epoch_{epoch:02d}_predicted_class_distribution.json",
                f"batchnorm_epoch_{epoch:02d}.json",
            })
        expected_files.add("last_checkpoint.json")
        assert expected_files <= {path.name for path in arm_dir.iterdir()}
        assert len(list(arm_dir.glob("rolling_checkpoint_epoch_*.pt"))) == 1
        checkpoint_pointer = json.loads(
            (arm_dir / "last_checkpoint.json").read_text(encoding="utf-8")
        )
        assert checkpoint_pointer["completed_epochs"] == 5
        with (arm_dir / "history.csv").open(newline="", encoding="utf-8") as handle:
            assert len(list(csv.DictReader(handle))) == 5
        class_weight_report = json.loads((arm_dir / "class_weights.json").read_text())
        assert class_weight_report["training_sample_weighted_mean_of_class_weights"] == pytest.approx(
            diagnostic.training_sample_weighted_mean(class_counts, class_weights)
        )
        provenance = json.loads((arm_dir / "provenance.json").read_text())
        assert provenance["diagnostic_overrides"]["learning_rate"] == 0.0001
        assert provenance["diagnostic_overrides"]["mixed_precision"] == "off"
        assert provenance["diagnostic_overrides"]["grad_scaler_enabled"] is False

    for arm in diagnostic.ARM_DEFINITIONS:
        arm_letter = arm[1]
        record = observations[arm_letter]
        assert len(record["model_hashes"]) == 5
        assert set(record["model_hashes"]) == {initial_hash}
        assert len(record["validation_bn_modes"]) == 5
        assert not any(record["validation_bn_modes"])
        if arm_letter == "B":
            assert all(record["training_bn_modes"])
        else:
            assert not any(record["training_bn_modes"])
        if arm_letter == "C":
            assert all(weights == [class_weights[name] for name in CLASS_NAMES]
                       for weights in record["training_weights"])
        else:
            assert all(weights is None for weights in record["training_weights"])
    augmentation_sequences = {
        tuple(record["augmentation_seed_sequences"])
        for record in observations.values()
    }
    assert len(augmentation_sequences) == 1
    shared_sequences = next(iter(augmentation_sequences))
    assert shared_sequences[0][0] != shared_sequences[0][1]
    assert shared_sequences[0][0] != shared_sequences[1][0]
    assert scaler_enabled == [False, False, False]


def test_all_arms_produce_identical_synthetic_augmentation_per_epoch_sample(
    tmp_path, monkeypatch
):
    split_csv = tmp_path / "synthetic_split.csv"
    with split_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=("image_path", "class_name", "class_index", "split")
        )
        writer.writeheader()
        writer.writerow({
            "image_path": "synthetic/train_sample.jpg",
            "class_name": CLASS_NAMES[0],
            "class_index": "0",
            "split": "train",
        })

    def synthetic_image_tensor(path, config, *, train=False, generator=None):
        source = torch.arange(3 * 5 * 7, dtype=torch.float32).reshape(3, 5, 7)
        return apply_training_augmentations(source, generator=generator) if train else source

    monkeypatch.setattr(dataset_module, "image_tensor", synthetic_image_tensor)
    arm_datasets = {
        arm[1]: NineClassDataset(
            tmp_path, split_csv, "train", PreprocessConfig(image_size=4),
            augmentation_seed=42,
        )
        for arm in diagnostic.ARM_DEFINITIONS
    }

    for epoch in range(diagnostic.DIAGNOSTIC_EPOCHS):
        augmented_by_arm = {}
        for arm_letter, dataset in arm_datasets.items():
            dataset.set_epoch(epoch)
            first = dataset[0][0]
            repeated = dataset[0][0]
            assert torch.equal(first, repeated)
            augmented_by_arm[arm_letter] = first
        reference = augmented_by_arm["A"]
        assert all(torch.equal(reference, value) for value in augmented_by_arm.values())


@pytest.mark.parametrize(
    ("policy", "updates_running_stats"),
    [
        ("freeze_running_stats", False),
        ("train_running_stats", True),
    ],
)
def test_batchnorm_policy_changes_running_stats_without_freezing_affine_parameters(
    policy, updates_running_stats
):
    batchnorm = torch.nn.BatchNorm1d(2)
    initial_mean = batchnorm.running_mean.clone()
    initial_variance = batchnorm.running_var.clone()
    initial_batches = batchnorm.num_batches_tracked.clone()
    inputs = torch.tensor([[0.0, 2.0], [2.0, 6.0], [4.0, 10.0]])

    configure_batchnorm_mode(batchnorm, training=True, policy=policy)
    output = batchnorm(inputs)
    output.square().sum().backward()

    assert batchnorm.weight.requires_grad and batchnorm.weight.grad is not None
    assert batchnorm.bias.requires_grad and batchnorm.bias.grad is not None
    if updates_running_stats:
        assert not torch.equal(batchnorm.running_mean, initial_mean)
        assert not torch.equal(batchnorm.running_var, initial_variance)
        assert int(batchnorm.num_batches_tracked) == int(initial_batches) + 1
    else:
        assert torch.equal(batchnorm.running_mean, initial_mean)
        assert torch.equal(batchnorm.running_var, initial_variance)
        assert torch.equal(batchnorm.num_batches_tracked, initial_batches)
