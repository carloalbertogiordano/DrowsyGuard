"""
Filters dataset/<split>/<class>/ into dataset_filtered/<split>/<class>/,
keeping only images where a face is detectable.

Context: n7i5x9/driver-drowsiness-dataset unifies labels from 4 source
datasets. Visual sampling found at least two incompatible framings mixed
under the same binary labels: full driver-in-car shots (face + visible
car interior) and extreme macro single-eye crops (no face in frame at
all, inherited from an MRL-eye-dataset-style source). A live webcam at
normal distance matches neither training distribution well, which is the
likely root cause of near-random confidence observed live. This script
removes the macro-eye subset so training only sees the framing that
resembles real deployment input.

Deliberately does NOT import TensorFlow: cv2.CascadeClassifier segfaults
when run in the same process as TensorFlow (see preprocessing.py history).
Standalone here, so the classic Haar frontal-face cascade is safe to use.

Splits are filtered independently and never remerged/reshuffled, same
rule as prepare_dataset.py (avoids leaking augmented variants across
train/validation/test).
"""

import os
import shutil

import cv2

SPLITS = ["train", "validation", "test"]
CLASSES = ["drowsy", "not_drowsy"]
DATASET_DIR = "dataset"
OUTPUT_DIR = "dataset_filtered"

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def has_face(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    return len(faces) > 0


def filter_split(split_name):
    kept, discarded = 0, 0
    for class_name in CLASSES:
        src_dir = os.path.join(DATASET_DIR, split_name, class_name)
        dst_dir = os.path.join(OUTPUT_DIR, split_name, class_name)
        os.makedirs(dst_dir, exist_ok=True)

        filenames = sorted(os.listdir(src_dir))
        n = len(filenames)
        for i, fname in enumerate(filenames):
            src_path = os.path.join(src_dir, fname)
            if has_face(src_path):
                shutil.copy2(src_path, os.path.join(dst_dir, fname))
                kept += 1
            else:
                discarded += 1

            if (i + 1) % 2000 == 0 or (i + 1) == n:
                print(f"  [{split_name}/{class_name}] {i + 1}/{n}")

    return kept, discarded


def main():
    total_kept, total_discarded = 0, 0
    for split_name in SPLITS:
        print(f"--- Filtering split '{split_name}' ---")
        kept, discarded = filter_split(split_name)
        total = kept + discarded
        pct = (discarded / total * 100) if total else 0.0
        print(f"{split_name}: kept {kept}, discarded {discarded} ({pct:.1f}% removed)")
        total_kept += kept
        total_discarded += discarded

    total = total_kept + total_discarded
    pct = (total_discarded / total * 100) if total else 0.0
    print(f"\nTOTAL: kept {total_kept}, discarded {total_discarded} ({pct:.1f}% removed)")


if __name__ == "__main__":
    main()
