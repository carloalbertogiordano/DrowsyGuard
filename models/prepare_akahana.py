"""
Downloads akahana/Driver-Drowsiness-Dataset from Hugging Face, filters it
with the same face-detection check as filter_dataset.py (removes images
with no detectable face -- incompatible framing, see filter_dataset.py's
docstring for the full investigation), and merges the result into
dataset_filtered/, adding volume back after filtering n7i5x9 down to
~38% of its original size.

akahana only ships train/test splits (no validation), so this script
carves its own 80/10/10 train/validation/test split with a fixed seed,
done ONCE on this source only. Never remerged with n7i5x9's existing
splits in dataset_filtered/ -- same anti-leakage rule as
prepare_dataset.py, extended to a second independent source.

Files are prefixed "akahana_" to avoid filename collisions with the
existing n7i5x9-derived files already in dataset_filtered/.
"""

import os
import random

import cv2
import numpy as np
from datasets import load_dataset

OUTPUT_DIR = "dataset_filtered"
SEED = 42
SPLIT_RATIOS = {"train": 0.8, "validation": 0.1, "test": 0.1}

# akahana's ClassLabel order is ["Drowsy", "Non Drowsy"] (index 0, 1) --
# opposite of this project's own convention (CLASSES = ["not_drowsy",
# "drowsy"] in train_model.py). Mapped explicitly here to avoid mixing them up.
LABEL_TO_CLASS = {0: "drowsy", 1: "not_drowsy"}

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def has_face(pil_img):
    img = np.array(pil_img.convert("RGB"))[:, :, ::-1]  # RGB -> BGR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    return len(faces) > 0


def assign_split(rng):
    r = rng.random()
    if r < SPLIT_RATIOS["train"]:
        return "train"
    if r < SPLIT_RATIOS["train"] + SPLIT_RATIOS["validation"]:
        return "validation"
    return "test"


def main():
    rng = random.Random(SEED)
    print("Download akahana/Driver-Drowsiness-Dataset...")
    ds = load_dataset("akahana/Driver-Drowsiness-Dataset")

    kept = 0
    discarded = 0
    counters = {}

    for source_split in ["train", "test"]:
        n = len(ds[source_split])
        for i, ex in enumerate(ds[source_split]):
            image = ex["image"]
            class_name = LABEL_TO_CLASS[ex["label"]]

            if not has_face(image):
                discarded += 1
                continue
            kept += 1

            split_name = assign_split(rng)
            key = (split_name, class_name)
            counters[key] = counters.get(key, 0) + 1
            idx = counters[key]

            class_dir = os.path.join(OUTPUT_DIR, split_name, class_name)
            os.makedirs(class_dir, exist_ok=True)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(os.path.join(class_dir, f"akahana_{idx}.jpg"))

            if (i + 1) % 2000 == 0 or (i + 1) == n:
                print(f"  [{source_split}] {i + 1}/{n} (kept {kept}, discarded {discarded})")

    print(f"\nTOTAL: kept {kept}, discarded {discarded}")
    for (split_name, class_name), count in sorted(counters.items()):
        print(f"  {split_name}/{class_name}: {count}")


if __name__ == "__main__":
    main()
