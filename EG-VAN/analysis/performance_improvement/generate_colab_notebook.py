from __future__ import annotations

import json
from pathlib import Path


OUTPUT = Path(__file__).resolve().parent / "EG_VAN_COLAB_GPU_TRAINING.ipynb"


def code(lines: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines.splitlines(True),
    }


def markdown(lines: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": lines.splitlines(True),
    }


cells: list[dict] = []

cells.append(code("""# First cell — Mount Google Drive
from pathlib import Path
from google.colab import drive

drive.mount("/content/drive")

PROJECT_ROOT = Path("/content/drive/MyDrive/EG-VAN")
DRIVE_OUTPUT_DIR = Path("/content/drive/MyDrive/EG-VAN/colab_runs")
NOTEBOOK_OUTPUT_DIR = DRIVE_OUTPUT_DIR / "egvan_gpu_training"
if not PROJECT_ROOT.is_dir():
    raise FileNotFoundError(f"Uploaded EG-VAN project folder not found: {PROJECT_ROOT}")
DRIVE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print("Project:", PROJECT_ROOT)
print("Persistent notebook output:", NOTEBOOK_OUTPUT_DIR)
print("ZIP output directory:", DRIVE_OUTPUT_DIR)"""))

cells.append(markdown("""# EG-VAN GPU Training — Reproducible Nine-Class Colab Experiment

**EXPLORATORY / NON-CLINICAL.** This notebook does not approve the cohort, establish
leakage-safe validation, or reproduce the EG-VAN paper. It requires explicit GPU
and exploratory-training opt-in. No pretrained weights are downloaded.

The 80% figure is an experimental target, not a guarantee. Do not report a result
unless it is actually produced by this notebook. Synthetic tensors are used only
for architecture/runtime smoke checks, never for model metrics."""))

cells.append(code("""# Cell 1 — Environment and GPU verification
import os, platform, sys, json, time, hashlib, shutil, zipfile
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import cv2
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, UnidentifiedImageError
import psutil

print("Python:", platform.python_version())
print("PyTorch:", torch.__version__)
try:
    import torchvision
    print("Torchvision:", torchvision.__version__)
    torch_pair = tuple(int(part) for part in torch.__version__.split("+")[0].split(".")[:2])
    torchvision_pair = tuple(
        int(part) for part in torchvision.__version__.split("+")[0].split(".")[:2]
    )
    if torch_pair[0] != 2 or torch_pair[1] < 3:
        raise RuntimeError(
            f"PyTorch >=2.3 is required for the CUDA AMP APIs used here: {torch.__version__}"
        )
    if torch_pair[0] == 2 and not (
        torchvision_pair[0] == 0 and torchvision_pair[1] == torch_pair[1] + 15
    ):
        raise RuntimeError(
            f"Unsupported PyTorch/Torchvision version pair: "
            f"{torch.__version__}/{torchvision.__version__}"
        )
    if torch_pair[0] == 1 and not (
        torchvision_pair[0] == 0 and torchvision_pair[1] == torch_pair[1] + 1
    ):
        raise RuntimeError(
            f"Unsupported PyTorch/Torchvision version pair: "
            f"{torch.__version__}/{torchvision.__version__}"
        )
except Exception as exc:
    raise RuntimeError(f"Torchvision is unavailable or incompatible: {exc}") from exc
print("NumPy:", np.__version__)
print("OpenCV:", cv2.__version__)
print("Pandas:", pd.__version__)
print("Matplotlib:", matplotlib.__version__)
print("psutil:", psutil.__version__)
torchvision.ops.nms(
    torch.tensor([[0.0, 0.0, 1.0, 1.0]]),
    torch.tensor([1.0]),
    0.5,
)

if not torch.cuda.is_available():
    raise RuntimeError("CUDA is unavailable. Training stops; GPU runtime is required.")

gpu_name = torch.cuda.get_device_name(0)
props = torch.cuda.get_device_properties(0)
print("GPU:", gpu_name)
print("GPU memory (GiB):", round(props.total_memory / 1024**3, 2))
print("CUDA runtime:", torch.version.cuda)
print("CUDA device count:", torch.cuda.device_count())

vm = psutil.virtual_memory()
disk = shutil.disk_usage("/content")
print("Host RAM GiB:", round(vm.total / 1024**3, 2),
      "available GiB:", round(vm.available / 1024**3, 2))
print("Colab scratch disk free GiB:", round(disk.free / 1024**3, 2))

torch.manual_seed(42)
torch.cuda.manual_seed_all(42)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
print("Environment verification complete.")"""))

cells.append(markdown("""## 2. Uploaded project files and manifests

The notebook uses the extracted project at `/content/drive/MyDrive/EG-VAN`
directly. Paths in the CSV manifest are resolved from that project root (or its
`data/` directory when the manifest path is dataset-relative). No ZIP extraction
or guessed image basename fallback is used."""))

cells.append(code("""# Cell 2 — Verify project sources and configure direct Drive paths
DATASET_DIR = PROJECT_ROOT / "data"
MANIFEST_CSV = PROJECT_ROOT / "analysis/nine_class_stage4/nine_class_source_manifest.csv"
EXPLORATORY_SPLIT_CSV = PROJECT_ROOT / "analysis/nine_class_exploratory/exploratory_split.csv"
EXPLORATORY_PROVENANCE_JSON = PROJECT_ROOT / "analysis/nine_class_exploratory/exploratory_provenance.json"
PREPROCESSING_JSON = PROJECT_ROOT / "config/nine_class_preprocessing_raw_v2.json"
TRAINING_CONFIG_JSON = PROJECT_ROOT / "config/nine_class_training_t4_four_way_v2.json"
OPTIONAL_BASELINE_CHECKPOINT = (
    PROJECT_ROOT / "analysis/nine_class_exploratory/runs/"
    "EXPLORATORY_ONLY_20261108T193315Z_d50a9c07/best.pt"
)
OPTIONAL_BASELINE_EXPECTED_SHA256 = (
    "3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08"
)

required_paths = [
    PROJECT_ROOT / "src/models/egvan/egvan.py",
    PROJECT_ROOT / "src/nine_class_dataset.py",
    PROJECT_ROOT / "src/nine_class_metrics.py",
    PROJECT_ROOT / "src/nine_class_training.py",
    PROJECT_ROOT / "src/nine_class_exploratory.py",
    PROJECT_ROOT / "src/nine_class_evaluation.py",
    PROJECT_ROOT / "src/nine_class_stage4.py",
    TRAINING_CONFIG_JSON,
    MANIFEST_CSV,
    EXPLORATORY_SPLIT_CSV,
    EXPLORATORY_PROVENANCE_JSON,
    PREPROCESSING_JSON,
]
missing = [str(path) for path in required_paths if not path.is_file()]
if missing:
    raise FileNotFoundError("Missing required project files:\\n" + "\\n".join(missing))
if not DATASET_DIR.is_dir():
    raise FileNotFoundError(f"Dataset directory is missing: {DATASET_DIR}")

sys.path.insert(0, str(PROJECT_ROOT / "src"))
print("PROJECT_ROOT:", PROJECT_ROOT)
print("DATASET_DIR:", DATASET_DIR)
print("OUTPUT_DIR:", NOTEBOOK_OUTPUT_DIR)"""))

cells.append(markdown("""## 3. File inventory and integrity

The inventory verifies image bytes, labels, formats and split integrity. Missing
or invalid images are reported; they are not silently skipped."""))

