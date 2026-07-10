import cv2
import numpy as np

from src.exceptions.VideoOpenError import VideoOpenError


class FrameProvider:
    """Handles frame acquisition from the video source."""

    def __init__(self, path: str):
        self.capturer = cv2.VideoCapture(path)
        if not self.capturer.isOpened():
            # Source not openable -> error
            raise VideoOpenError(f"Could not open video: {path}")

    def get_frame(self) -> np.ndarray:
        """Captures a frame as a NumPy array. Loops back to start at end of video."""
        read_success, frame = self.capturer.read()

        if not read_success:
            # Video ended: rewind to the first frame (loop effect)
            self.capturer.set(cv2.CAP_PROP_POS_FRAMES, 0)
            read_success, frame = self.capturer.read()

            if not read_success:
                raise VideoOpenError("Error reading video")

        return frame
