from __future__ import annotations

import hashlib
import io
import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, UnidentifiedImageError
from torch import nn

from showcase_data import CLASS_NAMES, ROOT, project_path


SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from models.egvan import build_nine_class_egvan  # noqa: E402
from nine_class_dataset import (  # noqa: E402
    PreprocessConfig,
    preprocessing_for_training,
    preprocessing_hash,
)
from preprocessing import gray_world, remove_hair, retinex  # noqa: E402


CHECKPOINT_RELATIVE = (
    "analysis/nine_class_exploratory/runs/"
    "EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt"
)
RUN_PROVENANCE_RELATIVE = (
    "analysis/nine_class_exploratory/runs/"
    "EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/run_provenance.json"
)
TRAINING_CONFIG_RELATIVE = "config/nine_class_training_t4_four_way_v2.json"
PREPROCESSING_CONFIG_RELATIVE = "config/nine_class_preprocessing_raw_v2.json"
EXPECTED_CHECKPOINT_SHA256 = (
    "3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08"
)
EXPECTED_RESEARCH_STATUS = "EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}


@dataclass(frozen=True)
class LoadedPredictor:
    model: nn.Module
    preprocessing: PreprocessConfig
    checkpoint_sha256: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verified_preprocessing(
    run_provenance: dict,
    training_config: dict,
    preprocessing_config: dict,
) -> PreprocessConfig:
    label_order = list(CLASS_NAMES)
    if run_provenance.get("research_status") != EXPECTED_RESEARCH_STATUS:
        raise ValueError("Checkpoint provenance does not identify an exploratory run")
    if run_provenance.get("config", {}).get("label_order") != label_order:
        raise ValueError("Run provenance class order differs from the showcase class order")
    if training_config.get("label_order") != label_order:
        raise ValueError("Training configuration class order differs from the showcase")
    if training_config.get("preprocessing_mode") != preprocessing_config.get("pipeline_version"):
        raise ValueError("Training and preprocessing configurations do not match")
    if preprocessing_config.get("status") != "candidate_for_future_approved_cohort; no_training_authorized":
        raise ValueError("Unexpected preprocessing specification status")
    if preprocessing_config.get("resize_interpolation") != "INTER_AREA":
        raise ValueError("Unsupported preprocessing interpolation")
    if preprocessing_config.get("channel_order") != "RGB":
        raise ValueError("Unsupported preprocessing channel order")
    if float(preprocessing_config.get("pixel_scale", 0)) != 255.0:
        raise ValueError("Unsupported preprocessing pixel scale")
    if tuple(preprocessing_config.get("mean", ())) != (0.485, 0.456, 0.406):
        raise ValueError("Preprocessing mean differs from the source implementation")
    if tuple(preprocessing_config.get("std", ())) != (0.229, 0.224, 0.225):
        raise ValueError("Preprocessing standard deviation differs from the source implementation")
    preprocessing = preprocessing_for_training(training_config)
    if preprocessing.image_size != int(preprocessing_config.get("image_size", 0)):
        raise ValueError("Training and preprocessing image sizes do not match")
    if preprocessing_hash(preprocessing) != run_provenance.get("preprocess_config_sha256"):
        raise ValueError("Preprocessing hash differs from checkpoint provenance")
    return preprocessing