cells.append(code("""# Cell 3 — File inventory and integrity
import csv
from pathlib import PurePosixPath
from collections import Counter

from nine_class_stage4 import CLASS_NAMES
from models.egvan import build_nine_class_egvan

CLASS_ORDER = list(CLASS_NAMES)
EXPECTED_LABELS = ["AKIEC","BCC","BKL","DF","MEL","NV","VASC","BENIGN","MALIGNANT"]
if CLASS_ORDER != EXPECTED_LABELS:
    raise RuntimeError(f"Class-order mismatch: {CLASS_ORDER}")

preprocessing = json.loads(PREPROCESSING_JSON.read_text(encoding="utf-8"))
if preprocessing["pipeline_version"] != "raw_resize_imagenet_v2":
    raise RuntimeError("This notebook requires raw_resize_imagenet_v2 preprocessing.")
if (preprocessing.get("resize_interpolation") != "INTER_AREA"
        or preprocessing.get("channel_order") != "RGB"
        or float(preprocessing.get("pixel_scale", 0)) != 255.0
        or tuple(preprocessing.get("mean", ())) != (0.485, 0.456, 0.406)
        or tuple(preprocessing.get("std", ())) != (0.229, 0.224, 0.225)):
    raise RuntimeError("Preprocessing JSON differs from the verified raw RGB pipeline.")
training_config = json.loads(TRAINING_CONFIG_JSON.read_text(encoding="utf-8"))
exploratory_provenance = json.loads(
    EXPLORATORY_PROVENANCE_JSON.read_text(encoding="utf-8")
)
if exploratory_provenance.get("status") != "EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION":
    raise RuntimeError("Exploratory provenance is missing the required research status.")
split_sha256 = hashlib.sha256(EXPLORATORY_SPLIT_CSV.read_bytes()).hexdigest()
if split_sha256 != exploratory_provenance.get("split_sha256"):
    raise RuntimeError("Historical exploratory split hash differs from its provenance.")
config_sha256 = hashlib.sha256(TRAINING_CONFIG_JSON.read_bytes()).hexdigest()
if config_sha256 != exploratory_provenance.get("config_sha256"):
    raise RuntimeError("Historical training config hash differs from exploratory provenance.")
if training_config.get("label_order") != EXPECTED_LABELS:
    raise RuntimeError("Training configuration class order differs from the model output.")
if training_config.get("preprocessing_mode") != preprocessing["pipeline_version"]:
    raise RuntimeError("Training and preprocessing configurations do not match.")
if (int(training_config["image_size"]) != int(preprocessing["image_size"])
        or int(training_config["batch_size"]) != 8
        or int(training_config["gradient_accumulation_steps"]) != 4
        or training_config["optimizer"].lower() != "adamax"
        or training_config.get("batchnorm_policy") != "freeze_running_stats"):
    raise RuntimeError("Training configuration differs from the expected T4 baseline.")
IMAGE_SIZE = int(preprocessing["image_size"])
MEAN = tuple(preprocessing["mean"])
STD = tuple(preprocessing["std"])

def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def resolve_manifest_image_path(value):
    normalized = str(value).strip().replace("\\\\", "/")
    if not normalized:
        raise ValueError("Manifest contains an empty image_path")
    supplied = Path(normalized)
    if supplied.is_absolute():
        candidates = [supplied]
    else:
        relative = PurePosixPath(normalized)
        candidates = [PROJECT_ROOT.joinpath(*relative.parts)]
        if not relative.parts or relative.parts[0] != "data":
            candidates.append(DATASET_DIR.joinpath(*relative.parts))
    project_root = PROJECT_ROOT.resolve()
    for candidate in candidates:
        if candidate.is_file():
            resolved = candidate.resolve()
            if project_root not in resolved.parents:
                raise ValueError(f"Image path escapes the uploaded project: {value}")
            return resolved
    raise FileNotFoundError(
        f"Image path does not resolve from the project root or data directory: {value}"
    )

split_rows = read_csv(EXPLORATORY_SPLIT_CSV)
manifest_rows = read_csv(MANIFEST_CSV)
if not split_rows or not manifest_rows:
    raise RuntimeError("The source manifest and exploratory split must contain records.")
required_manifest_columns = {
    "image_path", "original_label", "class_name", "class_index", "sha256",
    "source_dataset"
}
required_split_columns = {
    "image_path", "original_label", "class_name", "class_index", "sha256",
    "source_dataset", "split", "patient_id", "lesion_id", "overlap_group"
}
if not required_manifest_columns.issubset(manifest_rows[0]):
    raise RuntimeError(
        f"Source manifest missing columns: "
        f"{sorted(required_manifest_columns - set(manifest_rows[0]))}"
    )
if not required_split_columns.issubset(split_rows[0]):
    raise RuntimeError(
        f"Exploratory split missing columns: "
        f"{sorted(required_split_columns - set(split_rows[0]))}"
    )

missing_files = []
invalid_labels = []
invalid_images = []
hashes = {}
manifest_by_path = {}
resolved_paths = {}
digest_by_path = {}
manifest_classes = set()
for row in manifest_rows:
    path_value = row["image_path"]
    try:
        image_path = resolve_manifest_image_path(path_value)
    except (FileNotFoundError, ValueError) as exc:
        missing_files.append(f"{path_value}: {exc}")
        continue
    path_key = str(image_path)
    if path_key in manifest_by_path:
        invalid_labels.append(f"Duplicate manifest path: {path_value}")
    manifest_by_path[path_key] = row
    resolved_paths[path_key] = image_path
    manifest_classes.add(row["class_name"])
    if not row.get("original_label") or not row.get("source_dataset"):
        invalid_labels.append(f"Missing original source label/dataset: {path_value}")
    if row["class_name"] not in CLASS_ORDER:
        invalid_labels.append(f"Unknown manifest class: {path_value} -> {row['class_name']}")
    else:
        try:
            class_index = int(row["class_index"])
        except (TypeError, ValueError):
            class_index = -1
        if class_index != CLASS_ORDER.index(row["class_name"]):
            invalid_labels.append(
                f"Manifest index mismatch: {path_value} -> {row['class_name']}/{row['class_index']}"
            )
    digest = None
    try:
        image_bytes = image_path.read_bytes()
        digest = hashlib.sha256(image_bytes).hexdigest()
        with Image.open(image_path) as image:
            width, height = image.size
            image.verify()
            if width < 1 or height < 1:
                invalid_images.append(f"Invalid image dimensions: {path_value}")
            if image.format not in ("JPEG", "PNG"):
                invalid_images.append(f"Unsupported format {image.format}: {path_value}")
        decoded = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if decoded is None or decoded.ndim != 3 or decoded.shape[2] != 3:
            invalid_images.append(f"OpenCV decode failed: {path_value}")
        hashes.setdefault(digest, []).append(path_key)
        digest_by_path[path_key] = digest
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        invalid_images.append(f"Invalid image {path_value}: {exc}")
    if not row.get("sha256"):
        invalid_images.append(f"Missing manifest SHA-256: {path_value}")
    elif digest is not None and digest != row["sha256"]:
        invalid_images.append(f"SHA-256 mismatch: {path_value}")

split_classes = set()
seen_split_paths = set()
split_path_keys = {}
for row in split_rows:
    path_value = row["image_path"]
    try:
        image_path = resolve_manifest_image_path(path_value)
    except (FileNotFoundError, ValueError) as exc:
        missing_files.append(f"Split {path_value}: {exc}")
        continue
    path_key = str(image_path)
    split_path_keys[path_value] = path_key
    if path_key in seen_split_paths:
        invalid_labels.append(f"Duplicate split path: {path_value}")
    seen_split_paths.add(path_key)
    manifest_row = manifest_by_path.get(path_key)
    if manifest_row is None:
        invalid_labels.append(f"Split image absent from source manifest: {path_value}")
        continue
    split_classes.add(row["class_name"])
    if row["class_name"] not in CLASS_ORDER:
        invalid_labels.append(f"Unknown split class: {path_value} -> {row['class_name']}")
    else:
        try:
            class_index = int(row["class_index"])
        except (TypeError, ValueError):
            class_index = -1
        if class_index != CLASS_ORDER.index(row["class_name"]):
            invalid_labels.append(
                f"Split index mismatch: {path_value} -> {row['class_name']}/{row['class_index']}"
            )
    if (
        row["original_label"], row["source_dataset"],
        row["class_name"], row["class_index"]
    ) != (
        manifest_row["original_label"], manifest_row["source_dataset"],
        manifest_row["class_name"], manifest_row["class_index"]
    ):
        invalid_labels.append(f"Split label differs from source manifest: {path_value}")
    actual_digest = digest_by_path.get(path_key)
    if not row.get("sha256"):
        invalid_images.append(f"Missing split SHA-256: {path_value}")
    elif actual_digest is not None and actual_digest != row["sha256"]:
        invalid_images.append(f"Split SHA-256 mismatch: {path_value}")

for label in CLASS_ORDER:
    if label not in manifest_classes:
        invalid_labels.append(f"Required class absent from source manifest: {label}")
    if label not in split_classes:
        invalid_labels.append(f"Required class absent from exploratory split: {label}")

print("Manifest image rows:", len(manifest_rows))
print("Verified manifest image paths:", len(resolved_paths))
print("Exploratory split rows:", len(split_rows))
print("Unique split paths:", len(seen_split_paths))
print("Missing files:", len(missing_files))
print("Invalid labels:", len(invalid_labels))
print("Invalid images:", len(invalid_images))
print("Duplicate SHA-256 groups:", sum(len(v) > 1 for v in hashes.values()))
print("Manifest counts by source:", json.dumps(dict(Counter(
    row["source_dataset"] for row in manifest_rows
)), indent=2))
print("Manifest counts by class:", json.dumps(dict(Counter(
    row["class_name"] for row in manifest_rows
)), indent=2))
if missing_files:
    print("\\nMissing file report:", missing_files[:50])
if invalid_labels:
    print("\\nInvalid label report:", invalid_labels[:50])
if invalid_images:
    print("\\nInvalid image report:", invalid_images[:50])
if missing_files or invalid_labels or invalid_images:
    raise RuntimeError("Inventory integrity failed; fix the bundle or manifest before training.")

partition_counts = {part: {} for part in ("train","validation","calibration","test")}
for row in split_rows:
    if row["split"] not in partition_counts:
        raise RuntimeError(f"Unknown split partition: {row['split']}")
    partition_counts[row["split"]][row["class_name"]] = (
        partition_counts[row["split"]].get(row["class_name"], 0) + 1
    )
for partition in partition_counts:
    for label in CLASS_ORDER:
        partition_counts[partition].setdefault(label, 0)
print(json.dumps(partition_counts, indent=2))"""))

