"""On-demand nine-label RGB loader for architecture and pipeline verification."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

from nine_class_stage4 import CLASS_NAMES
from preprocessing import gray_world, remove_hair, retinex


@dataclass(frozen=True)
class PreprocessConfig:
    image_size: int = 384
    hair_kernel_size: int = 17
    hair_threshold: int = 10
    inpaint_radius: float = 1.0
    retinex_sigmas: tuple[float, ...] = (15.0, 80.0, 250.0)
    retinex_weights: tuple[float, ...] = (1 / 3, 1 / 3, 1 / 3)
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)


def image_tensor(path: Path, config: PreprocessConfig, *, train: bool = False) -> torch.Tensor:
    if not path.is_file():
        raise FileNotFoundError(path)
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Image could not be decoded: {path}")
    bgr = remove_hair(bgr, config.hair_kernel_size, config.hair_threshold, config.inpaint_radius)
    bgr = gray_world(bgr)
    bgr = retinex(bgr, config.retinex_sigmas, config.retinex_weights)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (config.image_size, config.image_size), interpolation=cv2.INTER_AREA)
    tensor = torch.from_numpy(np.ascontiguousarray(rgb.transpose(2, 0, 1))).float().div_(255.0)
    if train:
        if torch.rand(()) < 0.5:
            tensor = tensor.flip(-1)
        if torch.rand(()) < 0.5:
            tensor = tensor.flip(-2)
        turns = int(torch.randint(0, 4, ()).item())
        tensor = tensor.rot90(turns, (-2, -1))
    mean = torch.tensor(config.mean, dtype=tensor.dtype).view(3, 1, 1)
    std = torch.tensor(config.std, dtype=tensor.dtype).view(3, 1, 1)
    if (std <= 0).any():
        raise ValueError("Normalization std must be positive")
    result = (tensor - mean) / std
    if result.shape != (3, config.image_size, config.image_size) or not torch.isfinite(result).all():
        raise ValueError(f"Invalid preprocessed image: {path}")
    return result


class NineClassDataset(Dataset):
    """Loads only an explicitly assigned split; never invents assignments."""

    def __init__(self, root: Path, split_csv: Path, split: str,
                 config: PreprocessConfig = PreprocessConfig()) -> None:
        if split not in ("train", "validation", "test"):
            raise ValueError("Unknown split")
        with split_csv.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        required = {"image_path", "class_name", "class_index", "split"}
        if not rows or not required <= rows[0].keys():
            raise ValueError("Missing nine-class split columns")
        self.rows = [r for r in rows if r["split"] == split]
        if not self.rows:
            raise ValueError(f"No {split} rows; no split can be inferred")
        for row in self.rows:
            if row["class_name"] not in CLASS_NAMES or int(row["class_index"]) != CLASS_NAMES.index(row["class_name"]):
                raise ValueError("Nine-class label mapping mismatch")
            if split == "train" and row.get("source_split") == "test":
                raise ValueError("Protected publisher test record in training")
        self.root, self.split, self.config = Path(root), split, config

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        row = self.rows[index]
        return image_tensor(self.root / row["image_path"], self.config,
                            train=self.split == "train"), int(row["class_index"])
