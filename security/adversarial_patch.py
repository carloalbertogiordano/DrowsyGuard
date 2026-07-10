"""
Adversarial patch attack + defense (input sanitization), for the project's
IoT security demonstration (T4.3/T4.4).

Attack: generates a small pixel patch that, overlaid on an image, fools the
model (evasion attack) -- via gradient ascent (PGD-style): the patch pixels
are optimized to MAXIMIZE the loss w.r.t. the true label, keeping the
model's weights fixed. Same mathematical mechanism as training, but with
the roles reversed (variable = patch, not weights; objective = error, not
accuracy).

Defense: input sanitization (Gaussian blur) before inference, to break the
high-frequency perturbation typical of adversarial patches, without
requiring any retraining of the model.
"""

import os

import cv2
import numpy as np
import tensorflow as tf


def apply_patch(image: np.ndarray, patch: np.ndarray, position: tuple) -> np.ndarray:
    """
    Overlays patch onto image at position (x, y) = top-left corner.
    Returns a COPY (does not modify the original).
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
    Generates an adversarial patch for a specific image, via gradient
    ascent (PGD-style).

    image: (H, W, 3) float32, values 0..255 (same preprocessing format as
           training, e.g. Y/B/R channels already extracted).
    true_label: 0 or 1, the image's true label (needed to compute the loss
                to maximize -- we want the model to be wrong specifically
                on THIS label).
    position: where to place the patch (x, y).
    epsilon: step size for each gradient ascent iteration.
    steps: number of iterations.
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
        # Gradient ASCENT (+=, not -=): we want to INCREASE the loss (make
        # the model wrong), not minimize it like in normal training.
        patch.assign_add(epsilon * tf.sign(grad))
        patch.assign(tf.clip_by_value(patch, 0, 255))

    return patch.numpy()


def sanitize(image: np.ndarray, blur_ksize: int = 5) -> np.ndarray:
    """
    Defense: Gaussian blur before inference. Adversarial patches rely on
    precise pixel-by-pixel perturbations (high frequency); blurring the
    image destroys them, while the "real" content (low frequency: eye
    shape, general brightness) remains recognizable.
    """
    blurred = cv2.GaussianBlur(image.astype("uint8"), (blur_ksize, blur_ksize), 0)
    return blurred.astype("float32")