cells.append(markdown("""## 4. Evaluation protocol and development split

The existing exploratory split is **not approved** for final evaluation and is
never edited. A separate development split is built from its train, validation,
and calibration rows by taking connected components across every available
lesion, patient, overlap-group, and exact-image-hash identifier. The old test
partition is excluded and remains untouched."""))

cells.append(code("""# Cell 4 — Audit and create a separate grouped development split
import random
import io
from collections import defaultdict, Counter

CREATE_NEW_DEVELOPMENT_SPLIT = True
DEVELOPMENT_VAL_FRACTION = 0.20
SEED = 42

patient = sum(bool(row.get("patient_id")) for row in split_rows)
lesion = sum(bool(row.get("lesion_id")) for row in split_rows)
overlap = sum(bool(row.get("overlap_group")) for row in split_rows)
print("Rows with patient_id:", patient)
print("Rows with lesion_id:", lesion)
print("Rows with overlap_group:", overlap)

def normalized_identity(value):
    value = str(value or "").strip()
    return "" if value.lower() in {"", "na", "nan", "none", "null", "unknown"} else value

for field in ("patient_id", "lesion_id", "overlap_group"):
    identifiers = {normalized_identity(row.get(field)) for row in split_rows}
    identifiers.discard("")
    print(f"Unique {field} values:", len(identifiers))

def available_identity_keys(row):
    path_key = split_path_keys[row["image_path"]]
    digest = digest_by_path[path_key]
    keys = [("sha256", digest)]
    for field in ("lesion_id", "patient_id", "overlap_group"):
        value = normalized_identity(row.get(field))
        if value:
            keys.append((field, value))
    return keys

identity_partitions = defaultdict(set)
for row in split_rows:
    for identity in available_identity_keys(row):
        identity_partitions[identity].add(row["split"])
crossing_identities = sum(len(partitions) > 1 for partitions in identity_partitions.values())
print("Cross-partition available identity/hash groups:", crossing_identities)
print("Existing split approval status: NOT APPROVED")

if not CREATE_NEW_DEVELOPMENT_SPLIT:
    raise RuntimeError("A separate development split is required; do not train on the old split.")

development_source = [
    row for row in split_rows if row["split"] in ("train", "validation", "calibration")
]
parent = list(range(len(development_source)))

def find_root(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index

def union(left, right):
    left_root = find_root(left)
    right_root = find_root(right)
    if left_root != right_root:
        parent[right_root] = left_root

identity_owner = {}
for index, row in enumerate(development_source):
    for identity in available_identity_keys(row):
        if identity in identity_owner:
            union(index, identity_owner[identity])
        else:
            identity_owner[identity] = index

component_members = defaultdict(list)
for index, row in enumerate(development_source):
    component_members[find_root(index)].append((index, row))
component_classes = {
    component: {row["class_name"] for _, row in members}
    for component, members in component_members.items()
}
class_components = {
    name: {component for component, names in component_classes.items() if name in names}
    for name in CLASS_ORDER
}
for name in CLASS_ORDER:
    if len(class_components[name]) < 2:
        raise RuntimeError(
            f"Cannot split {name} without group leakage: fewer than two connected groups."
        )

rng = random.Random(SEED)
ordered_components = list(component_members)
rng.shuffle(ordered_components)
validation_components = set()
for name in CLASS_ORDER:
    if any(name in component_classes[key] for key in validation_components):
        continue
    candidates = [
        key for key in ordered_components
        if key not in validation_components and name in component_classes[key]
        and all(
            sum(
                other not in validation_components and label in component_classes[other]
                for other in component_members
            ) > 1
            for label in component_classes[key]
        )
    ]
    if not candidates:
        raise RuntimeError(f"Could not retain all classes in train and validation: {name}")
    validation_components.add(candidates[0])

target_validation_rows = max(
    sum(len(component_members[key]) for key in validation_components),
    int(len(development_source) * DEVELOPMENT_VAL_FRACTION),
)
for component in ordered_components:
    if sum(len(component_members[key]) for key in validation_components) >= target_validation_rows:
        break
    if component in validation_components:
        continue
    if all(
        sum(
            other not in validation_components and label in component_classes[other]
            for other in component_members
        ) > 1
        for label in component_classes[component]
    ):
        validation_components.add(component)

development_rows = []
component_for_row = {}
for component, members in component_members.items():
    for index, row in members:
        component_for_row[index] = component
        development_rows.append({
            **row,
            "image_path": str(
                resolved_paths[split_path_keys[row["image_path"]]].relative_to(PROJECT_ROOT.resolve())
            ),
            "split": "validation" if component in validation_components else "train",
            "development_component": str(component),
        })

dev_counts = defaultdict(Counter)
for row in development_rows:
    dev_counts[row["split"]][row["class_name"]] += 1
for part in ("train", "validation"):
    absent = [name for name in CLASS_ORDER if dev_counts[part][name] == 0]
    if absent:
        raise RuntimeError(f"Development {part} is missing classes: {absent}")
print("Development split counts:")
print(json.dumps({part: dict(dev_counts[part]) for part in ("train", "validation")}, indent=2))
print("Development connected groups:", len(component_members))
print("Rows with no patient/lesion/overlap identifier:", sum(
    not any(key[0] != "sha256" for key in available_identity_keys(row))
    for row in development_source
))

NOTEBOOK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEVELOPMENT_SPLIT_CSV = NOTEBOOK_OUTPUT_DIR / "development_split.csv"
fields = list(development_rows[0])
buffer = io.StringIO(newline="")
writer = csv.DictWriter(buffer, fieldnames=fields)
writer.writeheader()
writer.writerows(development_rows)
development_csv = buffer.getvalue()
buffer.close()
if DEVELOPMENT_SPLIT_CSV.exists():
    if DEVELOPMENT_SPLIT_CSV.read_bytes() != development_csv.encode("utf-8"):
        raise FileExistsError(
            f"Existing development split differs; refusing to overwrite: {DEVELOPMENT_SPLIT_CSV}"
        )
else:
    DEVELOPMENT_SPLIT_CSV.write_bytes(development_csv.encode("utf-8"))
print("Development split saved:", DEVELOPMENT_SPLIT_CSV)
print("Existing test partition remains untouched:", sum(r["split"] == "test" for r in split_rows), "rows")"""))

