import cv2
import numpy as np
import numpy.typing as npt
from src.exceptions.FrameError import FrameError


class ImageProcessor:

    def __init__(self, target_size: list[int] = (224, 224)):
        self.target_size = target_size

    def image_to_color_image(self, image: np.ndarray):
        if image.ndim == 2:  # if grayscale
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def preprocess(self, image: np.ndarray) -> npt.NDArray:

        if image is None:
            raise FrameError
        # Correct Colour
        img = self.image_to_color_image(image)

        # Correct size
        img = cv2.resize(img, self.target_size)

        # Correct data type
        img = img.astype("float32") / 255.0

        return img
