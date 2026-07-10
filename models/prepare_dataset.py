"""
Scarica il dataset "n7i5x9/driver-drowsiness-dataset" da Hugging Face ed esporta
ogni immagine come file .jpg dentro dataset/<split>/<classe>/, dove <split> e'
train/validation/test (preservati come nel dataset originale) e <classe> e'
"drowsy" o "not_drowsy".

IMPORTANTE: gli split NON vengono mescolati tra loro. Il dataset originale
contiene gia' augmentation; unire i 3 split e poi ri-splittare a caso
rischierebbe di mettere varianti della stessa immagine sorgente sia in train
che in validation/test (data leakage), gonfiando artificialmente l'accuracy.
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

        # struttura preservata: dataset/<split>/<classe>/
        class_dir = os.path.join(output_dir, split_name, class_name)
        os.makedirs(class_dir, exist_ok=True)

        image_path = os.path.join(class_dir, f"{idx}.jpg")

        # alcune immagini nel dataset sono in modalita' non-RGB (es. RGBA, L)
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
