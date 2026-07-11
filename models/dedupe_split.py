"""
Rebuilds dataset_filtered/'s train/validation/test split from scratch,
using near-duplicate clustering instead of a naive per-image random
split.

Why: measured leakage between train and validation via perceptual
hashing -- 86.7% near-duplicate overlap in n7i5x9's OWN upstream splits
(never touched by us, provided as-is), and 99.6% in this project's own
akahana split (prepare_akahana.py, per-image random assignment). Neither
source provides subject/session metadata, so these are almost certainly
near-duplicate frames from the same recording session landing on both
sides of the split by chance. Every "accuracy" number produced so far in
this project is inflated by this and should not be trusted.

Approach: perceptual-hash (average hash, 8x8 = 64 bits) every kept image
across all three current splits combined, cluster near-duplicates
(coarse 4x4 hash as a cheap bucketing key so we don't do a full O(n^2)
pairwise comparison over ~47k images, then exact 64-bit Hamming distance
<=5 within each bucket), and assign whole clusters -- never split one --
to train/validation/test targeting an 80/10/10 ratio.
"""

import os
import shutil
from collections import defaultdict

import numpy as np
from PIL import Image

SOURCE_DIR = "dataset_filtered"  # current (leaky) split, read from
OUTPUT_DIR = "dataset_dedup"  # new leak-safe split, written to
CLASSES = ["drowsy", "not_drowsy"]
SPLITS = ["train", "validation", "test"]
TARGET_RATIOS = {"train": 0.8, "validation": 0.1, "test": 0.1}
FINE_SIZE = 8
COARSE_SIZE = 4
HAMMING_THRESH = 5


def ahash_bits(pil_img, size):
    img = pil_img.convert("L").resize((size, size), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float64)
    return arr > arr.mean()


def bits_to_int(bits):
    out = 0
    for b in bits.flatten():
        out = (out << 1) | int(b)
    return out


def hamming(a, b):
    return int(np.count_nonzero(a != b))


def collect_all_images():
    by_class = {c: [] for c in CLASSES}
    for split in SPLITS:
        for cls in CLASSES:
            d = os.path.join(SOURCE_DIR, split, cls)
            if not os.path.isdir(d):
                continue
            for fname in os.listdir(d):
                by_class[cls].append(os.path.join(d, fname))
    return by_class


def cluster(paths):
    fine_hashes = {}
    buckets = defaultdict(list)
    for i, p in enumerate(paths):
        img = Image.open(p)
        fine_hashes[i] = ahash_bits(img, FINE_SIZE)
        coarse_key = bits_to_int(ahash_bits(img, COARSE_SIZE))
        buckets[coarse_key].append(i)
        if (i + 1) % 5000 == 0:
            print(f"    hashed {i + 1}/{len(paths)}")

    parent = list(range(len(paths)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for idxs in buckets.values():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                ia, ib = idxs[a], idxs[b]
                if hamming(fine_hashes[ia], fine_hashes[ib]) <= HAMMING_THRESH:
                    union(ia, ib)

    groups = defaultdict(list)
    for i in range(len(paths)):
        groups[find(i)].append(paths[i])
    return list(groups.values())


def assign_clusters(clusters):
    """Greedy: process clusters biggest-first, always give the next
    cluster to whichever split is currently furthest below its target
    share. Keeps final ratios close to 80/10/10 despite uneven cluster
    sizes, without ever splitting a cluster across splits."""
    total = sum(len(c) for c in clusters)
    targets = {s: TARGET_RATIOS[s] * total for s in SPLITS}
    counts = {s: 0 for s in SPLITS}
    assignment = {}
    for cluster_paths in sorted(clusters, key=len, reverse=True):
        best_split = min(SPLITS, key=lambda s: counts[s] - targets[s])
        for p in cluster_paths:
            assignment[p] = best_split
        counts[best_split] += len(cluster_paths)
    return assignment, counts


def main():
    by_class = collect_all_images()

    for cls in CLASSES:
        print(f"--- Class: {cls} ({len(by_class[cls])} images) ---")
        clusters = cluster(by_class[cls])
        print(f"  {len(by_class[cls])} images -> {len(clusters)} clusters")
        assignment, counts = assign_clusters(clusters)
        print(f"  split sizes: {counts}")

        next_idx = {s: 1 for s in SPLITS}
        for src_path, split in assignment.items():
            dst_dir = os.path.join(OUTPUT_DIR, split, cls)
            os.makedirs(dst_dir, exist_ok=True)
            idx = next_idx[split]
            next_idx[split] += 1
            shutil.copy2(src_path, os.path.join(dst_dir, f"{idx}.jpg"))

    print("\nDone. New leak-safe dataset in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
