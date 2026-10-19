#!/usr/bin/env python3
"""Read-only perceptual candidate search for the nine-class source images."""

from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis" / "nine_class_similarity"
THRESHOLD = 6
HAM_DIRS = (
    ROOT / "data/raw/HAM10000_images_part_1",
    ROOT / "data/raw/HAM10000_images_part_2",
)
BIN_DIR = ROOT / "data/isic/data"
POPCOUNT = np.unpackbits(np.arange(256, dtype=np.uint8)[:, None], axis=1).sum(axis=1)


def fingerprint(path: Path) -> tuple[int, int]:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Cannot decode {path}")
    small = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    dct = cv2.dct(small)[:8, :8]
    phash = (dct > np.median(dct[1:])).reshape(-1)
    tiny = cv2.resize(image, (9, 8), interpolation=cv2.INTER_AREA)
    dhash = (tiny[:, 1:] > tiny[:, :-1]).reshape(-1)
    return int.from_bytes(np.packbits(phash).tobytes(), "big"), int.from_bytes(np.packbits(dhash).tobytes(), "big")


def candidate_rows(paths: list[Path], phashes: np.ndarray, dhashes: np.ndarray):
    # Compare the small (3,297-image) binary set with all HAM originals and
    # with the remainder of itself. Byte-wise vectorization avoids a quadratic
    # Python loop; this is candidate retrieval, not proof of identity.
    binaries = [(i, p) for i, p in enumerate(paths) if p.is_relative_to(BIN_DIR)]
    for i, path in binaries:
        start = 0
        while start < len(paths):
            end = min(start + 4096, len(paths))
            p_xor = (phashes[start:end] ^ phashes[i]).view(np.uint8).reshape(-1, 8)
            d_xor = (dhashes[start:end] ^ dhashes[i]).view(np.uint8).reshape(-1, 8)
            p_dist = POPCOUNT[p_xor].sum(axis=1)
            d_dist = POPCOUNT[d_xor].sum(axis=1)
            for offset in np.flatnonzero((p_dist <= THRESHOLD) | (d_dist <= THRESHOLD)):
                j = start + int(offset)
                if j == i or (paths[j].is_relative_to(BIN_DIR) and j < i):
                    continue
                yield {
                    "path_a": path.relative_to(ROOT).as_posix(),
                    "path_b": paths[j].relative_to(ROOT).as_posix(),
                    "scope": "binary_binary" if paths[j].is_relative_to(BIN_DIR) else "binary_ham",
                    "phash_distance": int(p_dist[offset]),
                    "dhash_distance": int(d_dist[offset]),
                }
            start = end


def main() -> None:
    paths = sorted(p for directory in HAM_DIRS for p in directory.glob("*.jpg"))
    paths += sorted(BIN_DIR.rglob("*.jpg"))
    if len(paths) != 13312:
        raise ValueError(f"Expected 13,312 canonical source entries; got {len(paths)}")
    phashes, dhashes = [], []
    for index, path in enumerate(paths, 1):
        p, d = fingerprint(path)
        phashes.append(p)
        dhashes.append(d)
        if index % 1000 == 0:
            print(f"fingerprinted {index}/{len(paths)}", flush=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "fingerprints.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image_path", "phash64", "dhash64"))
        writer.writerows((p.relative_to(ROOT).as_posix(), f"{ph:016x}", f"{dh:016x}") for p, ph, dh in zip(paths, phashes, dhashes))
    with (OUTPUT / "candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path_a", "path_b", "scope", "phash_distance", "dhash_distance"))
        writer.writeheader()
        count = 0
        for row in candidate_rows(paths, np.asarray(phashes, dtype=np.uint64), np.asarray(dhashes, dtype=np.uint64)):
            writer.writerow(row)
            count += 1
    print(f"candidate pairs at Hamming distance <= {THRESHOLD}: {count}", flush=True)


if __name__ == "__main__":
    main()
