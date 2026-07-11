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

    def to_luminate(self, image: np.ndarray):
        ycc = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        y = ycc[:, :, 0]
        b = image[:, :, 2]
        r = image[:, :, 0]

        return np.stack([y, b, r], axis=-1)

    def preprocess(self, image: np.ndarray) -> npt.NDArray:

        if image is None:
            raise FrameError
        # Correct colour
        img = self.image_to_color_image(image)

        # Correct size
        img = cv2.resize(img, self.target_size)

        # Model trained on luminance
        img = self.to_luminate(img)

        # Correct data type
        img = img.astype("float32") / 255.0

        return img
