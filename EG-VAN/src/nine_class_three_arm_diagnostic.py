"""Isolated five-epoch, validation-only EG-VAN diagnostic experiment."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import platform
import struct
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Iterable, Mapping, Sequence
from uuid import uuid4

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Sampler

from nine_class_dataset import (
    NineClassDataset,
    PreprocessConfig,
    preprocessing_for_training,
    preprocessing_hash,
)
from nine_class_stage4 import CLASS_NAMES, ROOT

RESEARCH_STATUS = "EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION"
COHORT_STATUS = "NOT_APPROVED"
DIAGNOSTIC_EPOCHS = 5
BASE_LEARNING_RATE = 0.001
DIAGNOSTIC_LEARNING_RATE = 0.0001
BASE_MIXED_PRECISION = "cuda_if_available"
DIAGNOSTIC_MIXED_PRECISION = "off"
ALLOWED_IMAGE_PARTITIONS = frozenset(("train", "validation"))
ARM_DEFINITIONS = (
    ("arm_A_reference", "A", "freeze_running_stats", False),
    ("arm_B_bn_update", "B", "train_running_stats", False),
    ("arm_C_class_weighting", "C", "freeze_running_stats", True),
)
STATE_HASH_ALGORITHM = "sha256-egvan-tensor-state-v1-little-endian"


class FixedOrderSampler(Sampler[int]):
    def __init__(self, indices: Sequence[int]) -> None:
        self.indices = tuple(int(index) for index in indices)

    def __iter__(self):
        return iter(self.indices)

    def __len__(self) -> int:
        return len(self.indices)


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _write_json(path: Path, value: object, *, replace: bool = False) -> None:
    if path.exists() and not replace:
        raise FileExistsError(path)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
    *,
    replace: bool = False,
) -> None:
    if path.exists() and not replace:
        raise FileExistsError(path)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_torch_save(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        torch.save(value, temporary)
        with temporary.open("r+b") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _process_is_alive(pid: int) -> bool:
    if pid < 1:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as error:
        if os.name == "nt" and getattr(error, "winerror", None) == 87:
            return False
        raise
    return True


class ExperimentLock:
    def __init__(self, experiment_dir: Path) -> None:
        self.path = experiment_dir / ".diagnostic.lock"
        self.token = uuid4().hex
        self.acquired = False

    def _owner_record(self) -> dict:
        return {
            "token": self.token,
            "pid": os.getpid(),
            "host": platform.node(),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    def _create(self) -> None:
        descriptor = os.open(
            self.path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        try:
            payload = canonical_json_bytes(self._owner_record())
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            self.path.unlink(missing_ok=True)
            raise
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        self.acquired = True

    def acquire(self, *, resume: bool = False, confirm_stale: bool = False) -> None:
        try:
            self._create()
            return
        except FileExistsError:
            if not resume:
                raise RuntimeError("Diagnostic experiment is already locked")

        try:
            previous = json.loads(self.path.read_text(encoding="utf-8"))
            previous_token = previous["token"]
            previous_pid = int(previous["pid"])
            previous_host = str(previous["host"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise RuntimeError("Existing diagnostic lock is unreadable; inspect it manually") from error

        if previous_host == platform.node() and _process_is_alive(previous_pid):
            raise RuntimeError("Diagnostic experiment has an active owner")
        if not confirm_stale:
            raise RuntimeError(
                "Diagnostic lock may be stale; explicit stale-lock confirmation is required"
            )

        recovery_path = self.path.with_name(self.path.name + ".recovery")
        try:
            descriptor = os.open(
                recovery_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as error:
            raise RuntimeError("Another process is recovering the diagnostic lock") from error
        try:
            os.close(descriptor)
            current = json.loads(self.path.read_text(encoding="utf-8"))
            if current.get("token") != previous_token:
                raise RuntimeError("Diagnostic lock owner changed during recovery")
            if (
                current.get("host") == platform.node()
                and _process_is_alive(int(current.get("pid", -1)))
            ):
                raise RuntimeError("Diagnostic experiment became active during lock recovery")
            self.path.unlink()
            self._create()
        finally:
            recovery_path.unlink(missing_ok=True)

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            owner = json.loads(self.path.read_text(encoding="utf-8"))
            if owner.get("token") == self.token:
                self.path.unlink()
        finally:
            self.acquired = False


def model_state_sha256(state: Mapping[str, torch.Tensor]) -> str:
    """Hash sorted tensor metadata and canonical little-endian contiguous bytes."""
    digest = hashlib.sha256()
    digest.update((STATE_HASH_ALGORITHM + "\0").encode("ascii"))
    for name in sorted(state):
        tensor = state[name]
        if not isinstance(name, str) or not isinstance(tensor, torch.Tensor):
            raise TypeError("Model state must map string names to tensors")
        cpu_tensor = tensor.detach().to(device="cpu").contiguous()
        metadata = canonical_json_bytes({
            "name": name,
            "shape": list(cpu_tensor.shape),
            "dtype": str(cpu_tensor.dtype),
            "element_size": cpu_tensor.element_size(),
        })
        raw = cpu_tensor.reshape(-1).view(torch.uint8).numpy().tobytes()
        if sys.byteorder == "big" and cpu_tensor.element_size() > 1:
            byte_rows = np.frombuffer(raw, dtype=np.uint8).reshape(-1, cpu_tensor.element_size())
            raw = byte_rows[:, ::-1].copy().tobytes()
        digest.update(struct.pack("<Q", len(metadata)))
        digest.update(metadata)
        digest.update(struct.pack("<Q", len(raw)))
        digest.update(raw)
    return digest.hexdigest()


def load_shared_initial_state(path: Path, expected_sha256: str) -> dict[str, torch.Tensor]:
    state = torch.load(path, map_location="cpu", weights_only=True)
    if (
        not isinstance(state, dict)
        or state.get("format_version") != 1
        or state.get("hash_algorithm") != STATE_HASH_ALGORITHM
    ):
        raise ValueError("Invalid shared initialization artifact")
    model_state = state.get("model_state")
    if not isinstance(model_state, dict):
        raise ValueError("Shared initialization artifact has no model_state")
    actual_sha256 = model_state_sha256(model_state)
    if actual_sha256 != expected_sha256 or state.get("model_state_sha256") != expected_sha256:
        raise ValueError("Shared initialization state hash mismatch")
    return model_state


def _checkpoint_pointer_path(arm_dir: Path) -> Path:
    return arm_dir / "last_checkpoint.json"


def _validate_arm_checkpoint(
    payload: object,
    *,
    arm_name: str,
    initial_state_sha256: str,
    arm_config_sha256: str,
    split_sha256: str,
    preprocess_sha256: str,
    order_hashes: Sequence[str],
) -> dict:
    if not isinstance(payload, dict) or payload.get("format_version") != 2:
        raise ValueError("Invalid rolling checkpoint format")
    completed_epochs = payload.get("completed_epochs")
    if (
        isinstance(completed_epochs, bool)
        or not isinstance(completed_epochs, int)
        or not 1 <= completed_epochs <= DIAGNOSTIC_EPOCHS
    ):
        raise ValueError("Invalid rolling checkpoint epoch")
    expected = {
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "arm": arm_name,
        "initial_model_state_sha256": initial_state_sha256,
        "configuration_sha256": arm_config_sha256,
        "split_sha256": split_sha256,
        "preprocessing_fingerprint": preprocess_sha256,
        "sample_order_sha256": order_hashes[completed_epochs - 1],
        "scheduler_state": None,
    }
    if any(payload.get(name) != value for name, value in expected.items()):
        raise ValueError("Rolling checkpoint provenance mismatch")
    if not isinstance(payload.get("model_state"), dict):
        raise ValueError("Rolling checkpoint has no model state")
    if not isinstance(payload.get("optimizer_state"), dict):
        raise ValueError("Rolling checkpoint has no optimizer state")
    if not isinstance(payload.get("scaler_state"), dict):
        raise ValueError("Rolling checkpoint has no GradScaler state")
    actual_state_hash = model_state_sha256(payload["model_state"])
    if payload.get("model_state_sha256") != actual_state_hash:
        raise ValueError("Rolling checkpoint model-state hash mismatch")
    manifest_hash = payload.get("epoch_manifest_sha256")
    if not isinstance(manifest_hash, str) or len(manifest_hash) != 64:
        raise ValueError("Rolling checkpoint has no epoch manifest hash")
    return payload


def _load_rolling_checkpoint(
    arm_dir: Path,
    *,
    arm_name: str,
    initial_state_sha256: str,
    arm_config_sha256: str,
    split_sha256: str,
    preprocess_sha256: str,
    order_hashes: Sequence[str],
) -> tuple[dict | None, str | None]:
    pointer_path = _checkpoint_pointer_path(arm_dir)
    if not pointer_path.is_file():
        return None, None
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    if not isinstance(pointer, dict):
        raise ValueError("Invalid rolling checkpoint pointer")
    filename = pointer.get("filename")
    if (
        not isinstance(filename, str)
        or Path(filename).name != filename
        or PureWindowsPath(filename).name != filename
    ):
        raise ValueError("Unsafe rolling checkpoint pointer")
    checkpoint_path = arm_dir / filename
    if checkpoint_path.resolve().parent != arm_dir.resolve():
        raise ValueError("Rolling checkpoint escaped its arm directory")
    expected_sha256 = pointer.get("sha256")
    if not isinstance(expected_sha256, str) or _sha256_file(checkpoint_path) != expected_sha256:
        raise ValueError("Rolling checkpoint file hash mismatch")
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    _validate_arm_checkpoint(
        payload,
        arm_name=arm_name,
        initial_state_sha256=initial_state_sha256,
        arm_config_sha256=arm_config_sha256,
        split_sha256=split_sha256,
        preprocess_sha256=preprocess_sha256,
        order_hashes=order_hashes,
    )
    if pointer.get("completed_epochs") != payload["completed_epochs"]:
        raise ValueError("Rolling checkpoint pointer epoch mismatch")
    if pointer.get("model_state_sha256") != payload["model_state_sha256"]:
        raise ValueError("Rolling checkpoint pointer state hash mismatch")
    manifest_path = arm_dir / f"epoch_{payload['completed_epochs']:02d}_manifest.json"
    if _sha256_file(manifest_path) != payload["epoch_manifest_sha256"]:
        raise ValueError("Rolling checkpoint epoch manifest hash mismatch")
    return payload, expected_sha256


def _save_rolling_checkpoint(
    arm_dir: Path,
    payload: dict,
    *,
    arm_name: str,
    initial_state_sha256: str,
    arm_config_sha256: str,
    split_sha256: str,
    preprocess_sha256: str,
    order_hashes: Sequence[str],
) -> dict:
    old_pointer_path = _checkpoint_pointer_path(arm_dir)
    old_pointer = (
        json.loads(old_pointer_path.read_text(encoding="utf-8"))
        if old_pointer_path.is_file()
        else None
    )
    _validate_arm_checkpoint(
        payload,
        arm_name=arm_name,
        initial_state_sha256=initial_state_sha256,
        arm_config_sha256=arm_config_sha256,
        split_sha256=split_sha256,
        preprocess_sha256=preprocess_sha256,
        order_hashes=order_hashes,
    )
    expected_epoch = 1
    if old_pointer is not None:
        previous_payload, _ = _load_rolling_checkpoint(
            arm_dir,
            arm_name=arm_name,
            initial_state_sha256=initial_state_sha256,
            arm_config_sha256=arm_config_sha256,
            split_sha256=split_sha256,
            preprocess_sha256=preprocess_sha256,
            order_hashes=order_hashes,
        )
        if previous_payload is None:
            raise ValueError("Existing rolling checkpoint pointer has no checkpoint")
        expected_epoch = int(previous_payload["completed_epochs"]) + 1
        del previous_payload
    if payload["completed_epochs"] != expected_epoch:
        raise ValueError("Rolling checkpoint must advance by exactly one epoch")
    temporary = arm_dir / f".rolling_checkpoint.{uuid4().hex}.tmp"
    try:
        torch.save(payload, temporary)
        with temporary.open("r+b") as handle:
            os.fsync(handle.fileno())
        # Deserialize and verify before changing the pointer to the prior checkpoint.
        staged = torch.load(temporary, map_location="cpu", weights_only=True)
        _validate_arm_checkpoint(
            staged,
            arm_name=arm_name,
            initial_state_sha256=initial_state_sha256,
            arm_config_sha256=arm_config_sha256,
            split_sha256=split_sha256,
            preprocess_sha256=preprocess_sha256,
            order_hashes=order_hashes,
        )
        del staged
        checkpoint_sha256 = _sha256_file(temporary)
        filename = (
            f"rolling_checkpoint_epoch_{payload['completed_epochs']:02d}_"
            f"{uuid4().hex}.pt"
        )
        checkpoint_path = arm_dir / filename
        os.replace(temporary, checkpoint_path)
        if _sha256_file(checkpoint_path) != checkpoint_sha256:
            raise ValueError("Committed rolling checkpoint hash mismatch")
        pointer = {
            "format_version": 1,
            "filename": filename,
            "sha256": checkpoint_sha256,
            "completed_epochs": payload["completed_epochs"],
            "model_state_sha256": payload["model_state_sha256"],
        }
        _write_json(old_pointer_path, pointer, replace=old_pointer is not None)
        persisted_pointer = json.loads(old_pointer_path.read_text(encoding="utf-8"))
        if persisted_pointer != pointer:
            raise ValueError("Committed rolling checkpoint pointer verification failed")
        if old_pointer is not None:
            previous_filename = old_pointer.get("filename")
            if isinstance(previous_filename, str) and Path(previous_filename).name == previous_filename:
                previous_path = arm_dir / previous_filename
                if previous_path != checkpoint_path and previous_path.is_file():
                    previous_path.unlink()
        for orphan in arm_dir.glob("rolling_checkpoint_epoch_*.pt"):
            if orphan != checkpoint_path and (
                old_pointer is None or orphan.name != old_pointer.get("filename")
            ):
                if orphan.is_file():
                    orphan.unlink()
        return pointer
    finally:
        if temporary.exists():
            temporary.unlink()


def _epoch_artifact_names(epoch: int) -> tuple[str, ...]:
    return (
        f"epoch_{epoch:02d}_train_metrics.json",
        f"epoch_{epoch:02d}_validation_metrics.json",
        f"epoch_{epoch:02d}_validation_predictions.csv",
        f"epoch_{epoch:02d}_validation_confusion_matrix.csv",
        f"epoch_{epoch:02d}_predicted_class_distribution.json",
        f"batchnorm_epoch_{epoch:02d}.json",
    )


def _write_epoch_manifest(
    arm_dir: Path,
    epoch: int,
    *,
    arm_name: str,
    initial_state_sha256: str,
    arm_config_sha256: str,
    split_sha256: str,
    preprocess_sha256: str,
    sample_order_sha256: str,
    model_state_sha256_value: str,
) -> str:
    names = _epoch_artifact_names(epoch)
    if any(not (arm_dir / name).is_file() for name in names):
        raise FileNotFoundError("Cannot commit an epoch with missing metric artifacts")
    manifest = {
        "format_version": 1,
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "arm": arm_name,
        "epoch": epoch,
        "initial_model_state_sha256": initial_state_sha256,
        "configuration_sha256": arm_config_sha256,
        "split_sha256": split_sha256,
        "preprocessing_fingerprint": preprocess_sha256,
        "sample_order_sha256": sample_order_sha256,
        "model_state_sha256": model_state_sha256_value,
        "artifacts": {name: _sha256_file(arm_dir / name) for name in names},
    }
    path = arm_dir / f"epoch_{epoch:02d}_manifest.json"
    _write_json(path, manifest)
    return _sha256_file(path)


def _verify_epoch_records(
    arm_dir: Path,
    completed_epochs: int,
    *,
    arm_name: str,
    initial_state_sha256: str,
    arm_config_sha256: str,
    split_sha256: str,
    preprocess_sha256: str,
    order_hashes: Sequence[str],
) -> None:
    for epoch in range(1, completed_epochs + 1):
        path = arm_dir / f"epoch_{epoch:02d}_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        expected = {
            "format_version": 1,
            "research_status": RESEARCH_STATUS,
            "cohort_status": COHORT_STATUS,
            "arm": arm_name,
            "epoch": epoch,
            "initial_model_state_sha256": initial_state_sha256,
            "configuration_sha256": arm_config_sha256,
            "split_sha256": split_sha256,
            "preprocessing_fingerprint": preprocess_sha256,
            "sample_order_sha256": order_hashes[epoch - 1],
        }
        if any(manifest.get(name) != value for name, value in expected.items()):
            raise ValueError(f"Epoch {epoch} artifact provenance mismatch")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict) or set(artifacts) != set(_epoch_artifact_names(epoch)):
            raise ValueError(f"Epoch {epoch} artifact manifest is incomplete")
        for name, digest in artifacts.items():
            artifact_path = arm_dir / name
            if not artifact_path.is_file() or _sha256_file(artifact_path) != digest:
                raise ValueError(f"Epoch {epoch} artifact hash mismatch: {name}")


def _remove_uncommitted_epoch(arm_dir: Path, epoch: int) -> None:
    names = (*_epoch_artifact_names(epoch), f"epoch_{epoch:02d}_manifest.json")
    for name in names:
        target = arm_dir / name
        if target.is_file():
            target.unlink()
        for temporary in arm_dir.glob(f".{name}.*.tmp"):
            if temporary.is_file():
                temporary.unlink()


def _rebuild_history(arm_dir: Path, completed_epochs: int) -> None:
    rows = []
    for epoch in range(1, completed_epochs + 1):
        train = json.loads(
            (arm_dir / f"epoch_{epoch:02d}_train_metrics.json").read_text(encoding="utf-8")
        )
        validation = json.loads(
            (arm_dir / f"epoch_{epoch:02d}_validation_metrics.json").read_text(encoding="utf-8")
        )
        rows.append({
            "research_status": RESEARCH_STATUS,
            "cohort_status": COHORT_STATUS,
            "epoch": epoch,
            "train_loss": train["loss"],
            "train_loss_kind": train["loss_kind"],
            "train_accuracy": train["accuracy"],
            "train_macro_f1": train["macro_f1"],
            "validation_loss": validation["loss"],
            "validation_accuracy": validation["accuracy"],
            "validation_macro_f1": validation["macro_f1"],
            "validation_weighted_f1": validation["weighted_f1"],
            "validation_balanced_accuracy": validation["balanced_accuracy"],
        })
    fields = (
        "research_status", "cohort_status", "epoch", "train_loss", "train_loss_kind",
        "train_accuracy", "train_macro_f1", "validation_loss", "validation_accuracy",
        "validation_macro_f1", "validation_weighted_f1", "validation_balanced_accuracy",
    )
    _write_csv(arm_dir / "history.csv", fields, rows, replace=True)


def inverse_sqrt_class_weights(
    train_rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, int], dict[str, float]]:
    counts = {name: 0 for name in CLASS_NAMES}
    for row in train_rows:
        if row.get("split") != "train":
            raise ValueError("Class weights may be computed from training rows only")
        name = row.get("class_name")
        if name not in counts:
            raise ValueError(f"Unknown training class: {name}")
        counts[name] += 1
    if any(counts[name] == 0 for name in CLASS_NAMES):
        raise ValueError("Inverse-square-root weights require examples in all nine classes")
    raw = {name: 1.0 / math.sqrt(counts[name]) for name in CLASS_NAMES}
    mean_raw = sum(raw.values()) / len(CLASS_NAMES)
    weights = {name: raw[name] / mean_raw for name in CLASS_NAMES}
    return counts, weights


def epoch_sample_order(sample_count: int, base_seed: int, epoch: int) -> tuple[int, ...]:
    if sample_count < 1 or base_seed < 0 or epoch < 0:
        raise ValueError("Sample count must be positive and seed/epoch nonnegative")
    generator = torch.Generator(device="cpu").manual_seed(base_seed + epoch)
    return tuple(torch.randperm(sample_count, generator=generator).tolist())


def sample_order_sha256(indices: Sequence[int]) -> str:
    digest = hashlib.sha256()
    digest.update(b"egvan-sample-order-v1\0")
    digest.update(struct.pack("<Q", len(indices)))
    for index in indices:
        if isinstance(index, bool) or not isinstance(index, (int, np.integer)) or int(index) < 0:
            raise ValueError("Sample indices must be nonnegative integers")
        digest.update(struct.pack("<Q", int(index)))
    return digest.hexdigest()


def construct_diagnostic_dataset(
    root: Path,
    split_csv: Path,
    split: str,
    preprocess: PreprocessConfig,
    base_seed: int,
) -> NineClassDataset:
    if split not in ALLOWED_IMAGE_PARTITIONS:
        raise ValueError("Diagnostic runner permits only train and validation datasets")
    return NineClassDataset(
        root,
        split_csv,
        split,
        preprocess,
        augmentation_seed=base_seed if split == "train" else None,
    )


def protected_output_roots(project_root: Path = ROOT) -> tuple[Path, ...]:
    from nine_class_exploratory import (
        CONFIG as EXPLORATORY_CONFIG,
        OUT as EXPLORATORY_OUT,
        PREVIEW,
        REPORT,
        RUNS_ROOT as EXPLORATORY_RUNS_ROOT,
        SIIM_DECISIONS,
    )
    from nine_class_stage4 import (
        DATA_RAW_RELATIVE,
        ISIC_DATA_RELATIVE,
        OUT as STAGE4_OUT,
        OVERLAP_COMPLETION_RELATIVE,
        RECOVERY_STAGE3I_RELATIVE,
        VALIDATION_DIAGNOSTICS_ROOT,
    )
    from nine_class_training import (
        DEFAULT_CONFIG,
        DEFAULT_INVENTORY,
        DEFAULT_RUNS_ROOT,
    )
    project_root = project_root.resolve()
    source_root = ROOT.resolve()

    def rebase(path: Path) -> Path:
        try:
            relative = path.resolve().relative_to(source_root)
        except ValueError as error:
            raise RuntimeError(f"Protected path is outside the project root: {path}") from error
        return (project_root / relative).resolve()

    paths = (
        project_root / "data",
        project_root / DATA_RAW_RELATIVE,
        project_root / ISIC_DATA_RELATIVE,
        rebase(EXPLORATORY_OUT),
        rebase(EXPLORATORY_RUNS_ROOT),
        rebase(DEFAULT_RUNS_ROOT.parent),
        rebase(VALIDATION_DIAGNOSTICS_ROOT),
        rebase(STAGE4_OUT),
        rebase(PREVIEW.parent),
        rebase(REPORT.parent),
        rebase(SIIM_DECISIONS.parent),
        rebase(EXPLORATORY_CONFIG.parent),
        rebase(DEFAULT_CONFIG.parent),
        rebase(DEFAULT_INVENTORY.parent),
        project_root / OVERLAP_COMPLETION_RELATIVE,
        project_root / RECOVERY_STAGE3I_RELATIVE,
        project_root / "checkpoints",
        project_root / "src",
        project_root / "tests",
        project_root / "notebooks",
    )
    analysis_root = project_root / "analysis"
    if analysis_root.is_dir():
        paths += tuple(
            child
            for child in analysis_root.iterdir()
            if child.is_dir() and child.name != "nine_class_three_arm_diagnostics"
        )
    return tuple(sorted({path.resolve() for path in paths}, key=lambda path: str(path).casefold()))


def _validate_base_configuration(base_config: dict) -> None:
    if tuple(base_config["label_order"]) != CLASS_NAMES:
        raise ValueError("Nine-class order mismatch")
    if (
        int(base_config["batch_size"]) != 8
        or int(base_config["gradient_accumulation_steps"]) != 4
        or base_config["optimizer"] != "Adamax"
        or not math.isclose(float(base_config["learning_rate"]), BASE_LEARNING_RATE)
        or base_config["mixed_precision"] != BASE_MIXED_PRECISION
        or int(base_config["num_workers"]) != 0
        or int(base_config["epochs"]) != 25
        or base_config["batchnorm_policy"] != "freeze_running_stats"
        or base_config["class_weighting"] is not False
        or not math.isclose(float(base_config["focal_alpha"]), 0.25)
        or not math.isclose(float(base_config["focal_gamma"]), 2.0)
        or base_config["initialization"]["mode"] != "random"
    ):
        raise ValueError("Base configuration differs from the diagnostic protocol")


def preflight_diagnostic(root: Path = ROOT) -> dict:
    from nine_class_exploratory import CONFIG, SPLIT, validate_frozen
    from nine_class_training import load_config

    root = root.resolve()
    rows, frozen = validate_frozen(
        root,
        verify_bytes=True,
        image_partitions=ALLOWED_IMAGE_PARTITIONS,
    )
    if frozen.get("status") != RESEARCH_STATUS or not all(
        row.get("approval_status") == COHORT_STATUS for row in rows
    ):
        raise ValueError("Exploratory cohort status or frozen provenance mismatch")

    base_config = load_config(CONFIG)
    _validate_base_configuration(base_config)
    preprocess = preprocessing_for_training(base_config)
    preprocess_sha256 = preprocessing_hash(preprocess)
    train_dataset, validation_dataset = _create_datasets(
        root, SPLIT, preprocess, int(base_config["seed"])
    )
    class_counts, class_weights = inverse_sqrt_class_weights(train_dataset.rows)
    decoded_counts = {}
    for dataset in (train_dataset, validation_dataset):
        first_by_class = {}
        for index, row in enumerate(dataset.rows):
            first_by_class.setdefault(row["class_name"], index)
        if set(first_by_class) != set(CLASS_NAMES):
            raise ValueError(f"{dataset.split} does not contain every diagnostic class")
        for name, index in first_by_class.items():
            image, target = dataset[index]
            if (
                image.shape != (3, int(base_config["image_size"]), int(base_config["image_size"]))
                or not torch.isfinite(image).all()
                or target != CLASS_NAMES.index(name)
            ):
                raise ValueError(f"{dataset.split} image or label preflight failed: {name}")
        decoded_counts[dataset.split] = len(first_by_class)

    return {
        "status": "PREFLIGHT_PASSED",
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "checked_image_partitions": sorted(ALLOWED_IMAGE_PARTITIONS),
        "class_order": list(CLASS_NAMES),
        "split_sha256": frozen["split_sha256"],
        "configuration_sha256": frozen["config_sha256"],
        "preprocessing_fingerprint": preprocess_sha256,
        "base_configuration": {
            "learning_rate": BASE_LEARNING_RATE,
            "mixed_precision": BASE_MIXED_PRECISION,
        },
        "diagnostic_overrides": _diagnostic_override_record(base_config),
        "train_samples": len(train_dataset),
        "validation_samples": len(validation_dataset),
        "decoded_examples_by_class": decoded_counts,
        "training_class_counts": class_counts,
        "training_class_weights": class_weights,
    }


def create_experiment_directory(runs_root: Path, experiment_id: str | None = None) -> Path:
    if experiment_id is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        experiment_id = f"EXPLORATORY_ONLY_THREE_ARM_{stamp}_{uuid4().hex[:8]}"
    if not experiment_id or experiment_id in {".", ".."} or Path(experiment_id).name != experiment_id:
        raise ValueError("Experiment id must be a single path component")
    runs_root.mkdir(parents=True, exist_ok=True)
    resolved_runs_root = runs_root.resolve()
    experiment_dir = runs_root / experiment_id
    experiment_dir.mkdir(parents=False, exist_ok=False)
    resolved_experiment_dir = experiment_dir.resolve()
    if resolved_experiment_dir == resolved_runs_root or resolved_runs_root not in resolved_experiment_dir.parents:
        raise ValueError("Experiment directory escaped the diagnostic output root")
    return resolved_experiment_dir


def validate_output_root(
    runs_root: Path,
    protected_roots: Sequence[Path],
    *,
    project_root: Path | None = None,
) -> Path:
    raw_path = str(runs_root)
    if any(
        part == ".."
        for pure_path in (PurePosixPath(raw_path), PureWindowsPath(raw_path))
        for part in pure_path.parts
    ):
        raise ValueError("Output root must not contain parent traversal")
    windows_path = PureWindowsPath(raw_path)
    if windows_path.drive.startswith("\\\\"):
        raise ValueError("Output root must not use a UNC or device path")
    if (windows_path.drive or windows_path.root) and not Path(runs_root).is_absolute():
        raise ValueError("Output root has a non-native drive or root")
    candidate = Path(runs_root)
    resolved_project = project_root.resolve() if project_root is not None else None
    if resolved_project is not None and not candidate.is_absolute():
        candidate = resolved_project / candidate
    resolved_root = candidate.resolve()
    if resolved_project is not None and (
        resolved_root == resolved_project or resolved_project not in resolved_root.parents
    ):
        raise ValueError("Output root must be a child of the project root")
    for protected_root in protected_roots:
        protected = protected_root.resolve()
        if (
            resolved_root == protected
            or resolved_root in protected.parents
            or protected in resolved_root.parents
        ):
            raise ValueError(f"Output root overlaps protected directory: {protected}")
    return resolved_root


_STATUS_TRANSITIONS = {
    "created": {"running", "failed", "interrupted"},
    "running": {"running", "completed", "failed", "interrupted"},
    "completed": set(),
    "failed": set(),
    "interrupted": set(),
}


def update_status(
    path: Path,
    status: str,
    progress: int,
    required_progress: int,
    *,
    progress_name: str,
    error: str | None = None,
    allow_resume: bool = False,
) -> None:
    if (
        status not in _STATUS_TRANSITIONS
        or isinstance(progress, bool)
        or not isinstance(progress, int)
        or progress < 0
        or isinstance(required_progress, bool)
        or not isinstance(required_progress, int)
        or required_progress < 1
    ):
        raise ValueError("Invalid status or progress")
    previous = None
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        old_status = previous["status"]
        if old_status not in _STATUS_TRANSITIONS:
            raise ValueError("Existing status file contains an unknown state")
        previous_required_progress = previous.get("required_progress")
        if (
            isinstance(previous_required_progress, bool)
            or not isinstance(previous_required_progress, int)
            or previous_required_progress != required_progress
        ):
            raise ValueError("Status required progress cannot change")
        resumed_transition = (
            allow_resume and old_status == "interrupted" and status == "running"
        )
        if status not in _STATUS_TRANSITIONS[old_status] and not resumed_transition:
            raise ValueError(f"Invalid status transition: {old_status} -> {status}")
        if progress < int(previous.get(progress_name, 0)):
            raise ValueError("Status progress cannot move backwards")
    elif status != "created":
        raise ValueError("The first persisted status must be created")
    if progress > required_progress:
        raise ValueError("Status progress exceeds the required work")
    if status == "completed" and progress != required_progress:
        raise ValueError("Cannot mark incomplete work completed")
    record = {
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "status": status,
        progress_name: progress,
        "required_progress": required_progress,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if error is not None:
        record["error"] = error
    _write_json(path, record, replace=path.exists())


def _status_progress(path: Path, progress_name: str) -> int:
    if not path.is_file():
        return 0
    return int(json.loads(path.read_text(encoding="utf-8")).get(progress_name, 0))


def _persist_experiment_terminal_status(
    path: Path,
    status: str,
    required_progress: int,
    *,
    progress_name: str,
    error: str,
) -> None:
    progress = _status_progress(path, progress_name)
    if not path.exists():
        update_status(path, "created", 0, required_progress, progress_name=progress_name)
    update_status(
        path,
        status,
        progress,
        required_progress,
        progress_name=progress_name,
        error=error,
    )


def _persist_arm_terminal_status(
    path: Path,
    status: str,
    completed_epochs: int,
    *,
    error: str,
) -> None:
    if status not in {"failed", "interrupted"}:
        raise ValueError("Arm terminal status must be failed or interrupted")
    progress = completed_epochs
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        current_status = existing["status"]
        if current_status not in _STATUS_TRANSITIONS:
            raise ValueError("Existing arm status file contains an unknown state")
        if current_status in {"completed", "failed", "interrupted"}:
            return
        progress = max(progress, int(existing.get("completed_epochs", 0)))
    else:
        update_status(path, "created", 0, DIAGNOSTIC_EPOCHS,
                      progress_name="completed_epochs")
    update_status(
        path,
        status,
        progress,
        DIAGNOSTIC_EPOCHS,
        progress_name="completed_epochs",
        error=error,
    )


def _record_arm_failure_without_masking(
    status_path: Path,
    status: str,
    completed_epochs: int,
    error: BaseException,
) -> None:
    try:
        _persist_arm_terminal_status(
            status_path,
            status,
            completed_epochs,
            error=str(error) or type(error).__name__,
        )
    except BaseException as status_error:
        raise error from status_error


def training_sample_weighted_mean(
    class_counts: Mapping[str, int],
    class_weights: Mapping[str, float],
) -> float:
    if set(class_counts) != set(CLASS_NAMES) or set(class_weights) != set(CLASS_NAMES):
        raise ValueError("Class counts and weights must match the nine-class order")
    total_samples = sum(class_counts.values())
    if total_samples < 1 or any(count < 1 for count in class_counts.values()):
        raise ValueError("Training sample counts must be positive for every class")
    return float(sum(class_counts[name] * class_weights[name] for name in CLASS_NAMES)
                 / total_samples)


def _safe_json_value(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _safe_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json_value(item) for item in value]
    if isinstance(value, np.ndarray):
        return _safe_json_value(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return _safe_json_value(value.detach().cpu().tolist())
    return value


def _enrich_metrics(report: dict, probabilities: np.ndarray | None = None) -> dict:
    matrix = report["confusion_matrix"]
    report["balanced_accuracy"] = float(
        sum(metrics["recall"] for metrics in report["per_class"].values()) / len(CLASS_NAMES)
    )
    report["predicted_class_distribution"] = {
        name: int(sum(matrix[row][column] for row in range(len(CLASS_NAMES))))
        for column, name in enumerate(CLASS_NAMES)
    }
    if probabilities is not None:
        predicted = probabilities.argmax(axis=1)
        observed = Counter(int(index) for index in predicted)
        if any(observed.get(index, 0) != report["predicted_class_distribution"][name]
               for index, name in enumerate(CLASS_NAMES)):
            raise ValueError("Predicted distribution does not match the confusion matrix")
    return report


def _batchnorm_buffers(model: nn.Module) -> dict[str, torch.Tensor]:
    buffers: dict[str, torch.Tensor] = {}
    for module_name, module in model.named_modules():
        if isinstance(module, nn.modules.batchnorm._BatchNorm):
            for buffer_name in ("running_mean", "running_var", "num_batches_tracked"):
                value = getattr(module, buffer_name, None)
                if value is not None:
                    buffers[f"{module_name}.{buffer_name}"] = value.detach().cpu().clone()
    return buffers


def _batchnorm_record(
    model: nn.Module,
    initial_buffers: Mapping[str, torch.Tensor],
    epoch: int,
) -> dict:
    current = _batchnorm_buffers(model)
    if set(current) != set(initial_buffers):
        raise ValueError("BatchNorm buffer structure changed during training")
    layers = {}
    for name in sorted(current):
        value = current[name]
        initial = initial_buffers[name]
        if name.endswith("num_batches_tracked"):
            layers[name] = {"value": int(value.item()), "initial_value": int(initial.item())}
        else:
            layers[name] = {
                "mean": float(value.float().mean().item()),
                "std": float(value.float().std(unbiased=False).item()),
                "max_abs_delta_from_initial": float((value.float() - initial.float()).abs().max().item()),
            }
    return {
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "epoch": epoch,
        "sha256": model_state_sha256(current),
        "layers": layers,
    }


def _runtime_metadata(device: torch.device) -> dict:
    import torchvision

    return {
        "python": platform.python_version(),
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "pytorch": torch.__version__,
        "torchvision": torchvision.__version__,
        "cuda_runtime": torch.version.cuda,
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
        "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
    }


def _record_resume_attempt(experiment_dir: Path, runtime: dict) -> None:
    path = experiment_dir / "resume_attempts.json"
    if path.is_file():
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(record, dict)
            or record.get("research_status") != RESEARCH_STATUS
            or record.get("cohort_status") != COHORT_STATUS
            or not isinstance(record.get("attempts"), list)
        ):
            raise ValueError("Existing resume-attempt provenance is invalid")
        attempts = record["attempts"]
    else:
        attempts = []
    attempts.append({
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "host": platform.node(),
        "runtime_metadata": runtime,
    })
    _write_json(path, {
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "attempts": attempts,
    }, replace=path.exists())


def _diagnostic_override_record(base_config: Mapping[str, object]) -> dict:
    return {
        "base_learning_rate": float(base_config["learning_rate"]),
        "learning_rate": DIAGNOSTIC_LEARNING_RATE,
        "base_mixed_precision": str(base_config["mixed_precision"]),
        "mixed_precision": DIAGNOSTIC_MIXED_PRECISION,
        "grad_scaler_enabled": False,
        "adaptive_scheduler": False,
    }


def _arm_configuration(base_config: dict, arm: tuple[str, str, str, bool]) -> dict:
    directory, arm_name, batchnorm_policy, weighted = arm
    config = copy.deepcopy(base_config)
    config["epochs"] = DIAGNOSTIC_EPOCHS
    config["learning_rate"] = DIAGNOSTIC_LEARNING_RATE
    config["mixed_precision"] = DIAGNOSTIC_MIXED_PRECISION
    config["batchnorm_policy"] = batchnorm_policy
    config["class_weighting"] = weighted
    config["scheduler"] = {"name": "disabled", "reason": "fixed diagnostic learning rate"}
    config["diagnostic_overrides"] = {
        "arm": arm_name,
        "epochs": DIAGNOSTIC_EPOCHS,
        **_diagnostic_override_record(base_config),
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
    }
    if directory not in {definition[0] for definition in ARM_DEFINITIONS}:
        raise ValueError("Unknown diagnostic arm")
    return config


def _write_initial_state(experiment_dir: Path, state_dict: Mapping[str, torch.Tensor]) -> str:
    digest = model_state_sha256(state_dict)
    cpu_state = {name: value.detach().to(device="cpu").contiguous().clone()
                 for name, value in state_dict.items()}
    _atomic_torch_save(experiment_dir / "initial_model_state.pt", {
        "format_version": 1,
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "hash_algorithm": STATE_HASH_ALGORITHM,
        "model_state_sha256": digest,
        "model_state": cpu_state,
    })
    _write_json(experiment_dir / "initial_model_state.json", {
        "research_status": RESEARCH_STATUS,
        "cohort_status": COHORT_STATUS,
        "hash_algorithm": STATE_HASH_ALGORITHM,
        "model_state_sha256": digest,
        "tensor_count": len(cpu_state),
    })
    return digest


def _validation_prediction_rows(
    dataset: NineClassDataset,
    probabilities: np.ndarray,
    targets: np.ndarray,
    epoch: int,
) -> list[dict[str, object]]:
    if len(dataset.rows) != len(targets) or probabilities.shape != (len(targets), len(CLASS_NAMES)):
        raise ValueError("Validation rows and predictions are not aligned")
    expected_targets = np.asarray([int(row["class_index"]) for row in dataset.rows], dtype=np.int64)
    if not np.array_equal(targets, expected_targets):
        raise ValueError("Sequential validation targets differ from dataset row order")
    records = []
    for sample_index, row in enumerate(dataset.rows):
        target = int(targets[sample_index])
        predicted = int(probabilities[sample_index].argmax())
        record = {
            "research_status": RESEARCH_STATUS,
            "cohort_status": COHORT_STATUS,
            "epoch": epoch,
            "sample_index": sample_index,
            "image_path": row["image_path"],
            "true_class": CLASS_NAMES[target],
            "predicted_class": CLASS_NAMES[predicted],
        }
        record.update({
            f"prob_{name}": float(probabilities[sample_index, class_index])
            for class_index, name in enumerate(CLASS_NAMES)
        })
        records.append(record)
    return records


def _write_confusion_matrix(path: Path, matrix: Sequence[Sequence[int]], epoch: int) -> None:
    if len(matrix) != len(CLASS_NAMES) or any(len(row) != len(CLASS_NAMES) for row in matrix):
        raise ValueError("Expected a nine-by-nine confusion matrix")
    rows = [
        {"research_status": RESEARCH_STATUS, "cohort_status": COHORT_STATUS, "epoch": epoch,
         "true_class": name, **{predicted: int(matrix[row_index][column_index])
                                for column_index, predicted in enumerate(CLASS_NAMES)}}
        for row_index, name in enumerate(CLASS_NAMES)
    ]
    _write_csv(path, ("research_status", "cohort_status", "epoch", "true_class", *CLASS_NAMES),
               rows)


def _append_history(path: Path, row: Mapping[str, object]) -> None:
    fields = (
        "research_status", "cohort_status", "epoch", "train_loss", "train_loss_kind",
        "train_accuracy", "train_macro_f1",
        "validation_loss", "validation_accuracy", "validation_macro_f1",
        "validation_weighted_f1", "validation_balanced_accuracy",
    )
    if not path.exists():
        with path.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
            handle.flush()
            os.fsync(handle.fileno())
        return
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writerow(row)
        handle.flush()
        os.fsync(handle.fileno())


def _create_datasets(
    root: Path,
    split_csv: Path,
    preprocess: PreprocessConfig,
    base_seed: int,
) -> tuple[NineClassDataset, NineClassDataset]:
    train_dataset = construct_diagnostic_dataset(root, split_csv, "train", preprocess, base_seed)
    validation_dataset = construct_diagnostic_dataset(root, split_csv, "validation", preprocess, base_seed)
    if train_dataset.split != "train" or validation_dataset.split != "validation":
        raise RuntimeError("Unexpected dataset split in diagnostic runner")
    return train_dataset, validation_dataset


def _write_or_verify_json(path: Path, value: dict) -> None:
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != _safe_json_value(value):
            raise ValueError(f"Existing diagnostic metadata differs: {path.name}")
        return
    _write_json(path, value)


def _write_or_verify_sample_orders(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
        expected = [{key: str(value) for key, value in row.items()} for row in rows]
        if existing != expected:
            raise ValueError("Existing sample-order provenance differs")
        return
    _write_csv(path, ("research_status", "cohort_status", "epoch", "sample_order_sha256"), rows)


def _run_arm(
    *,
    arm: tuple[str, str, str, bool],
    arm_dir: Path,
    arm_config: dict,
    arm_config_sha256: str,
    root: Path,
    train_dataset: NineClassDataset,
    validation_dataset: NineClassDataset,
    initial_state_path: Path,
    initial_state_sha256: str,
    epoch_orders: Sequence[Sequence[int]],
    order_hashes: Sequence[str],
    class_counts: Mapping[str, int],
    class_weights_by_name: Mapping[str, float],
    sample_weighted_mean: float,
    split_sha256: str,
    preprocess_sha256: str,
    runtime: dict,
    device: torch.device,
    build_model,
    run_epoch,
    seed_all,
    resume: bool = False,
) -> None:
    arm_name, _, batchnorm_policy, weighted = arm
    status_path = arm_dir / "status.json"
    completed_epochs = 0
    try:
        if not status_path.is_file():
            raise FileNotFoundError(f"Arm status is missing: {status_path}")
        status_record = json.loads(status_path.read_text(encoding="utf-8"))
        current_status = status_record.get("status")
        if current_status == "failed":
            raise ValueError("Failed arms cannot be resumed")
        if current_status == "completed" and not resume:
            raise ValueError("Completed arms cannot be run again")
        if not resume and current_status != "created":
            raise ValueError(f"New arm run requires created status, found {current_status}")
        if resume and current_status not in {"created", "running", "interrupted", "completed"}:
            raise ValueError(f"Arm cannot be resumed from status {current_status}")
        status_progress = int(status_record.get("completed_epochs", 0))
        if current_status == "completed" and status_progress != DIAGNOSTIC_EPOCHS:
            raise ValueError("Completed arm status has incomplete progress")
        if current_status != "completed":
            update_status(
                status_path,
                "running",
                status_progress,
                DIAGNOSTIC_EPOCHS,
                progress_name="completed_epochs",
                allow_resume=current_status == "interrupted",
            )

        model, branch_hashes = build_model(arm_config, root)
        shared_state = load_shared_initial_state(initial_state_path, initial_state_sha256)
        model.load_state_dict(shared_state, strict=True)
        loaded_sha256 = model_state_sha256(model.state_dict())
        if loaded_sha256 != initial_state_sha256:
            raise ValueError(f"{arm_name} loaded a different initial state")
        model.to(device)

        optimizer = torch.optim.Adamax(model.parameters(), lr=DIAGNOSTIC_LEARNING_RATE)
        scaler = torch.amp.GradScaler(
            "cuda", enabled=bool(arm_config["diagnostic_overrides"]["grad_scaler_enabled"])
        )
        initial_bn_buffers = _batchnorm_buffers(model)
        class_weights = (
            torch.tensor([class_weights_by_name[name] for name in CLASS_NAMES],
                         dtype=torch.float32, device=device)
            if weighted else None
        )
        _write_or_verify_json(arm_dir / "runtime_metadata.json", runtime)
        _write_or_verify_json(
            arm_dir / "batchnorm_epoch_00_initial.json",
            _batchnorm_record(model, initial_bn_buffers, 0),
        )
        class_weight_record = {
            "research_status": RESEARCH_STATUS,
            "cohort_status": COHORT_STATUS,
            "class_order": list(CLASS_NAMES),
            "counts_from_training_rows_only": dict(class_counts),
            "formula": "(1/sqrt(n_c))/mean_j(1/sqrt(n_j))",
            "enabled_for_training": weighted,
            "weights": dict(class_weights_by_name) if weighted else None,
            "training_sample_weighted_mean_of_class_weights": sample_weighted_mean,
            "effective_training_loss_class_weighted_mean": (
                sample_weighted_mean if weighted else None
            ),
        }
        _write_or_verify_json(arm_dir / "class_weights.json", class_weight_record)
        provenance = {
            "research_status": RESEARCH_STATUS,
            "cohort_status": COHORT_STATUS,
            "arm": arm_name,
            "initial_model_state_sha256": initial_state_sha256,
            "initial_state_hash_algorithm": STATE_HASH_ALGORITHM,
            "configuration_sha256": arm_config_sha256,
            "split_sha256": split_sha256,
            "preprocessing_fingerprint": preprocess_sha256,
            "runtime_metadata": runtime,
            "branch_initialization_hashes": branch_hashes,
            "seed": int(arm_config["seed"]),
            "epochs": DIAGNOSTIC_EPOCHS,
            "diagnostic_overrides": arm_config["diagnostic_overrides"],
            "batchnorm_policy": batchnorm_policy,
            "class_weighting": weighted,
        }
        _write_or_verify_json(arm_dir / "provenance.json", provenance)
        order_rows = [
            {"research_status": RESEARCH_STATUS, "cohort_status": COHORT_STATUS,
             "epoch": epoch + 1, "sample_order_sha256": digest}
            for epoch, digest in enumerate(order_hashes)
        ]
        _write_or_verify_sample_orders(arm_dir / "sample_order_hashes.csv", order_rows)

        checkpoint_payload = None
        start_epoch = 0
        if resume:
            checkpoint_payload, _ = _load_rolling_checkpoint(
                arm_dir,
                arm_name=arm_name,
                initial_state_sha256=initial_state_sha256,
                arm_config_sha256=arm_config_sha256,
                split_sha256=split_sha256,
                preprocess_sha256=preprocess_sha256,
                order_hashes=order_hashes,
            )
            if checkpoint_payload is None:
                if status_progress:
                    raise ValueError("Arm progress has no matching rolling checkpoint")
            else:
                start_epoch = int(checkpoint_payload["completed_epochs"])
                if status_progress > start_epoch:
                    raise ValueError("Arm status is ahead of its verified checkpoint")
                _verify_epoch_records(
                    arm_dir,
                    start_epoch,
                    arm_name=arm_name,
                    initial_state_sha256=initial_state_sha256,
                    arm_config_sha256=arm_config_sha256,
                    split_sha256=split_sha256,
                    preprocess_sha256=preprocess_sha256,
                    order_hashes=order_hashes,
                )
                model.load_state_dict(checkpoint_payload["model_state"], strict=True)
                optimizer.load_state_dict(checkpoint_payload["optimizer_state"])
                scaler.load_state_dict(checkpoint_payload["scaler_state"])
            if current_status == "completed":
                if start_epoch != DIAGNOSTIC_EPOCHS:
                    raise ValueError("Completed arm has incomplete checkpoint progress")
                _rebuild_history(arm_dir, start_epoch)
                return
            completed_epochs = start_epoch
            _remove_uncommitted_epoch(arm_dir, start_epoch + 1)
            for orphan in arm_dir.glob("rolling_checkpoint_epoch_*.pt"):
                pointer = _checkpoint_pointer_path(arm_dir)
                referenced = None
                if pointer.is_file():
                    referenced = json.loads(pointer.read_text(encoding="utf-8")).get("filename")
                if orphan.name != referenced and orphan.is_file():
                    orphan.unlink()
            for temporary in arm_dir.glob(".rolling_checkpoint.*.tmp"):
                if temporary.is_file():
                    temporary.unlink()
            _rebuild_history(arm_dir, start_epoch)
            update_status(
                status_path,
                "running",
                start_epoch,
                DIAGNOSTIC_EPOCHS,
                progress_name="completed_epochs",
                allow_resume=current_status == "interrupted",
            )
        for epoch in range(start_epoch, DIAGNOSTIC_EPOCHS):
            order = epoch_orders[epoch]
            if sample_order_sha256(order) != order_hashes[epoch]:
                raise ValueError("Training sample order hash changed")
            train_dataset.set_epoch(epoch)
            seed_all(int(arm_config["seed"]) + epoch)
            loader_seed = torch.Generator(device="cpu").manual_seed(
                int(arm_config["seed"]) + epoch
            )
            train_loader = DataLoader(
                train_dataset,
                batch_size=int(arm_config["batch_size"]),
                sampler=FixedOrderSampler(order),
                shuffle=False,
                num_workers=0,
                pin_memory=True,
                generator=loader_seed,
            )
            train_report = run_epoch(
                model,
                train_loader,
                device,
                arm_config,
                optimizer=optimizer,
                scaler=scaler,
                class_weights=class_weights,
            )
            validation_seed = torch.Generator(device="cpu").manual_seed(
                int(arm_config["seed"]) + epoch + DIAGNOSTIC_EPOCHS
            )
            validation_loader = DataLoader(
                validation_dataset,
                batch_size=int(arm_config["batch_size"]),
                shuffle=False,
                num_workers=0,
                pin_memory=True,
                generator=validation_seed,
            )
            validation_report = run_epoch(
                model,
                validation_loader,
                device,
                arm_config,
                class_weights=None,
                include_predictions=True,
            )
            probabilities = validation_report.pop("probabilities")
            targets = validation_report.pop("targets")
            _enrich_metrics(train_report)
            _enrich_metrics(validation_report, probabilities)
            train_report.update({
                "research_status": RESEARCH_STATUS,
                "cohort_status": COHORT_STATUS,
                "arm": arm_name,
                "epoch": epoch + 1,
                "loss_kind": "weighted_focal" if weighted else "unweighted_focal",
            })
            validation_report.update({
                "research_status": RESEARCH_STATUS,
                "cohort_status": COHORT_STATUS,
                "arm": arm_name,
                "epoch": epoch + 1,
                "loss_kind": "unweighted_focal",
            })

            _write_json(arm_dir / f"epoch_{epoch + 1:02d}_train_metrics.json",
                        _safe_json_value(train_report))
            _write_json(arm_dir / f"epoch_{epoch + 1:02d}_validation_metrics.json",
                        _safe_json_value(validation_report))
            _write_csv(
                arm_dir / f"epoch_{epoch + 1:02d}_validation_predictions.csv",
                ("research_status", "cohort_status", "epoch", "sample_index", "image_path",
                 "true_class", "predicted_class", *(f"prob_{name}" for name in CLASS_NAMES)),
                _validation_prediction_rows(validation_dataset, probabilities, targets, epoch + 1),
            )
            _write_confusion_matrix(
                arm_dir / f"epoch_{epoch + 1:02d}_validation_confusion_matrix.csv",
                validation_report["confusion_matrix"],
                epoch + 1,
            )
            _write_json(
                arm_dir / f"epoch_{epoch + 1:02d}_predicted_class_distribution.json",
                {
                    "research_status": RESEARCH_STATUS,
                    "cohort_status": COHORT_STATUS,
                    "epoch": epoch + 1,
                    "predicted_class_distribution": validation_report[
                        "predicted_class_distribution"
                    ],
                },
            )
            _write_json(
                arm_dir / f"batchnorm_epoch_{epoch + 1:02d}.json",
                _batchnorm_record(model, initial_bn_buffers, epoch + 1),
            )
            artifact_manifest_sha256 = _write_epoch_manifest(
                arm_dir,
                epoch + 1,
                arm_name=arm_name,
                initial_state_sha256=initial_state_sha256,
                arm_config_sha256=arm_config_sha256,
                split_sha256=split_sha256,
                preprocess_sha256=preprocess_sha256,
                sample_order_sha256=order_hashes[epoch],
                model_state_sha256_value=model_state_sha256(model.state_dict()),
            )
            model_state = {
                name: value.detach().to(device="cpu").contiguous().clone()
                for name, value in model.state_dict().items()
            }
            checkpoint = {
                "format_version": 2,
                "research_status": RESEARCH_STATUS,
                "cohort_status": COHORT_STATUS,
                "arm": arm_name,
                "completed_epochs": epoch + 1,
                "model_state": model_state,
                "model_state_sha256": model_state_sha256(model_state),
                "optimizer_state": optimizer.state_dict(),
                "scheduler_state": None,
                "scaler_state": scaler.state_dict(),
                "initial_model_state_sha256": initial_state_sha256,
                "configuration_sha256": arm_config_sha256,
                "split_sha256": split_sha256,
                "preprocessing_fingerprint": preprocess_sha256,
                "sample_order_sha256": order_hashes[epoch],
                "epoch_manifest_sha256": artifact_manifest_sha256,
            }
            _save_rolling_checkpoint(
                arm_dir,
                checkpoint,
                arm_name=arm_name,
                initial_state_sha256=initial_state_sha256,
                arm_config_sha256=arm_config_sha256,
                split_sha256=split_sha256,
                preprocess_sha256=preprocess_sha256,
                order_hashes=order_hashes,
            )
            completed_epochs = epoch + 1
            _rebuild_history(arm_dir, completed_epochs)
            update_status(
                status_path, "running", completed_epochs, DIAGNOSTIC_EPOCHS,
                progress_name="completed_epochs",
            )
        if completed_epochs != DIAGNOSTIC_EPOCHS:
            raise RuntimeError("Diagnostic arm did not complete all five epochs")
        update_status(status_path, "completed", completed_epochs, DIAGNOSTIC_EPOCHS,
                      progress_name="completed_epochs")
    except KeyboardInterrupt as error:
        _record_arm_failure_without_masking(
            status_path, "interrupted", completed_epochs, error
        )
        raise
    except Exception as error:
        _record_arm_failure_without_masking(status_path, "failed", completed_epochs, error)
        raise


def run_experiment(
    root: Path = ROOT,
    runs_root: Path | None = None,
    experiment_id: str | None = None,
    *,
    resume_experiment_id: str | None = None,
    confirm_stale_lock: bool = False,
) -> Path:
    from nine_class_exploratory import CONFIG, SPLIT, validate_frozen
    from nine_class_training import build_model, load_config, run_epoch, seed_all

    root = root.resolve()
    runs_root = runs_root or root / "analysis/nine_class_three_arm_diagnostics"
    runs_root = validate_output_root(
        runs_root,
        protected_output_roots(root),
        project_root=root,
    )
    if experiment_id is not None and resume_experiment_id is not None:
        raise ValueError("Specify a new experiment id or a resume id, not both")
    if confirm_stale_lock and resume_experiment_id is None:
        raise ValueError("Stale-lock confirmation requires an explicit resume id")

    experiment_dir: Path | None = None
    experiment_status: Path | None = None
    lock: ExperimentLock | None = None
    resuming = resume_experiment_id is not None
    if resuming:
        if (
            not resume_experiment_id
            or resume_experiment_id in {".", ".."}
            or Path(resume_experiment_id).name != resume_experiment_id
            or PureWindowsPath(resume_experiment_id).name != resume_experiment_id
        ):
            raise ValueError("Resume id must be a single path component")
        experiment_dir = (runs_root / resume_experiment_id).resolve()
        if (
            experiment_dir.parent != runs_root
            or not experiment_dir.is_dir()
        ):
            raise FileNotFoundError("The requested diagnostic experiment does not exist")
        lock = ExperimentLock(experiment_dir)
        lock.acquire(resume=True, confirm_stale=confirm_stale_lock)

    try:
        rows, frozen = validate_frozen(
            root,
            verify_bytes=True,
            image_partitions=ALLOWED_IMAGE_PARTITIONS,
        )
        if frozen.get("status") != RESEARCH_STATUS or not all(
            row.get("approval_status") == COHORT_STATUS for row in rows
        ):
            raise ValueError("Exploratory cohort status or frozen provenance mismatch")
        base_config = load_config(CONFIG)
        _validate_base_configuration(base_config)
        preprocess = preprocessing_for_training(base_config)
        preprocess_sha256 = preprocessing_hash(preprocess)
        train_dataset, validation_dataset = _create_datasets(
            root, SPLIT, preprocess, int(base_config["seed"])
        )
        class_counts, class_weights = inverse_sqrt_class_weights(train_dataset.rows)
        sample_weighted_mean = training_sample_weighted_mean(class_counts, class_weights)
        epoch_orders = tuple(
            epoch_sample_order(len(train_dataset), int(base_config["seed"]), epoch)
            for epoch in range(DIAGNOSTIC_EPOCHS)
        )
        order_hashes = tuple(sample_order_sha256(order) for order in epoch_orders)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type != "cuda":
            raise RuntimeError("Three-arm diagnostic requires CUDA")
        base_config_sha256 = frozen["config_sha256"]
        split_sha256 = frozen["split_sha256"]

        if not resuming:
            experiment_dir = create_experiment_directory(runs_root, experiment_id)
            lock = ExperimentLock(experiment_dir)
            lock.acquire()
        experiment_status = experiment_dir / "status.json"
        if not resuming:
            update_status(
                experiment_status, "created", 0, len(ARM_DEFINITIONS),
                progress_name="completed_arms",
            )

        arm_configs = {
            arm[0]: _arm_configuration(base_config, arm) for arm in ARM_DEFINITIONS
        }
        arm_hashes = {
            name: hashlib.sha256(canonical_json_bytes(config)).hexdigest()
            for name, config in arm_configs.items()
        }

        arm_dirs: dict[str, Path] = {}
        for arm in ARM_DEFINITIONS:
            arm_name = arm[0]
            arm_dir = experiment_dir / arm_name
            resolved_arm_dir = arm_dir.resolve()
            if (
                resolved_arm_dir == experiment_dir
                or experiment_dir not in resolved_arm_dir.parents
                or runs_root not in resolved_arm_dir.parents
            ):
                raise ValueError("Arm output directory escaped the diagnostic output root")
            arm_dirs[arm_name] = arm_dir
            config_path = arm_dir / "configuration.json"
            expected_config_bytes = canonical_json_bytes(arm_configs[arm_name])
            if resuming:
                if not arm_dir.is_dir() or config_path.read_bytes() != expected_config_bytes:
                    raise ValueError(f"Existing arm configuration mismatch: {arm_name}")
            else:
                arm_dir.mkdir(exist_ok=False)
                with config_path.open("xb") as handle:
                    handle.write(expected_config_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())
                update_status(
                    arm_dir / "status.json", "created", 0, DIAGNOSTIC_EPOCHS,
                    progress_name="completed_epochs",
                )

        if resuming:
            experiment_status_record = json.loads(
                experiment_status.read_text(encoding="utf-8")
            )
            parent_status = experiment_status_record.get("status")
            if parent_status in {"failed", "completed"}:
                raise ValueError(f"Experiment cannot be resumed from status {parent_status}")
            manifest_path = experiment_dir / "experiment_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected_manifest = {
                "research_status": RESEARCH_STATUS,
                "cohort_status": COHORT_STATUS,
                "base_configuration_sha256": base_config_sha256,
                "split_sha256": split_sha256,
                "preprocessing_fingerprint": preprocess_sha256,
                "initial_state_hash_algorithm": STATE_HASH_ALGORITHM,
                "training_sample_weighted_mean_of_class_weights": sample_weighted_mean,
                "class_order": list(CLASS_NAMES),
                "seed": int(base_config["seed"]),
                "epochs": DIAGNOSTIC_EPOCHS,
                "diagnostic_overrides": _diagnostic_override_record(base_config),
                "sample_order_sha256_by_epoch": list(order_hashes),
            }
            if any(manifest.get(name) != value for name, value in expected_manifest.items()):
                raise ValueError("Existing experiment manifest differs from current inputs")
            for arm in ARM_DEFINITIONS:
                arm_name = arm[0]
                expected_arm = {
                    "definition": {
                        "letter": arm[1],
                        "batchnorm_policy": arm[2],
                        "class_weighting": arm[3],
                    },
                    "configuration_sha256": arm_hashes[arm_name],
                }
                if manifest.get("arms", {}).get(arm_name) != expected_arm:
                    raise ValueError(f"Existing experiment arm definition mismatch: {arm_name}")
            initial_state_sha256 = manifest.get("initial_model_state_sha256")
            if not isinstance(initial_state_sha256, str):
                raise ValueError("Existing experiment has no shared initialization hash")
            load_shared_initial_state(
                experiment_dir / "initial_model_state.pt", initial_state_sha256
            )
            runtime = manifest.get("runtime_metadata")
            if not isinstance(runtime, dict):
                raise ValueError("Existing experiment runtime provenance is missing")
            current_runtime = _runtime_metadata(device)
            runtime_identity_fields = (
                "python", "pytorch", "torchvision", "cuda_runtime", "device",
                "gpu_name", "cudnn_deterministic", "cudnn_benchmark",
                "deterministic_algorithms",
            )
            if any(
                runtime.get(field) != current_runtime.get(field)
                for field in runtime_identity_fields
            ):
                raise ValueError("Runtime differs from the original experiment")
            _record_resume_attempt(experiment_dir, current_runtime)
            completed_arms = sum(
                json.loads((arm_dirs[arm[0]] / "status.json").read_text(
                    encoding="utf-8"
                )).get("status") == "completed"
                for arm in ARM_DEFINITIONS
            )
            update_status(
                experiment_status,
                "running",
                completed_arms,
                len(ARM_DEFINITIONS),
                progress_name="completed_arms",
                allow_resume=parent_status == "interrupted",
            )
        else:
            seed_all(int(base_config["seed"]))
            template_model, initial_branch_hashes = build_model(base_config, root)
            initial_state = {
                name: value.detach().to(device="cpu").contiguous().clone()
                for name, value in template_model.state_dict().items()
            }
            initial_state_sha256 = _write_initial_state(experiment_dir, initial_state)
            del template_model
            runtime = _runtime_metadata(device)
            _write_json(experiment_dir / "experiment_manifest.json", {
                "research_status": RESEARCH_STATUS,
                "cohort_status": COHORT_STATUS,
                "base_configuration_sha256": base_config_sha256,
                "split_sha256": split_sha256,
                "preprocessing_fingerprint": preprocess_sha256,
                "initial_model_state_sha256": initial_state_sha256,
                "initial_state_hash_algorithm": STATE_HASH_ALGORITHM,
                "training_sample_weighted_mean_of_class_weights": sample_weighted_mean,
                "class_order": list(CLASS_NAMES),
                "seed": int(base_config["seed"]),
                "epochs": DIAGNOSTIC_EPOCHS,
                "diagnostic_overrides": _diagnostic_override_record(base_config),
                "initial_branch_hashes": initial_branch_hashes,
                "runtime_metadata": runtime,
                "sample_order_sha256_by_epoch": list(order_hashes),
                "arms": {
                    arm[0]: {
                        "definition": {"letter": arm[1], "batchnorm_policy": arm[2],
                                       "class_weighting": arm[3]},
                        "configuration_sha256": arm_hashes[arm[0]],
                    }
                    for arm in ARM_DEFINITIONS
                },
            })
            update_status(
                experiment_status, "running", 0, len(ARM_DEFINITIONS),
                progress_name="completed_arms",
            )

        for arm in ARM_DEFINITIONS:
            arm_name = arm[0]
            _run_arm(
                arm=arm,
                arm_dir=arm_dirs[arm_name],
                arm_config=arm_configs[arm_name],
                arm_config_sha256=arm_hashes[arm_name],
                root=root,
                train_dataset=train_dataset,
                validation_dataset=validation_dataset,
                initial_state_path=experiment_dir / "initial_model_state.pt",
                initial_state_sha256=initial_state_sha256,
                epoch_orders=epoch_orders,
                order_hashes=order_hashes,
                class_counts=class_counts,
                class_weights_by_name=class_weights,
                sample_weighted_mean=sample_weighted_mean,
                split_sha256=split_sha256,
                preprocess_sha256=preprocess_sha256,
                runtime=runtime,
                device=device,
                build_model=build_model,
                run_epoch=run_epoch,
                seed_all=seed_all,
                resume=resuming,
            )
            completed_arms = sum(
                json.loads((arm_dirs[definition[0]] / "status.json").read_text(
                    encoding="utf-8"
                ))["status"] == "completed"
                for definition in ARM_DEFINITIONS
            )
            update_status(
                experiment_status, "running", completed_arms, len(ARM_DEFINITIONS),
                progress_name="completed_arms",
            )
        update_status(
            experiment_status, "completed", len(ARM_DEFINITIONS), len(ARM_DEFINITIONS),
            progress_name="completed_arms",
        )
        return experiment_dir
    except KeyboardInterrupt as error:
        if experiment_status is not None and experiment_status.exists():
            _persist_experiment_terminal_status(
                experiment_status,
                "interrupted",
                len(ARM_DEFINITIONS),
                progress_name="completed_arms",
                error=str(error) or "KeyboardInterrupt",
            )
        raise
    except Exception as error:
        if experiment_status is not None and experiment_status.exists():
            _persist_experiment_terminal_status(
                experiment_status,
                "failed",
                len(ARM_DEFINITIONS),
                progress_name="completed_arms",
                error=f"{type(error).__name__}: {error}",
            )
        raise
    finally:
        if lock is not None:
            lock.release()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    parser.add_argument("--experiment-id")
    parser.add_argument("--resume-experiment")
    parser.add_argument("--confirm-stale-lock", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.preflight_only:
        if args.resume_experiment or args.confirm_stale_lock:
            parser.error("--preflight-only cannot be combined with resume options")
        print(json.dumps(preflight_diagnostic(args.root), indent=2))
        return 0
    experiment_dir = run_experiment(
        args.root,
        args.runs_root,
        args.experiment_id,
        resume_experiment_id=args.resume_experiment,
        confirm_stale_lock=args.confirm_stale_lock,
    )
    print(json.dumps({"status": RESEARCH_STATUS, "experiment_dir": str(experiment_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
