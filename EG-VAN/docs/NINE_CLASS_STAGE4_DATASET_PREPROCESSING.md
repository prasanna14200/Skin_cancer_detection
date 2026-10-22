# Stage 4: nine-class source manifest and preprocessing interface

## Status and scope

Stage 4 implements a **source inventory and a gated nine-label data interface**, not a final eligible cohort or evaluation split. The fixed output order is `AKIEC=0, BCC=1, BKL=2, DF=3, MEL=4, NV=5, VASC=6, BENIGN=7, MALIGNANT=8`. This numeric encoding is an explicit **local adaptation** because the paper's exact encoding was not recovered. These are seven HAM diagnoses plus two Fanconic source labels; they are not nine mutually exclusive clinical diagnoses. HAM labels are not remapped to the Fanconic classes.

The manifest generator reads the 10,015 HAM original JPEGs listed by `data/raw/HAM10000_metadata.csv` and the 3,297 JPEGs beneath **only** `data/isic/data/{train,test}/{benign,malignant}`. The mirrored `data/isic/{train,test}` tree is not traversed. Each path is source-qualified and has a newly calculated SHA-256, source label, class index, available HAM image and lesion IDs, Fanconic source partition, overlap graph ID, evidence tiers, and a provisional status. Blank Fanconic image, lesion, and patient IDs mean unknown; numerical file stems are not invented IDs. No raw image is changed.

`analysis/nine_class_stage4/nine_class_source_manifest.csv` is the full **13,312-row inventory**, including disputed records. It is not a training manifest. `analysis/nine_class_stage4/split_eligibility_audit.json` records source counts, provisional statuses, input evidence hashes and the split gate. Earlier proposed exclusions remain proposals and are labeled `PRIOR_PROPOSED_EXCLUSION_NOT_APPROVED`, never silently applied. `AI_SAME_PHOTO_QUARANTINE` and `AI_UNCERTAIN_QUARANTINE` are separate from independent verification. The original Fanconic test partition is labeled `PROTECTED_SOURCE_TEST_UNADJUDICATED`; linked HAM/source-train records are quarantined from a prospective training pool. The transitive graph joins Stage 3I prior/AI/suspected relations and all HAM photos sharing a recorded lesion ID. Graph membership is a leakage-control precaution, not patient identity proof.

## Split decision

No final train, validation or test split is generated. Train/validation/test counts are **zero assigned**, not zero available. The [Stage 3I review](NINE_CLASS_STAGE3I_AI_REVIEW.md) left only 83 provisionally retained BENIGN entries (64 source train, 19 source test), and each has an AI-supported same-photo HAM candidate. The 19 protected source-test candidates make a defensible nine-class test unavailable. Treating all 83 as excluded would require independent adjudication and approval; treating them as ordinary independent samples would risk photo leakage. A HAM-only or eight-present-class exploratory partition would not answer the nine-class evaluation question, so this Stage 4 release deliberately emits no data split.

`guarded_group_split` in `src/nine_class_stage4.py` is a deterministic seed-42 **train/validation-only** helper for a later, separately adjudicated eligible input. It requires an explicit `APPROVED_ELIGIBLE` status on every row, rejects publisher source-test rows, requires at least two independent overlap groups in each of the nine classes, and checks that every class occurs in both partitions. It keeps each supplied overlap group intact. No Stage 4 inventory row has this approval status. Its input must already include approved identity resolution and verified IDs; this helper does not convert the source inventory into an eligible cohort. A future protocol must protect source test, audit cross-source and suspected overlaps, stratify when feasible, freeze group assignments, and report class counts before any final test use. The previously proposed 80/10/10 seed-42 ratio is a local adaptation proposal, not a verified EG-VAN paper split.

## On-demand preprocessing and loader

`src/nine_class_dataset.py` loads an **explicit split CSV** only and refuses absent partitions, mapping errors, missing files, or publisher test rows assigned to training. No split CSV was created here. Its `PreprocessConfig` exposes all numerical settings. The per-image operation order is the existing `src/preprocessing.py` implementation: elliptical blackhat hair mask (17-pixel kernel, threshold 10), Telea inpainting (radius 1), Gray World balancing, and three-scale Retinex (sigmas 15/80/250, equal weights, 1st/99th percentile channel scaling). These numerical settings are **local adaptations**; the paper does not specify them. The Fanconic JPEGs are already 224×224 and their prior processing is unknown, so repeating color operations may compound unknown source processing. This must be reviewed before model experiments.