cells.append(markdown("""## 5. Model construction

Uses the actual `build_nine_class_egvan` implementation with no pretrained branch
downloads. Random initialization is the default. An optional baseline checkpoint
may be used only if `weights_only=True` loading and strict state-dict validation
pass."""))

cells.append(code("""# Cell 5 — Actual EG-VAN construction and smoke test
import torch.nn as nn
from torch.utils.data import DataLoader

INITIALIZE_FROM_OPTIONAL_BASELINE = False
model = build_nine_class_egvan(
    pretrained_efficient=False,
    pretrained_resnet=False,
    fusion_channels=128,
)

if INITIALIZE_FROM_OPTIONAL_BASELINE:
    from nine_class_dataset import PreprocessConfig, preprocessing_hash

    if not OPTIONAL_BASELINE_CHECKPOINT.is_file():
        raise FileNotFoundError(OPTIONAL_BASELINE_CHECKPOINT)
    baseline_sha256=hashlib.sha256(OPTIONAL_BASELINE_CHECKPOINT.read_bytes()).hexdigest()
    if baseline_sha256!=OPTIONAL_BASELINE_EXPECTED_SHA256:
        raise RuntimeError("Optional baseline checkpoint hash differs from the recorded SHA-256.")
    state = torch.load(OPTIONAL_BASELINE_CHECKPOINT, map_location="cpu", weights_only=True)
    if not isinstance(state,dict) or not isinstance(state.get("model_state"),dict):
        raise RuntimeError("Optional baseline is not a provenance-wrapped checkpoint.")
    run_provenance_path=OPTIONAL_BASELINE_CHECKPOINT.parent/"run_provenance.json"
    if not run_provenance_path.is_file():
        raise FileNotFoundError(run_provenance_path)
    run_provenance=json.loads(run_provenance_path.read_text(encoding="utf-8"))
    if run_provenance.get("research_status")!="EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION":
        raise RuntimeError("Optional baseline is not marked as exploratory research.")
    for key in ("config_sha256","split_sha256","preprocess_config_sha256"):
        if state.get(key)!=run_provenance.get(key):
            raise RuntimeError(f"Optional baseline checkpoint provenance mismatch: {key}")
    config_sha256=hashlib.sha256(TRAINING_CONFIG_JSON.read_bytes()).hexdigest()
    if config_sha256!=run_provenance.get("config_sha256"):
        raise RuntimeError("Optional baseline training configuration hash mismatch.")
    if run_provenance.get("config",{}).get("label_order")!=CLASS_ORDER:
        raise RuntimeError("Optional baseline provenance class order mismatch.")
    baseline_preprocessing=PreprocessConfig(
        image_size=IMAGE_SIZE,
        pipeline_version=preprocessing["pipeline_version"],
    )
    if preprocessing_hash(baseline_preprocessing)!=run_provenance.get("preprocess_config_sha256"):
        raise RuntimeError("Optional baseline preprocessing hash mismatch.")
    model_state=state["model_state"]
    result = model.load_state_dict(model_state, strict=True)
    if getattr(result, "missing_keys", None) or getattr(result, "unexpected_keys", None):
        raise RuntimeError(f"Baseline checkpoint mismatch: {result}")
    print("Optional baseline loaded strictly:", OPTIONAL_BASELINE_CHECKPOINT)
else:
    print("Random initialization used; no pretrained weights downloaded.")

model = model.cuda()
model.train()

sample = torch.randn(2, 3, IMAGE_SIZE, IMAGE_SIZE, device="cuda")
target = torch.tensor([0, 8], dtype=torch.long, device="cuda")
model.zero_grad(set_to_none=True)
logits = model(sample)
if tuple(logits.shape) != (2, 9):
    raise RuntimeError(f"Expected (2,9) logits; got {tuple(logits.shape)}")
loss = nn.functional.cross_entropy(logits, target)
loss.backward()
parameter_count = sum(p.numel() for p in model.parameters())
grad_count = sum(p.grad is not None for p in model.parameters())
finite_gradients = sum(
    torch.isfinite(p.grad).all().item()
    for p in model.parameters()
    if p.grad is not None
)
print("Parameters:", parameter_count)
print("Logit shape:", tuple(logits.shape))
print("Gradients:", grad_count, "finite:", finite_gradients)
if not torch.isfinite(logits).all() or grad_count != finite_gradients:
    raise RuntimeError("CUDA forward/backward smoke test failed.")
del sample, target, logits, loss
torch.cuda.empty_cache()"""))

cells.append(markdown("""## 6. Baseline experiment

The baseline mirrors the existing configuration closely: 384 pixels, random
initialization unless locally baseline initialization is explicitly enabled,
Adamax, focal loss, microbatch 8, accumulation 4 and 25 epochs. It uses the
separate development split and saves every validation probability."""))

cells.append(code("""# Cell 6 — Data loader, preprocessing and baseline helpers
import random
from collections import Counter
from nine_class_dataset import NineClassDataset, PreprocessConfig

SEED = 42

def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

development_rows = read_csv(DEVELOPMENT_SPLIT_CSV)
train_rows = [row for row in development_rows if row["split"] == "train"]
validation_rows = [row for row in development_rows if row["split"] == "validation"]
print("Development train:", len(train_rows), "development validation:", len(validation_rows))
if not train_rows or not validation_rows:
    raise RuntimeError("Development partitions are empty")

preprocess_config = PreprocessConfig(
    image_size=IMAGE_SIZE,
    mean=MEAN,
    std=STD,
    pipeline_version=preprocessing["pipeline_version"],
)
train_dataset = NineClassDataset(
    PROJECT_ROOT, DEVELOPMENT_SPLIT_CSV, "train", preprocess_config,
    augmentation_seed=SEED,
)
validation_dataset = NineClassDataset(
    PROJECT_ROOT, DEVELOPMENT_SPLIT_CSV, "validation", preprocess_config,
)

train_counts = Counter(row["class_name"] for row in train_rows)
class_weights = torch.tensor(
    [len(train_rows) / (9 * train_counts[name]) for name in CLASS_ORDER],
    dtype=torch.float32,
)
print("Train-only inverse-frequency class weights:", class_weights.tolist())

MICROBATCH = 8
ACCUMULATION = 4
EPOCHS = int(training_config["epochs"])
SEED = 42

seed_everything(SEED)
"""))

cells.append(markdown("""## 7. Controlled imbalance experiments

The notebook supports separate, controlled variants:

- standard cross-entropy
- train-only class-weighted cross-entropy
- weighted sampling with cross-entropy
- focal loss

Each run uses the same development split and model dataflow."""))

cells.append(code("""# Cell 7 — Loss and sampling experiment functions
def focal_loss(logits, targets, alpha=None, gamma=None, weights=None):
    alpha=float(training_config["focal_alpha"]) if alpha is None else alpha
    gamma=float(training_config["focal_gamma"]) if gamma is None else gamma
    ce = nn.functional.cross_entropy(logits.float(), targets, reduction="none")
    loss = alpha * (1 - (-ce).exp()).pow(gamma) * ce
    if weights is not None:
        loss = loss * weights.to(logits.device)[targets]
    return loss.mean()

def build_loss_fn(loss_name, weighted_tensor=None):
    if loss_name == "cross_entropy":
        return lambda logits, targets: nn.functional.cross_entropy(logits, targets)
    if loss_name == "weighted_cross_entropy":
        return lambda logits, targets: nn.functional.cross_entropy(
            logits, targets, weight=weighted_tensor.to(logits.device)
        )
    if loss_name == "focal":
        return lambda logits, targets: focal_loss(logits, targets)
    raise ValueError(loss_name)

train_samples = Counter(row["class_name"] for row in train_rows)
sampler_weights = []
for row in train_rows:
    sampler_weights.append(1.0 / train_samples[row["class_name"]])
print("Weighted-sampling weights calculated from training labels only.",
      "Sampler sample count:", len(sampler_weights))"""))

