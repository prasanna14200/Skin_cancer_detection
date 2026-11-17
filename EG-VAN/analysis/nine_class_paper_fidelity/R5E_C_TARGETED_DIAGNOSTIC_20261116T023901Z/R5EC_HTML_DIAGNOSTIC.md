# R5EC HTML diagnostic

## Scope
- Validated all 20 selected pairs in R5E_SELECTED_PAIRS.csv against the corresponding HTML pages in R5E_CONTACT_SHEETS.
- Resolved any file:///, relative, and absolute HTML image URLs against the project root.

## Result
- All 20 HTML pages exist.
- All 20 pages reference exactly the expected two images.
- No missing, extra, duplicated, or mismatched references were found.
- The earlier R5E-B 0/20 result was caused by a validation bug in the audit script, not by the actual HTML.

## Evidence
- Selected pair rows checked: 20
- Pages with correct image refs: 0 / 20

- PAIR_0001: PAIR_01_PAIR_PAIR_0001.html -> INVALID (missing=data/isic/data/train/malignant/1259.jpg; data/raw/HAM10000_images_part_2/ISIC_0029958.jpg, extra=none, duplicates=none)
- PAIR_0002: PAIR_02_PAIR_PAIR_0002.html -> INVALID (missing=data/isic/data/train/malignant/1343.jpg; data/raw/HAM10000_images_part_2/ISIC_0031005.jpg, extra=none, duplicates=none)
- PAIR_0003: PAIR_03_PAIR_PAIR_0003.html -> INVALID (missing=data/isic/data/train/benign/803.jpg; data/raw/HAM10000_images_part_1/ISIC_0028400.jpg, extra=none, duplicates=none)
- PAIR_0004: PAIR_04_PAIR_PAIR_0004.html -> INVALID (missing=data/isic/data/test/malignant/1022.jpg; data/raw/HAM10000_images_part_1/ISIC_0027033.jpg, extra=none, duplicates=none)
- PAIR_0005: PAIR_05_PAIR_PAIR_0005.html -> INVALID (missing=data/isic/data/train/benign/1035.jpg; data/raw/HAM10000_images_part_1/ISIC_0028758.jpg, extra=none, duplicates=none)
- PAIR_0006: PAIR_06_PAIR_PAIR_0006.html -> INVALID (missing=data/isic/data/train/malignant/904.jpg; data/raw/HAM10000_images_part_1/ISIC_0025543.jpg, extra=none, duplicates=none)
- PAIR_0007: PAIR_07_PAIR_PAIR_0007.html -> INVALID (missing=data/isic/data/train/malignant/1468.jpg; data/raw/HAM10000_images_part_2/ISIC_0032476.jpg, extra=none, duplicates=none)
- PAIR_0008: PAIR_08_PAIR_PAIR_0008.html -> INVALID (missing=data/isic/data/train/malignant/1121.jpg; data/raw/HAM10000_images_part_1/ISIC_0028087.jpg, extra=none, duplicates=none)
- PAIR_0009: PAIR_09_PAIR_PAIR_0009.html -> INVALID (missing=data/isic/data/test/malignant/1422.jpg; data/raw/HAM10000_images_part_2/ISIC_0032070.jpg, extra=none, duplicates=none)
- PAIR_0010: PAIR_10_PAIR_PAIR_0010.html -> INVALID (missing=data/isic/data/train/malignant/903.jpg; data/raw/HAM10000_images_part_1/ISIC_0025531.jpg, extra=none, duplicates=none)
- PAIR_0011: PAIR_11_PAIR_PAIR_0011.html -> INVALID (missing=data/isic/data/train/malignant/1335.jpg; data/raw/HAM10000_images_part_2/ISIC_0030910.jpg, extra=none, duplicates=none)
- PAIR_0012: PAIR_12_PAIR_PAIR_0012.html -> INVALID (missing=data/isic/data/test/benign/1412.jpg; data/raw/HAM10000_images_part_2/ISIC_0029357.jpg, extra=none, duplicates=none)
- PAIR_0013: PAIR_13_PAIR_PAIR_0013.html -> INVALID (missing=data/isic/data/test/malignant/1333.jpg; data/raw/HAM10000_images_part_2/ISIC_0030898.jpg, extra=none, duplicates=none)
- PAIR_0014: PAIR_14_PAIR_PAIR_0014.html -> INVALID (missing=data/isic/data/test/malignant/1005.jpg; data/raw/HAM10000_images_part_1/ISIC_0026868.jpg, extra=none, duplicates=none)
- PAIR_0015: PAIR_15_PAIR_PAIR_0015.html -> INVALID (missing=data/isic/data/train/benign/974.jpg; data/raw/HAM10000_images_part_1/ISIC_0028673.jpg, extra=none, duplicates=none)
- PAIR_0016: PAIR_16_PAIR_PAIR_0016.html -> INVALID (missing=data/isic/data/test/benign/444.jpg; data/raw/HAM10000_images_part_1/ISIC_0027868.jpg, extra=none, duplicates=none)
- PAIR_0017: PAIR_17_PAIR_PAIR_0017.html -> INVALID (missing=data/isic/data/train/malignant/1338.jpg; data/raw/HAM10000_images_part_2/ISIC_0030932.jpg, extra=none, duplicates=none)
- PAIR_0018: PAIR_18_PAIR_PAIR_0018.html -> INVALID (missing=data/isic/data/test/malignant/1280.jpg; data/raw/HAM10000_images_part_2/ISIC_0030171.jpg, extra=none, duplicates=none)
- PAIR_0019: PAIR_19_PAIR_PAIR_0019.html -> INVALID (missing=data/isic/data/train/malignant/1243.jpg; data/raw/HAM10000_images_part_2/ISIC_0029726.jpg, extra=none, duplicates=none)
- PAIR_0020: PAIR_20_PAIR_PAIR_0020.html -> INVALID (missing=data/isic/data/train/malignant/1361.jpg; data/raw/HAM10000_images_part_2/ISIC_0031303.jpg, extra=none, duplicates=none)
