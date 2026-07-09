import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import cv2

from src.exceptions.VideoOpenError import VideoOpenError
from src.frame_provider import FrameProvider


class TestFrameProvider(unittest.TestCase):
    @patch.object(cv2, 'VideoCapture')
    def test_get_frame_returns_numpy_array(self, video_capture: MagicMock):
        # --- ARRANGE ---
        fake_frame = np.zeros((10, 10, 3), dtype=np.uint8)
        mock_capturer = MagicMock()
        mock_capturer.read.return_value = (True, fake_frame)
        mock_capturer.isOpened.return_value = True
        video_capture.return_value = mock_capturer

        provider = FrameProvider("dummy.mp4")

        # --- ACT ---
        result = provider.get_frame()

        # --- ASSERT ---
        self.assertIsInstance(result, np.ndarray)
        self.assertTrue(np.array_equal(result, fake_frame))

    @patch.object(cv2, 'VideoCapture')
    def test_init_raises_when_video_cannot_be_opened(self, video_capture: MagicMock):
        # --- ARRANGE ---
        mock_capturer = MagicMock()
        mock_capturer.isOpened.return_value = False
        video_capture.return_value = mock_capturer

        # --- ACT & ASSERT ---
        self.assertRaises(VideoOpenError, FrameProvider, "bad_path.mp4")

    @patch.object(cv2, 'VideoCapture')
    def test_get_frame_loops_video_when_it_ends(self, video_capture: MagicMock):
        # --- ARRANGE ---
        fake_frame = np.zeros((10, 10, 3), dtype=np.uint8)
        mock_capturer = MagicMock()
        mock_capturer.isOpened.return_value = True
        # prima lettura fallisce (video finito), seconda riparte da capo
        mock_capturer.read.side_effect = [(False, None), (True, fake_frame)]
        video_capture.return_value = mock_capturer

        provider = FrameProvider("video.mp4")

        # --- ACT ---
        result = provider.get_frame()

        # --- ASSERT ---
        self.assertTrue(np.array_equal(result, fake_frame))
        mock_capturer.set.assert_called_with(cv2.CAP_PROP_POS_FRAMES, 0)


if __name__ == "__main__":
    unittest.main()