After color processing, the loader converts OpenCV BGR to RGB, resizes to 384×384, scales uint8 pixels to float32 `[0,1]`, then applies RGB ImageNet mean `(0.485, 0.456, 0.406)` and standard deviation `(0.229, 0.224, 0.225)` as a **model-specific adaptation** matching the existing EfficientNet baseline convention. The tensor is `float32` in `C,H,W` order, shape `(3,384,384)`. No dataset statistics are fit; the protected test set supplies no normalization parameters. Validation and test apply only deterministic steps. Random horizontal/vertical flips and 0/90/180/270-degree rotations run only for training. This is a deliberately small local augmentation set, **not** the paper's unspecified 20 transformations. Processing is on demand; no duplicate processed-image cache is written. The existing seven-class code remains unchanged.

Loader usage after an eligible split is approved:

```python
from pathlib import Path
from torch.utils.data import DataLoader
from nine_class_dataset import NineClassDataset, PreprocessConfig

root = Path(r"E:\Cancerdetection\EG-VAN")
config = PreprocessConfig(image_size=384)
train = NineClassDataset(root, root / "PATH_TO_APPROVED_SPLIT.csv", "train", config)
train_loader = DataLoader(train, batch_size=32, shuffle=True)
```

The example is an interface contract, not an existing approved split or a training instruction. Use `validation` and `test` only after their partitions are independently frozen. The model must expose nine logits in the fixed order above.

## Reproduce and validate

From the project root, run `python src/nine_class_stage4.py` **only when its output manifest and audit are absent**; the generator refuses to overwrite them. `python src/nine_class_stage4_validate.py` verifies the manifest and writes a new `analysis/nine_class_stage4/validation_report.json`, also refusing overwrite. Tests: `python -m pytest tests/test_nine_class_stage4.py -q`. The validator loads one original HAM and one original Fanconic image at 64×64 solely as a lightweight smoke test; it creates no split or processed-image copy. This documentation and the Stage 4 outputs do not alter any Stage 3 evidence, reviewer choice, clinical label, source image, or previous experiment output.

The initial Stage 4 run found **8,303 transitive groups**, including **90 groups containing both publisher source-train and source-test members after HAM lesion grouping**. That is broader than the four source-boundary groups in the Stage 3I photo/suspected graph alone: adding all photos with a common recorded HAM lesion ID can connect more binary source partitions. These 90 are a conservative graph audit, not 90 independently verified patient matches. There are three exact-SHA groups (the known Fanconic malignant pair and two HAM groups), with no exact-content group missing from the Stage 3I/lesion graph. The statuses are: 2,369 prior proposed exclusions, 83 AI-supported BENIGN quarantine records, 165 other protected binary source-test records, 705 HAM records linked to protected source-test groups, 680 provisional binary source-train MALIGNANT records, and 9,310 other HAM records. These are inventory statuses, **not counts approved for training**. The 20 AI-uncertain pair edges touch BENIGN records already in the AI-same-photo quarantine status; they remain present as `SUSPECTED_UNRESOLVED_OVERLAP` evidence tiers.

The real-image smoke test decoded both samples as finite `torch.float32` `(3,64,64)` tensors. The configured production interface remains `(3,384,384)`. Focused Stage 4 tests returned **5 passed**; the existing shape-contract test returned **1 passed**. Three Stage 3I evidence tests also passed after generation. Torchvision emitted an optional `torchvision.io` image-extension warning in this Windows environment during the shape-contract test; the new loader uses OpenCV for decoding and did not rely on that extension.

## Open scientific gates

Independent review of AI-supported BENIGN photo matches, unresolved candidate relations and protected source-test conflicts remains necessary. The exact Fanconic version used by EG-VAN, Fanconic patient/lesion and source image IDs, clinical basis for broad binary labels, source-test provenance, and image-level redistribution terms remain unverified. SHA equality and the recorded photo/lesion graph are narrower than patient independence; near-duplicate retrieval can miss altered images. No leakage-audited nine-class accuracy can be measured yet. **Stage 5 architecture and shape verification may proceed using synthetic tensors and the nine-label interface**, while final cohort approval, split freezing and model training remain gated.