cells.append(markdown("""## 8. Training improvements and resume

The runner uses CUDA AMP, gradient accumulation, gradient clipping, cosine or
reduce-on-plateau scheduling, early stopping, and checkpoints after each epoch.
Checkpoints are stored in Google Drive. No GPU memory size is assumed."""))

cells.append(code("""# Cell 8 — Bounded GPU training implementation
from torch.utils.data import WeightedRandomSampler
from torch.optim import Adamax, AdamW

IMBALANCE_EXPERIMENTS = [
    {"id":"A_ce","loss":"cross_entropy","sampler":False,"lr":float(training_config["learning_rate"]),"optimizer":"adamax","scheduler":"plateau"},
    {"id":"B_weighted_ce","loss":"weighted_cross_entropy","sampler":False,"lr":float(training_config["learning_rate"]),"optimizer":"adamax","scheduler":"plateau"},
    {"id":"C_weighted_sampling","loss":"cross_entropy","sampler":True,"lr":float(training_config["learning_rate"]),"optimizer":"adamax","scheduler":"plateau"},
    {"id":"D_focal","loss":"focal","sampler":False,"lr":float(training_config["learning_rate"]),"optimizer":"adamax","scheduler":"plateau"},
]

RUN_TRAINING = False
AUTHORIZE_EXPLORATORY_TRAINING = False
CONFIRM_TRAINING_AFTER_BENCHMARK = False
RUN_RESUME = False
RESUME_CHECKPOINT = None
EXPERIMENT_RUN_ID = "run_001"
SELECTED_EXPERIMENTS = ["D_focal"]
MAX_EPOCHS_OVERRIDE = None
COLLAPSE_PREDICTION_LIMIT = 0.90
EXPERIMENT_OUTPUT_ROOT = NOTEBOOK_OUTPUT_DIR / "experiments"
EXPERIMENT_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

def metrics_from_outputs(probabilities, targets):
    probabilities = np.asarray(probabilities, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.int64)
    predicted = probabilities.argmax(axis=1)
    matrix = np.zeros((9,9), dtype=np.int64)
    np.add.at(matrix, (targets,predicted),1)
    support = matrix.sum(axis=1)
    predicted_count = matrix.sum(axis=0)
    true_positive = matrix.diagonal()
    precision = np.divide(true_positive,predicted_count,out=np.zeros(9),where=predicted_count>0)
    recall = np.divide(true_positive,support,out=np.zeros(9),where=support>0)
    f1 = np.divide(2*precision*recall,precision+recall,out=np.zeros(9),where=(precision+recall)>0)
    balanced = float(recall.mean())
    return {
        "n_samples": int(len(targets)),
        "accuracy": float((predicted==targets).mean()),
        "macro_f1": float(f1.mean()),
        "weighted_f1": float(np.average(f1,weights=support)),
        "balanced_accuracy": balanced,
        "per_class": {name:{
            "precision":float(precision[i]),
            "recall":float(recall[i]),
            "f1":float(f1[i]),
            "support":int(support[i]),
        } for i,name in enumerate(CLASS_ORDER)},
        "confusion_matrix":matrix.tolist(),
        "prediction_distribution":{name:int(predicted_count[i]) for i,name in enumerate(CLASS_ORDER)},
    }

def evaluate_model(model, dataset, batch_size=MICROBATCH):
    loader = DataLoader(
        dataset, batch_size=batch_size, shuffle=False,
        num_workers=int(training_config["num_workers"]), pin_memory=True,
    )
    model.eval()
    probabilities=[]; targets=[]; image_paths=[]
    with torch.inference_mode():
        with torch.amp.autocast("cuda", enabled=True):
            for images, labels in loader:
                logits=model(images.cuda())
                if tuple(logits.shape)!=(len(labels),len(CLASS_ORDER)):
                    raise RuntimeError(f"Unexpected validation logit shape: {tuple(logits.shape)}")
                if not torch.isfinite(logits).all().item():
                    raise RuntimeError("Validation logits contain non-finite values.")
                batch_probabilities=torch.softmax(logits.float(),dim=1)
                probabilities.append(batch_probabilities.cpu().numpy())
                targets.extend(labels.numpy().tolist())
    probability_array=np.concatenate(probabilities)
    target_array=np.asarray(targets,dtype=np.int64)
    if not np.isfinite(probability_array).all():
        raise RuntimeError("Validation probabilities contain non-finite values.")
    if not np.allclose(probability_array.sum(axis=1),1.0,rtol=0.0,atol=1e-6):
        raise RuntimeError("Validation probabilities do not sum to one.")
    metrics=metrics_from_outputs(probability_array,target_array)
    metrics["probabilities"]=probability_array
    metrics["targets"]=target_array
    return metrics

def configure_model_eval(model):
    model.eval()

if RUN_TRAINING:
    if not AUTHORIZE_EXPLORATORY_TRAINING:
        raise RuntimeError("Set AUTHORIZE_EXPLORATORY_TRAINING=True before real GPU training.")
    if not torch.cuda.is_available():
        raise RuntimeError("GPU training requires CUDA.")

    benchmark_model = build_nine_class_egvan(
        pretrained_efficient=False, pretrained_resnet=False, fusion_channels=128
    ).cuda()
    benchmark_model.train()
    benchmark_images = torch.randn(MICROBATCH,3,IMAGE_SIZE,IMAGE_SIZE,device="cuda")
    benchmark_targets = torch.randint(0,9,(MICROBATCH,),device="cuda")
    torch.cuda.synchronize()
    started=time.time()
    benchmark_logits=benchmark_model(benchmark_images)
    benchmark_loss=nn.functional.cross_entropy(benchmark_logits,benchmark_targets)
    benchmark_loss.backward()
    torch.cuda.synchronize()
    batch_seconds=time.time()-started
    print("Microbatch benchmark seconds:", round(batch_seconds,3))
    benchmark_steps=int(np.ceil(len(train_rows)/MICROBATCH))
    benchmark_epochs=EPOCHS if MAX_EPOCHS_OVERRIDE is None else int(MAX_EPOCHS_OVERRIDE)
    print(
        "Rough training-only duration (excludes validation, data I/O, and checkpoint "
        "overhead; not a guarantee), hours:",
        round(batch_seconds*benchmark_steps*benchmark_epochs/3600,2),
    )
    del benchmark_model, benchmark_images, benchmark_targets, benchmark_logits, benchmark_loss
    torch.cuda.empty_cache()
else:
    print("Training remains disabled. Set RUN_TRAINING=True and authorize explicitly.")"""))

cells.append(markdown("""## 9. Experiment comparison

The experiment loop below writes a separate register entry and history for every
model. Selection uses validation macro-F1 and balanced accuracy, while penalizing
majority-class collapse; accuracy alone is not sufficient. A checkpoint is
rejected for selection if any one predicted class accounts for at least 90% of
validation predictions."""))

