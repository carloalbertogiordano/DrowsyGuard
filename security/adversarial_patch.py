"""
Adversarial patch attack + difesa (input sanitization), per la dimostrazione
IoT security del progetto (T4.3/T4.4).

Attacco: genera una piccola patch di pixel che, sovrapposta a un'immagine,
inganna il modello (evasion attack) -- via gradient ascent (PGD-style):
si ottimizzano i pixel della patch per MASSIMIZZARE la loss rispetto
all'etichetta vera, tenendo i pesi del modello fissi. Stesso meccanismo
matematico del training, ma con i ruoli invertiti (variabile = patch, non
pesi; obiettivo = errore, non accuratezza).

Difesa: sanitizzazione dell'input (blur gaussiano) prima dell'inferenza, per
rompere la perturbazione ad alta frequenza tipica delle patch adversarial,
senza richiedere un nuovo training del modello.
"""

import os

import cv2
import numpy as np
import tensorflow as tf


def apply_patch(image: np.ndarray, patch: np.ndarray, position: tuple) -> np.ndarray:
    """
    Sovrappone patch su image alla posizione (x, y) = angolo alto-sinistra.
    Ritorna una COPIA (non modifica l'originale).
    """
    result = image.copy()
    x, y = position
    ph, pw = patch.shape[:2]
    result[y : y + ph, x : x + pw] = patch
    return result


def generate_patch(
    model: tf.keras.Model,
    image: np.ndarray,
    true_label: int,
    position: tuple = (38, 38),
    patch_size: int = 20,
    epsilon: float = 8.0,
    steps: int = 50,
) -> np.ndarray:
    """
    Genera una patch adversarial per una specifica immagine, via gradient
    ascent (PGD-style).

    image: (H, W, 3) float32, valori 0..255 (stesso formato preprocessing
           del training, es. canali Y/B/R gia' estratti).
    true_label: 0 o 1, l'etichetta vera dell'immagine (serve per calcolare
                la loss da massimizzare -- vogliamo che il modello sbagli
                proprio su QUESTA etichetta).
    position: dove piazzare la patch (x, y).
    epsilon: step size per ogni iterazione del gradient ascent.
    steps: numero di iterazioni.
    """
    x, y = position
    patch = tf.Variable(
        np.random.uniform(0, 255, size=(patch_size, patch_size, 3)).astype("float32")
    )
    label = tf.constant([[float(true_label)]], dtype=tf.float32)
    loss_fn = tf.keras.losses.BinaryCrossentropy()

    for _ in range(steps):
        with tf.GradientTape() as tape:
            tape.watch(patch)
            patched = tf.identity(image)
            patched = tf.tensor_scatter_nd_update(
                patched,
                indices=[[i, j] for i in range(y, y + patch_size) for j in range(x, x + patch_size)],
                updates=tf.reshape(patch, (-1, 3)),
            )
            patched_batch = tf.expand_dims(patched / 255.0, axis=0)
            prediction = model(patched_batch, training=False)
            loss = loss_fn(label, prediction)

        grad = tape.gradient(loss, patch)
        # Gradient ASCENT (+=, non -=): vogliamo AUMENTARE la loss (far
        # sbagliare il modello), non minimizzarla come nel training normale.
        patch.assign_add(epsilon * tf.sign(grad))
        patch.assign(tf.clip_by_value(patch, 0, 255))

    return patch.numpy()


def sanitize(image: np.ndarray, blur_ksize: int = 5) -> np.ndarray:
    """
    Difesa: blur gaussiano prima dell'inferenza. Le patch adversarial
    dipendono da perturbazioni precise pixel-per-pixel (alta frequenza);
    sfocare l'immagine le distrugge, mentre il contenuto "vero" (basso
    frequenza: forma occhio, luminosita' generale) resta riconoscibile.
    """
    blurred = cv2.GaussianBlur(image.astype("uint8"), (blur_ksize, blur_ksize), 0)
    return blurred.astype("float32")