@lru_cache(maxsize=1)
def load_predictor() -> LoadedPredictor:
    checkpoint = project_path(CHECKPOINT_RELATIVE)
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Nine-class checkpoint is missing: {CHECKPOINT_RELATIVE}")
    checkpoint_sha256 = _sha256_file(checkpoint)
    if checkpoint_sha256 != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Nine-class checkpoint SHA-256 does not match the recorded value")

    provenance = json.loads(project_path(RUN_PROVENANCE_RELATIVE).read_text(encoding="utf-8"))
    training_config_path = project_path(TRAINING_CONFIG_RELATIVE)
    training_config_bytes = training_config_path.read_bytes()
    if hashlib.sha256(training_config_bytes).hexdigest() != provenance.get("config_sha256"):
        raise ValueError("Training configuration hash differs from checkpoint provenance")
    training_config = json.loads(training_config_bytes)
    preprocessing_config = json.loads(
        project_path(PREPROCESSING_CONFIG_RELATIVE).read_text(encoding="utf-8")
    )
    preprocessing = _verified_preprocessing(
        provenance, training_config, preprocessing_config
    )

    state = torch.load(
        checkpoint,
        map_location="cpu",
        weights_only=True,
        mmap=True,
    )
    if not isinstance(state, dict) or not isinstance(state.get("model_state"), dict):
        raise ValueError("Checkpoint does not contain a supported model state")
    for key in ("config_sha256", "split_sha256", "preprocess_config_sha256"):
        if state.get(key) != provenance.get(key):
            raise ValueError(f"Checkpoint {key} differs from run provenance")

    model = build_nine_class_egvan(
        pretrained_efficient=False,
        pretrained_resnet=False,
        fusion_channels=int(training_config["fusion_channels"]),
    )
    model.load_state_dict(state["model_state"], strict=True)
    if model.classifier.out_features != len(CLASS_NAMES):
        raise ValueError("Loaded checkpoint does not expose nine output classes")
    model.to("cpu")
    model.eval()
    return LoadedPredictor(model, preprocessing, checkpoint_sha256)


def _decode_upload(payload: bytes) -> np.ndarray:
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("Upload an image file with non-empty contents.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError("Image exceeds the 20 MiB upload limit.")
    try:
        with Image.open(io.BytesIO(payload)) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ValueError("Only JPEG and PNG images are supported.")
            width, height = image.size
            if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions exceed the 25-megapixel safety limit.")
            image.verify()
    except UnidentifiedImageError as exc:
        raise ValueError("The uploaded file is not a supported image.") from exc
    except OSError as exc:
        raise ValueError("The uploaded image is damaged or could not be decoded.") from exc

    bgr = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("The uploaded image could not be decoded.")
    return bgr


def preprocess_upload(
    payload: bytes,
    config: PreprocessConfig,
) -> tuple[np.ndarray, torch.Tensor]:
    bgr = _decode_upload(payload)
    if config.pipeline_version == "stage4_full_v1":
        bgr = remove_hair(
            bgr, config.hair_kernel_size, config.hair_threshold, config.inpaint_radius
        )
        bgr = gray_world(bgr)
        bgr = retinex(bgr, config.retinex_sigmas, config.retinex_weights)
    elif config.pipeline_version != "raw_resize_imagenet_v2":
        raise ValueError("Unsupported checkpoint preprocessing pipeline.")

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(
        rgb,
        (config.image_size, config.image_size),
        interpolation=cv2.INTER_AREA,
    )
    tensor = (
        torch.from_numpy(np.ascontiguousarray(rgb.transpose(2, 0, 1)))
        .float()
        .div_(255.0)
    )
    mean = torch.tensor(config.mean, dtype=tensor.dtype).view(3, 1, 1)
    std = torch.tensor(config.std, dtype=tensor.dtype).view(3, 1, 1)
    tensor = (tensor - mean) / std
    if tensor.shape != (3, config.image_size, config.image_size):
        raise ValueError("Preprocessed image has an unexpected shape.")
    if not torch.isfinite(tensor).all().item():
        raise ValueError("Preprocessed image contains non-finite values.")
    return rgb, tensor


def predict_upload(payload: bytes) -> tuple[np.ndarray, dict[str, float]]:
    predictor = load_predictor()
    preview, image_tensor = preprocess_upload(payload, predictor.preprocessing)
    with torch.inference_mode():
        logits = predictor.model(image_tensor.unsqueeze(0))
        probabilities = torch.softmax(logits.float(), dim=1)
    if tuple(probabilities.shape) != (1, len(CLASS_NAMES)):
        raise ValueError("Model did not return nine class probabilities.")
    if not torch.isfinite(probabilities).all().item():
        raise ValueError("Model produced non-finite probabilities.")
    if not torch.allclose(
        probabilities.sum(dim=1),
        torch.ones(1, dtype=probabilities.dtype),
        rtol=0.0,
        atol=1e-6,
    ):
        raise ValueError("Model probabilities do not sum to one.")
    return preview, {
        name: float(probabilities[0, index].item())
        for index, name in enumerate(CLASS_NAMES)
    }