cells.append(code("""# Cell 9 — Run controlled experiments and compare
experiment_register = []

def train_one_experiment(experiment):
    experiment_id=experiment["id"]
    experiment_dir=EXPERIMENT_OUTPUT_ROOT/experiment_id/EXPERIMENT_RUN_ID
    if RUN_RESUME:
        resume_path=Path(RESUME_CHECKPOINT) if RESUME_CHECKPOINT else None
        if resume_path is None or not resume_path.is_file():
            raise FileNotFoundError("Set RESUME_CHECKPOINT to the exact persistent last.pt.")
        if resume_path.resolve() != (experiment_dir/"last.pt").resolve():
            raise RuntimeError("Resume checkpoint must be this experiment run's last.pt.")
    elif experiment_dir.exists() and any(experiment_dir.iterdir()):
        raise FileExistsError(
            f"Run directory already contains outputs: {experiment_dir}. "
            "Choose a new EXPERIMENT_RUN_ID or resume its last.pt."
        )
    experiment_dir.mkdir(parents=True,exist_ok=True)
    seed_everything(SEED)
    model=build_nine_class_egvan(
        pretrained_efficient=False,
        pretrained_resnet=False,
        fusion_channels=128,
    ).cuda()
    if experiment["optimizer"]=="adamw":
        optimizer=AdamW(model.parameters(),lr=experiment["lr"],weight_decay=1e-4)
    else:
        optimizer=Adamax(model.parameters(),lr=experiment["lr"])
    if experiment["scheduler"]=="plateau":
        scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=float(training_config["scheduler"]["factor"]),
            patience=int(training_config["scheduler"]["patience"]),
        )
    else:
        scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=EPOCHS)

    loader_generator=torch.Generator().manual_seed(SEED)
    train_dataset.set_epoch(0)
    val_dataset=validation_dataset
    if experiment["sampler"]:
        sampler=WeightedRandomSampler(
            torch.tensor(sampler_weights,dtype=torch.float32),
            num_samples=len(sampler_weights),
            replacement=True,
            generator=loader_generator,
        )
        train_loader=DataLoader(train_dataset,batch_size=MICROBATCH,shuffle=False,
                                sampler=sampler,
                                num_workers=int(training_config["num_workers"]),
                                pin_memory=True,generator=loader_generator)
    else:
        generator=loader_generator
        train_loader=DataLoader(train_dataset,batch_size=MICROBATCH,shuffle=True,
                                generator=generator,
                                num_workers=int(training_config["num_workers"]),
                                pin_memory=True)
    loss_fn=build_loss_fn(experiment["loss"],class_weights)
    scaler=torch.amp.GradScaler("cuda",enabled=True)

    def atomic_torch_save(value,path):
        temporary=path.with_suffix(path.suffix+".tmp")
        torch.save(value,temporary)
        os.replace(temporary,path)

    def atomic_csv_save(frame,path):
        temporary=path.with_suffix(path.suffix+".tmp")
        frame.to_csv(temporary,index=False)
        os.replace(temporary,path)

    def atomic_json_save(value,path):
        temporary=path.with_suffix(path.suffix+".tmp")
        temporary.write_text(json.dumps(value,indent=2),encoding="utf-8")
        os.replace(temporary,path)

    history=[]
    history_path=experiment_dir/"training_history.csv"
    if not RUN_RESUME and history_path.exists():
        raise FileExistsError(f"History already exists; choose a fresh run ID: {history_path}")
    best_score=-float("inf")
    best_epoch=0
    bad_epochs=0
    epochs=EPOCHS if MAX_EPOCHS_OVERRIDE is None else int(MAX_EPOCHS_OVERRIDE)
    start_epoch=0
    run_fingerprint=hashlib.sha256(json.dumps({
        "experiment":experiment,
        "development_split_sha256":hashlib.sha256(DEVELOPMENT_SPLIT_CSV.read_bytes()).hexdigest(),
        "training_config":training_config,
        "preprocessing":preprocessing,
        "class_order":CLASS_ORDER,
        "seed":SEED,
        "microbatch":MICROBATCH,
        "accumulation":ACCUMULATION,
    },sort_keys=True).encode("utf-8")).hexdigest()

    if RUN_RESUME:
        resume_state=torch.load(resume_path,map_location="cpu",weights_only=True)
        if resume_state.get("experiment",{}).get("id") != experiment_id:
            raise RuntimeError("Resume experiment ID does not match the selected experiment.")
        if resume_state.get("run_fingerprint") != run_fingerprint:
            raise RuntimeError(
                "Resume configuration, preprocessing, or development split differs from the saved run."
            )
        model.load_state_dict(resume_state["model_state"],strict=True)
        optimizer.load_state_dict(resume_state["optimizer_state"])
        scheduler.load_state_dict(resume_state["scheduler_state"])
        scaler.load_state_dict(resume_state["scaler_state"])
        loader_generator.set_state(resume_state["loader_generator_state"])
        torch.set_rng_state(resume_state["torch_rng_state"])
        torch.cuda.set_rng_state_all(resume_state["cuda_rng_states"])
        start_epoch=int(resume_state["epoch"])
        history=list(resume_state["history"])
        best_score=float(resume_state["best_selection_score"])
        best_epoch=int(resume_state["best_epoch"])
        bad_epochs=int(resume_state["bad_epochs"])
        if not history or int(history[-1]["epoch"]) != start_epoch:
            raise RuntimeError("Checkpoint history does not end at its saved epoch.")
        best_path=experiment_dir/"best.pt"
        if best_epoch == 0:
            if best_path.exists():
                raise RuntimeError("Run has a best checkpoint but no accepted best epoch.")
        elif not best_path.is_file():
            atomic_torch_save(resume_state,best_path)
        else:
            best_state=torch.load(best_path,map_location="cpu",weights_only=True)
            if float(best_state.get("best_selection_score",-float("inf"))) < best_score:
                atomic_torch_save(resume_state,best_path)
        if resume_state.get("validation_metrics") and resume_state.get("validation_predictions"):
            atomic_json_save(resume_state["validation_metrics"],experiment_dir/"last_metrics.json")
            atomic_csv_save(
                pd.DataFrame(resume_state["validation_predictions"]),
                experiment_dir/"last_validation_predictions.csv",
            )
        print("Resuming",experiment_id,"after epoch",start_epoch)
    elif (experiment_dir/"last.pt").exists() or (experiment_dir/"best.pt").exists():
        raise FileExistsError(
            f"Checkpoint already exists in {experiment_dir}; resume it or select a new run ID."
        )
    if epochs <= start_epoch:
        raise ValueError(f"Requested epoch limit {epochs} is not after saved epoch {start_epoch}.")

    for epoch in range(start_epoch+1,epochs+1):
        train_dataset.set_epoch(epoch)
        model.train()
        for module in model.modules():
            if isinstance(module,(nn.BatchNorm1d,nn.BatchNorm2d,nn.BatchNorm3d)):
                module.eval()
        optimizer.zero_grad(set_to_none=True)
        train_loss=0.0
        train_samples_seen=0
        total_batches=len(train_loader)
        for batch_index,(images,targets) in enumerate(train_loader):
            images=images.cuda(non_blocking=True)
            targets=targets.cuda(non_blocking=True)
            with torch.amp.autocast("cuda",enabled=True):
                logits=model(images)
                loss=loss_fn(logits,targets)
            if not torch.isfinite(loss.detach()).all().item():
                raise RuntimeError(f"Non-finite training loss at epoch {epoch}, batch {batch_index}.")
            window_start=(batch_index//ACCUMULATION)*ACCUMULATION
            window_end=min(window_start+ACCUMULATION,total_batches)
            window_samples=sum(
                min(MICROBATCH,len(train_rows)-batch_number*MICROBATCH)
                for batch_number in range(window_start,window_end)
            )
            scaler.scale(loss*(len(targets)/window_samples)).backward()
            train_loss+=(float(loss.detach())*len(targets))
            train_samples_seen+=len(targets)
            if (batch_index+1)%ACCUMULATION==0 or batch_index+1==total_batches:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    float(training_config["gradient_clip_norm"]),
                    error_if_nonfinite=True,
                )
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
        if train_samples_seen != len(train_rows):
            raise RuntimeError(
                f"Training loader yielded {train_samples_seen} samples, expected {len(train_rows)}."
            )
        train_loss/=max(train_samples_seen,1)
        val_metrics=evaluate_model(model,val_dataset)
        val_probs=val_metrics.pop("probabilities")
        val_targets=val_metrics.pop("targets")
        val_predictions=np.asarray(val_probs).argmax(axis=1)
        val_loss=0.0
        val_loader=DataLoader(
            val_dataset,batch_size=MICROBATCH,shuffle=False,
            num_workers=int(training_config["num_workers"]),pin_memory=True,
        )
        model.eval()
        with torch.inference_mode():
            for images,targets in val_loader:
                with torch.amp.autocast("cuda",enabled=True):
                    logits=model(images.cuda())
                    val_loss+=float(nn.functional.cross_entropy(logits,targets.cuda()).detach())*len(targets)
        val_loss/=len(val_dataset)
        max_predicted_fraction=max(val_metrics["prediction_distribution"].values())/len(val_dataset)
        selection_score=val_metrics["macro_f1"]+val_metrics["balanced_accuracy"]-0.5*max_predicted_fraction
        majority_collapse_rejected=max_predicted_fraction>=COLLAPSE_PREDICTION_LIMIT
        if isinstance(scheduler,torch.optim.lr_scheduler.ReduceLROnPlateau):
            scheduler.step(val_loss)
        else:
            scheduler.step()
        improved=(not majority_collapse_rejected) and selection_score>best_score
        if improved:
            best_score=selection_score
            best_epoch=epoch
            bad_epochs=0
        else:
            bad_epochs+=1

        row={
            "experiment_id":experiment_id,
            "epoch":epoch,
            "train_loss":train_loss,
            "validation_loss":val_loss,
            "accuracy":val_metrics["accuracy"],
            "macro_f1":val_metrics["macro_f1"],
            "weighted_f1":val_metrics["weighted_f1"],
            "balanced_accuracy":val_metrics["balanced_accuracy"],
            "max_predicted_class_fraction":max_predicted_fraction,
            "majority_collapse_rejected":majority_collapse_rejected,
            "selection_score":selection_score,
            "learning_rate":optimizer.param_groups[0]["lr"],
            "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
        }
        history.append(row)
        val_metrics.update({
            "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
            "validation_loss":val_loss,
            "checkpoint_epoch":epoch,
            "majority_collapse_rejected":majority_collapse_rejected,
        })
        prediction_rows=[{
            "image_path":sample_row["image_path"],
            "source_dataset":sample_row.get("source_dataset",""),
            "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
            "target_index":int(sample_row["class_index"]),
            "predicted_index":int(val_predictions[index]),
            **{f"prob_{name}":float(val_probs[index,i]) for i,name in enumerate(CLASS_ORDER)}
        } for index,sample_row in enumerate(validation_rows)]

        state={
            "model_state":model.state_dict(),
            "epoch":epoch,
            "best_validation_loss":val_loss,
            "experiment":experiment,
            "optimizer_state":optimizer.state_dict(),
            "scheduler_state":scheduler.state_dict(),
            "scaler_state":scaler.state_dict(),
            "class_order":CLASS_ORDER,
            "preprocessing_config":preprocessing,
            "seed":SEED,
            "selection_score":selection_score,
            "best_selection_score":best_score,
            "best_epoch":best_epoch,
            "bad_epochs":bad_epochs,
            "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
            "run_fingerprint":run_fingerprint,
            "loader_generator_state":loader_generator.get_state(),
            "torch_rng_state":torch.get_rng_state(),
            "cuda_rng_states":torch.cuda.get_rng_state_all(),
            "history":history,
            "validation_metrics":val_metrics,
            "validation_predictions":prediction_rows,
            "max_predicted_class_fraction":max_predicted_fraction,
        }
        atomic_torch_save(state,experiment_dir/"last.pt")
        atomic_json_save(val_metrics,experiment_dir/"last_metrics.json")
        atomic_csv_save(
            pd.DataFrame(prediction_rows),
            experiment_dir/"last_validation_predictions.csv",
        )
        if improved:
            atomic_torch_save(state,experiment_dir/"best.pt")
            atomic_csv_save(
                pd.DataFrame(prediction_rows),
                experiment_dir/"validation_predictions.csv",
            )
            atomic_json_save(val_metrics,experiment_dir/"metrics.json")
        atomic_csv_save(pd.DataFrame(history),history_path)
        print(json.dumps(row))
        early_stopping=training_config["early_stopping"]
        if early_stopping["enabled"] and bad_epochs>=int(early_stopping["patience"]):
            print("Early stopping after",epoch,"epochs")
            break
    return {
        "experiment_id":experiment_id,
        "run_id":EXPERIMENT_RUN_ID,
        "status":"complete" if best_epoch else "rejected_majority_collapse",
        "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
        "best_epoch":best_epoch,
        "best_selection_score":best_score if best_epoch else None,
        "output_dir":str(experiment_dir),
    }

if RUN_TRAINING:
    selected=[exp for exp in IMBALANCE_EXPERIMENTS if exp["id"] in SELECTED_EXPERIMENTS]
    if not selected:
        raise RuntimeError("SELECTED_EXPERIMENTS is empty.")
    if not CONFIRM_TRAINING_AFTER_BENCHMARK:
        raise RuntimeError(
            "Review the Cell 8 benchmark estimate, then set "
            "CONFIRM_TRAINING_AFTER_BENCHMARK=True before starting training."
        )
    if RUN_RESUME and len(selected)!=1:
        raise RuntimeError("Resume exactly one experiment at a time.")
    register=[]
    for experiment in selected:
        register.append(train_one_experiment(experiment))
    register_path=NOTEBOOK_OUTPUT_DIR/f"experiment_register_{EXPERIMENT_RUN_ID}.csv"
    if register_path.exists():
        raise FileExistsError(f"Experiment register already exists: {register_path}")
    pd.DataFrame(register).to_csv(register_path,index=False)
    print(json.dumps(register,indent=2))
else:
    print("Controlled experiment loop remains disabled.")"""))

