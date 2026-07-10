"""
Verifica visiva del preprocessing (resize quadrato + luminanza YCbCr).
Prende N immagini a caso dal training set (mix drowsy/not_drowsy), applica
la stessa to_luminance() usata da train_model.py, e salva coppie
originale/preprocessata in models/preprocessing_samples/ cosi' si puo'
controllare a occhio il risultato.

Gira in locale, no GPU/Docker necessario (solo OpenCV, veloce).
"""

import os
import random

import cv2

from preprocessing import SQUARE_SIZE, to_luminance

CLASSES = ["drowsy", "not_drowsy"]
TRAIN_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "train")
N_SAMPLES = 5
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "preprocessing_samples")


def pick_random_images(n):
    samples = []
    for class_name in CLASSES:
        class_dir = os.path.join(TRAIN_DIR, class_name)
        files = os.listdir(class_dir)
        chosen = random.sample(files, min(n, len(files)))
        samples.extend((class_name, os.path.join(class_dir, f)) for f in chosen)
    random.shuffle(samples)
    return samples[:n]


def main():
    if not os.path.isdir(TRAIN_DIR):
        print(f"ERRORE: manca '{TRAIN_DIR}'. Esegui prima prepare_dataset.py.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    samples = pick_random_images(N_SAMPLES)

    for i, (class_name, path) in enumerate(samples):
        bgr = cv2.imread(path)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, SQUARE_SIZE)  # forza quadrato (stretch)

        processed = to_luminance(rgb)  # (H, W, 3) float32, canali [Y, B, R]
        processed_img = processed.astype("uint8")
        y_channel, b_channel, r_channel = (processed_img[:, :, c] for c in range(3))

        original_path = os.path.join(OUTPUT_DIR, f"{i}_{class_name}_original.png")
        composite_path = os.path.join(OUTPUT_DIR, f"{i}_{class_name}_composite_YBR.png")
        y_path = os.path.join(OUTPUT_DIR, f"{i}_{class_name}_channel_Y.png")
        b_path = os.path.join(OUTPUT_DIR, f"{i}_{class_name}_channel_B.png")
        r_path = os.path.join(OUTPUT_DIR, f"{i}_{class_name}_channel_R.png")

        cv2.imwrite(original_path, bgr)
        cv2.imwrite(composite_path, processed_img)  # 3 canali, "falso colore"
        cv2.imwrite(y_path, y_channel)
        cv2.imwrite(b_path, b_channel)
        cv2.imwrite(r_path, r_channel)

        print(f"[{i}] {class_name}: {original_path} -> Y/B/R + composite in {OUTPUT_DIR}")

    print(f"\n{len(samples)} coppie salvate in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
