from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

SHOWCASE = Path(__file__).resolve().parents[1]
ROOT = SHOWCASE.parent
sys.path.insert(0, str(SHOWCASE))
sys.path.insert(0, str(ROOT / "src"))

from nine_class_dataset import image_tensor, preprocessing_for_training  # noqa: E402
from nine_class_inference import (  # noqa: E402
    ALLOWED_IMAGE_FORMATS,
    MAX_IMAGE_PIXELS,
    MAX_UPLOAD_BYTES,
    _decode_upload,
    load_predictor,
    predict_upload,
    preprocess_upload,
)
from nine_class_stage4 import CLASS_NAMES  # noqa: E402
from showcase_data import project_path  # noqa: E402


def _png_bytes(array: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_preprocessing_matches_source_image_tensor(tmp_path):
    source = np.zeros((31, 47, 3), dtype=np.uint8)
    source[:, :23] = (230, 35, 80)
    source[:, 23:] = (15, 170, 210)
    payload = _png_bytes(source)
    path = tmp_path / "source.png"
    path.write_bytes(payload)
    config = preprocessing_for_training(
        {
            "image_size": 384,
            "preprocessing_mode": "raw_resize_imagenet_v2",
        }
    )

    preview, tensor = preprocess_upload(payload, config)
    expected = image_tensor(path, config)

    assert preview.shape == (384, 384, 3)
    assert tensor.shape == (3, 384, 384)
    assert torch.allclose(tensor, expected, rtol=0.0, atol=0.0)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "non-empty"),
        (b"not an image", "not a supported image"),
        (None, "non-empty"),
    ],
)
def test_invalid_uploads_are_rejected(payload, message):
    with pytest.raises(ValueError, match=message):
        _decode_upload(payload)


def test_unsupported_format_oversized_file_and_dimensions_are_rejected():
    gif_buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(gif_buffer, format="GIF")
    with pytest.raises(ValueError, match="Only JPEG and PNG"):
        _decode_upload(gif_buffer.getvalue())

    with pytest.raises(ValueError, match="20 MiB"):
        _decode_upload(b"x" * (MAX_UPLOAD_BYTES + 1))

    oversized_dimensions = Image.new("1", (MAX_IMAGE_PIXELS + 1, 1))
    buffer = io.BytesIO()
    oversized_dimensions.save(buffer, format="PNG")
    payload = buffer.getvalue()
    with pytest.raises(ValueError, match="25-megapixel"):
        _decode_upload(payload)


def test_checkpoint_loads_strictly_and_returns_nine_finite_probabilities():
    predictor = load_predictor()
    checkpoint = project_path(
        "analysis/nine_class_exploratory/runs/"
        "EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt"
    )
    image_path = project_path(
        "data/raw/HAM10000_images_part_1/ISIC_0025837.jpg"
    )
    assert predictor.checkpoint_sha256 == (
        "3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08"
    )
    assert tuple(CLASS_NAMES) == (
        "AKIEC",
        "BCC",
        "BKL",
        "DF",
        "MEL",
        "NV",
        "VASC",
        "BENIGN",
        "MALIGNANT",
    )
    assert checkpoint.is_file() and image_path.is_file()
    preview, probabilities = predict_upload(image_path.read_bytes())

    assert preview.shape == (384, 384, 3)
    assert tuple(probabilities) == CLASS_NAMES
    assert len(probabilities) == 9
    assert all(np.isfinite(value) for value in probabilities.values())
    assert sum(probabilities.values()) == pytest.approx(1.0, abs=1e-6)