cells.append(markdown("""## 10. Final evaluation

The selected checkpoint is frozen and evaluated on the newly generated
development-validation partition. The historical test partition is marked
NOT_APPROVED, so this notebook deliberately blocks its evaluation."""))

cells.append(code("""# Cell 10 — Freeze and evaluate selected checkpoint

def export_partition_outputs(partition_name, rows, probs, targets, metrics):
    predictions=probs.argmax(axis=1)
    FINAL_OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    classification_rows=[]
    for name in CLASS_ORDER:
        i=CLASS_ORDER.index(name)
        classification_rows.append({
            "class_name":name,
            "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
            "precision":metrics["per_class"][name]["precision"],
            "recall":metrics["per_class"][name]["recall"],
            "f1":metrics["per_class"][name]["f1"],
            "support":metrics["per_class"][name]["support"],
        })
    pd.DataFrame(classification_rows).to_csv(
        FINAL_OUTPUT_DIR/f"{partition_name}_classification_report.csv",index=False
    )
    pd.DataFrame(
        metrics["confusion_matrix"],
        index=CLASS_ORDER,
        columns=CLASS_ORDER,
    ).to_csv(FINAL_OUTPUT_DIR/f"{partition_name}_confusion_matrix.csv")
    import matplotlib.pyplot as plt
    figure,axis=plt.subplots(figsize=(8,8))
    matrix=np.asarray(metrics["confusion_matrix"],dtype=np.int64)
    axis.imshow(matrix,cmap="Blues")
    axis.set_xticks(range(9),CLASS_ORDER,rotation=45,ha="right")
    axis.set_yticks(range(9),CLASS_ORDER)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("True")
    for true_index in range(9):
        for predicted_index in range(9):
            axis.text(predicted_index,true_index,str(matrix[true_index,predicted_index]),
                      ha="center",va="center",fontsize=7)
    figure.tight_layout()
    figure.savefig(FINAL_OUTPUT_DIR/f"{partition_name}_confusion_matrix.png",dpi=150)
    plt.close(figure)

    probability_rows=[]
    for index,row in enumerate(rows):
        probability_rows.append({
            "image_path":row["image_path"],
            "source_dataset":row.get("source_dataset",""),
            "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
            "target_index":int(targets[index]),
            "predicted_index":int(predictions[index]),
            **{f"prob_{name}":float(probs[index,i]) for i,name in enumerate(CLASS_ORDER)}
        })
    pd.DataFrame(probability_rows).to_csv(
        FINAL_OUTPUT_DIR/f"{partition_name}_predictions.csv",index=False
    )
    pd.DataFrame(probability_rows).to_csv(
        FINAL_OUTPUT_DIR/f"{partition_name}_probabilities.csv",index=False
    )

SELECTED_CHECKPOINT = None
RUN_FINAL_TEST = False
SELECTED_RUN_LABEL = (
    Path(SELECTED_CHECKPOINT).parent.name if SELECTED_CHECKPOINT is not None else "unset"
)
FINAL_OUTPUT_DIR = NOTEBOOK_OUTPUT_DIR/"final_evaluation"/SELECTED_RUN_LABEL

if RUN_FINAL_TEST:
    raise RuntimeError(
        "The historical test partition is NOT_APPROVED and cannot be evaluated by this notebook."
    )

if SELECTED_CHECKPOINT is not None:
    checkpoint_path=Path(SELECTED_CHECKPOINT)
    if not checkpoint_path.is_file():
        raise FileNotFoundError(checkpoint_path)
    state=torch.load(checkpoint_path,map_location="cpu",weights_only=True)
    if state.get("class_order")!=CLASS_ORDER:
        raise RuntimeError("Selected checkpoint class order differs from the nine-class output.")
    if state.get("preprocessing_config")!=preprocessing:
        raise RuntimeError("Selected checkpoint preprocessing differs from the verified config.")
    if state.get("research_status")!="EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION":
        raise RuntimeError("Selected checkpoint lacks the expected exploratory research status.")
    if float(state.get("max_predicted_class_fraction",1.0))>=COLLAPSE_PREDICTION_LIMIT:
        raise RuntimeError("Selected checkpoint was rejected for majority-class collapse.")
    model=build_nine_class_egvan(
        pretrained_efficient=False,
        pretrained_resnet=False,
        fusion_channels=128,
    )
    model.load_state_dict(state["model_state"],strict=True)
    model.cuda().eval()
    val_metrics=evaluate_model(model,validation_dataset)
    val_probs=val_metrics.pop("probabilities")
    val_targets=val_metrics.pop("targets")
    val_metrics["evaluation_partition"]="development_validation"
    val_metrics["research_status"]="EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION"
    val_metrics["checkpoint_epoch"]=int(state["epoch"])
    val_metrics["validation_loss"]=float(state["best_validation_loss"])
    (FINAL_OUTPUT_DIR).mkdir(parents=True,exist_ok=True)
    (FINAL_OUTPUT_DIR/"validation_metrics.json").write_text(json.dumps(val_metrics,indent=2))
    export_partition_outputs("validation",validation_rows,val_probs,val_targets,val_metrics)
    print(json.dumps(val_metrics,indent=2))

    print("Historical test partition remains untouched and unevaluated.")
else:
    print("SELECTED_CHECKPOINT is not set; validation/final evaluation remains disabled.")"""))

