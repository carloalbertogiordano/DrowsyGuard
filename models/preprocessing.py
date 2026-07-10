"""
Preprocessing condiviso: conversione a luminanza (canale Y di YCbCr) su
immagine quadrata. Nessun crop, nessun filtro (cascade Haar abbandonato:
troppi scarti / falsi rilevamenti, vedi discussione progetto).
"""

import numpy as np
import cv2

SQUARE_SIZE = (96, 96)


def to_luminance(image: np.ndarray) -> np.ndarray:
    """
    Costruisce un tensore a 3 canali (Y, B, R): Y = luminanza (da YCbCr),
    B e R = canali blu e rosso grezzi dall'immagine RGB originale. L'immagine
    in input e' gia' quadrata (resize fatto a monte, es. da
    flow_from_directory).

    Perche' 3 canali (non solo Y): il backend GPU Intel (ITEX/oneDNN) non
    supporta la convoluzione con input a 1 solo canale (errore "output depth
    must be evenly divisible by number of groups") -- serve comunque un
    input a 3 canali per la prima Conv2D. Il conteggio parametri della rete
    NON dipende dal contenuto dei canali (solo dal numero), quindi tanto
    vale mettere 3 canali con informazione reale (Y, B, R) invece di
    replicare Y tre volte.

    Input: (H, W, 3) RGB, valori 0..255.
    Output: (H, W, 3) float32, valori 0..255 -- canali [Y, B, R].
    """
    ycc = cv2.cvtColor(image.astype("uint8"), cv2.COLOR_RGB2YCrCb)
    y = ycc[:, :, 0]
    b = image[:, :, 2]
    r = image[:, :, 0]
    stacked = np.stack([y, b, r], axis=-1)  # (H, W) x3 -> (H, W, 3)
    return stacked.astype("float32")
