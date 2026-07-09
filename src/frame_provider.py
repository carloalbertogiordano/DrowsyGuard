import cv2
import numpy as np

from src.exceptions.VideoOpenError import VideoOpenError


class FrameProvider:
    """Gestisce l'acquisizione dei frame dalla sorgente video."""

    def __init__(self, path: str):
        self.capturer = cv2.VideoCapture(path)
        if not self.capturer.isOpened():
            # Sorgente non apribile -> errore
            raise VideoOpenError(f"Impossibile aprire il video: {path}")

    def get_frame(self) -> np.ndarray:
        """Cattura un frame come array NumPy. A fine video riparte (loop)."""
        read_success, frame = self.capturer.read()

        if not read_success:
            # Video terminato: riavvolgi alla prima frame (effetto loop)
            self.capturer.set(cv2.CAP_PROP_POS_FRAMES, 0)
            read_success, frame = self.capturer.read()

            if not read_success:
                raise VideoOpenError("Errore nella lettura del video")

        return frame