cells.append(markdown("""## 11. Checkpoint export

Exports a strict-loadable research checkpoint and metadata. It does **not**
replace or satisfy the existing Streamlit loader's frozen-checkpoint hash and
provenance checks; do not use this export for public inference without a separate
review and explicit loader update."""))

cells.append(code("""# Cell 11 — Export research checkpoint and metadata
EXPORT_DIR = NOTEBOOK_OUTPUT_DIR/"exports"/SELECTED_RUN_LABEL
EXPORT_DIR.mkdir(parents=True,exist_ok=True)

if SELECTED_CHECKPOINT is not None:
    checkpoint_path=Path(SELECTED_CHECKPOINT)
    state=torch.load(checkpoint_path,map_location="cpu",weights_only=True)
    model_config={
        "architecture":"EG-VAN nine-class",
        "num_classes":9,
        "fusion_channels":128,
        "pretrained_efficient":False,
        "pretrained_resnet":False,
        "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
        "selected_experiment":state.get("experiment"),
        "selection_score":state.get("selection_score"),
    }
    class_mapping={name:index for index,name in enumerate(CLASS_ORDER)}
    model_output=EXPORT_DIR/"best_model.pt"
    export_state={
        "model_state":state["model_state"],
        "class_order":CLASS_ORDER,
        "preprocessing_config":preprocessing,
        "model_config":model_config,
        "research_status":"EXPLORATORY_ONLY_NONCLINICAL_NOT_PAPER_REPRODUCTION",
        "max_predicted_class_fraction":state["max_predicted_class_fraction"],
        "source_checkpoint_sha256":hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
    }
    torch.save(export_state,model_output)

    (EXPORT_DIR/"model_config.json").write_text(json.dumps(model_config,indent=2))
    (EXPORT_DIR/"class_mapping.json").write_text(json.dumps(class_mapping,indent=2))
    (EXPORT_DIR/"preprocessing_config.json").write_text(json.dumps(preprocessing,indent=2))
    (EXPORT_DIR/"metrics.json").write_text(json.dumps(val_metrics,indent=2))
    source_experiment_dir=checkpoint_path.parent
    for filename in ("training_history.csv","validation_predictions.csv","metrics.json"):
        source=source_experiment_dir/filename
        if source.is_file():
            shutil.copy2(source,EXPORT_DIR/filename)
    for filename in (
        f"experiment_register_{EXPERIMENT_RUN_ID}.csv",
    ):
        source=NOTEBOOK_OUTPUT_DIR/filename
        if source.is_file():
            shutil.copy2(source,EXPORT_DIR/filename)
    for filename in (
        "validation_classification_report.csv",
        "validation_confusion_matrix.csv",
        "validation_confusion_matrix.png",
        "validation_probabilities.csv",
    ):
        source=FINAL_OUTPUT_DIR/filename
        if source.is_file():
            shutil.copy2(source,EXPORT_DIR/filename)

    checkpoint_sha=hashlib.sha256(model_output.read_bytes()).hexdigest()
    print("Exported checkpoint:", model_output)
    print("Checkpoint SHA-256:", checkpoint_sha)
    (EXPORT_DIR/"checkpoint_sha256.txt").write_text(checkpoint_sha+"\\n")
else:
    print("No export produced; SELECTED_CHECKPOINT is unset.")"""))

cells.append(markdown("""## 12. Download results

Creates `EG_VAN_COLAB_RESULTS.zip` containing experiment registers, histories,
metrics, predictions, class reports and research checkpoints where available."""))

cells.append(code("""# Cell 12 — Package and download results
from google.colab import files

RESULTS_ZIP=DRIVE_OUTPUT_DIR/"EG_VAN_COLAB_RESULTS.zip"
if RESULTS_ZIP.exists():
    RESULTS_ZIP=DRIVE_OUTPUT_DIR/f"EG_VAN_COLAB_RESULTS_{time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())}.zip"
if RESULTS_ZIP.exists():
    raise FileExistsError(f"Refusing to overwrite an existing results archive: {RESULTS_ZIP}")
readme=NOTEBOOK_OUTPUT_DIR/"README.txt"
readme.write_text(
    "EG-VAN COLAB RESULTS\\n"
    "EXPLORATORY / NON-CLINICAL / NOT APPROVED\\n"
    "NOT AN EXACT EG-VAN PAPER REPRODUCTION.\\n"
    "The historical test partition was not evaluated.\\n"
    "No 80% result is claimed unless measured and recorded in metrics.json.\\n"
)
output_files=[
    path for path in NOTEBOOK_OUTPUT_DIR.rglob("*")
    if path.is_file() and path!=RESULTS_ZIP and not path.name.endswith(".tmp")
]
with zipfile.ZipFile(RESULTS_ZIP,"w",compression=zipfile.ZIP_DEFLATED) as archive:
    for path in output_files:
        archive.write(path,path.relative_to(DRIVE_OUTPUT_DIR))
files.download(str(RESULTS_ZIP))
print("Results archive:", RESULTS_ZIP)
print("Included files:", len(output_files))"""))

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUTPUT.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
print(OUTPUT)
