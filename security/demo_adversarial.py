"""
Demo end-to-end: attacco adversarial patch + difesa (input sanitization).

1. Carica il modello allenato e un'immagine di validation.
2. Predizione baseline (nessun attacco).
3. Genera e applica una patch adversarial -> predizione (dovrebbe sbagliare).
4. Applica la difesa (blur) sull'immagine con patch -> predizione (dovrebbe
   tornare corretta).
5. Salva le 3 immagini (originale, con patch, con patch+difesa) e un report
   testuale con le confidence, per la relazione.
"""

import os
import random
import sys

import cv2
import numpy as np
import tensorflow as tf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "models"))
from preprocessing import SQUARE_SIZE, to_luminance  # noqa: E402

from adversarial_patch import apply_patch, generate_patch, sanitize

KERAS_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "drowsiness_model.keras")
VAL_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "validation")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "adversarial_demo")
CLASSES = ["not_drowsy", "drowsy"]  # indice 1 = drowsy (coerente con train_model.py)


def pick_sample():
    class_name = random.choice(CLASSES)
    class_dir = os.path.join(VAL_DIR, class_name)
    filename = random.choice(os.listdir(class_dir))
    label = CLASSES.index(class_name)
    return os.path.join(class_dir, filename), label, class_name


def load_and_preprocess(path):
    bgr = cv2.imread(path)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, SQUARE_SIZE)
    return to_luminance(rgb)  # (H, W, 3) float32, canali [Y, B, R]


def predict(model, image):
    batch = np.expand_dims(image / 255.0, axis=0).astype("float32")
    prob = float(model.predict(batch, verbose=0)[0][0])
    label = "drowsy" if prob > 0.5 else "not_drowsy"
    return prob, label


def main():
    if not os.path.exists(KERAS_MODEL_PATH):
        print(f"ERRORE: manca '{KERAS_MODEL_PATH}'. Allena prima il modello.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Carico modello: {KERAS_MODEL_PATH}")
    model = tf.keras.models.load_model(KERAS_MODEL_PATH)

    path, true_label, class_name = pick_sample()
    print(f"Campione scelto: {path} (vera classe: {class_name})")
    image = load_and_preprocess(path)

    report_lines = [f"Campione: {path}", f"Classe vera: {class_name}", ""]

    # 1. Baseline
    prob, pred = predict(model, image)
    print(f"[Baseline]        P(drowsy)={prob:.4f}  predetto={pred}")
    report_lines.append(f"Baseline:            P(drowsy)={prob:.4f}  predetto={pred}")
    cv2.imwrite(os.path.join(OUTPUT_DIR, "1_original.png"), image.astype("uint8"))

    # 2. Attacco
    patch = generate_patch(model, image, true_label)
    patched_image = apply_patch(image, patch, position=(38, 38))
    prob_attack, pred_attack = predict(model, patched_image)
    print(f"[Con patch]       P(drowsy)={prob_attack:.4f}  predetto={pred_attack}")
    report_lines.append(f"Con patch (attacco): P(drowsy)={prob_attack:.4f}  predetto={pred_attack}")
    cv2.imwrite(os.path.join(OUTPUT_DIR, "2_patched.png"), patched_image.astype("uint8"))

    # 3. Difesa
    sanitized_image = sanitize(patched_image)
    prob_defense, pred_defense = predict(model, sanitized_image)
    print(f"[Patch + difesa]  P(drowsy)={prob_defense:.4f}  predetto={pred_defense}")
    report_lines.append(f"Patch + difesa:      P(drowsy)={prob_defense:.4f}  predetto={pred_defense}")
    cv2.imwrite(os.path.join(OUTPUT_DIR, "3_sanitized.png"), sanitized_image.astype("uint8"))

    attack_success = pred_attack != class_name
    defense_success = pred_defense == class_name
    report_lines.append("")
    report_lines.append(f"Attacco riuscito (ha cambiato la predizione): {attack_success}")
    report_lines.append(f"Difesa riuscita (ha ripristinato la predizione corretta): {defense_success}")

    report_path = os.path.join(OUTPUT_DIR, "report.txt")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\nImmagini + report salvati in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
