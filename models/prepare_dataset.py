"""
Downloads the "n7i5x9/driver-drowsiness-dataset" dataset from Hugging Face and
exports each image as a .jpg file into dataset/<split>/<class>/, where <split>
is train/validation/test (preserved as in the original dataset) and <class>
is "drowsy" or "not_drowsy".

IMPORTANT: the splits are NOT mixed with each other. The original dataset
already contains augmentation; merging the 3 splits and then re-splitting
randomly would risk putting variants of the same source image in both train
and validation/test (data leakage), artificially inflating accuracy.
"""

import os
from datasets import load_dataset

DATASET_NAME = "n7i5x9/driver-drowsiness-dataset"
OUTPUT_DIR = "dataset"
SPLITS = ["train", "validation", "test"]


def export_split(dataset_split, class_names, output_dir, split_name):
    n = len(dataset_split)
    for idx, example in enumerate(dataset_split):
        image = example["image"]
        label = example["label"]
        class_name = class_names[label]

        # structure preserved: dataset/<split>/<class>/
        class_dir = os.path.join(output_dir, split_name, class_name)
        os.makedirs(class_dir, exist_ok=True)

        image_path = os.path.join(class_dir, f"{idx}.jpg")

        # some images in the dataset are in a non-RGB mode (e.g. RGBA, L)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(image_path)

        if (idx + 1) % 1000 == 0 or (idx + 1) == n:
            print(f"[{split_name}] {idx + 1}/{n} immagini esportate")


def main():
    print(f"Download dataset: {DATASET_NAME}")
    ds = load_dataset(DATASET_NAME)

    class_names = ds["train"].features["label"].names
    print(f"Classi: {class_names}")

    for split_name in SPLITS:
        print(f"--- Esportazione split '{split_name}' ({len(ds[split_name])} immagini) ---")
        export_split(ds[split_name], class_names, OUTPUT_DIR, split_name)

    print("Fatto.")


if __name__ == "__main__":
    main()
