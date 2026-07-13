import unittest
import numpy as np
import cv2

from src.exceptions.FrameError import FrameError
from src.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    def test_preprocess_returns_numpy_array(self):
        # ARRANGE: random uint8 image with a size != target
        img = np.random.randint(0, 256, size=(120, 200, 3), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT
        self.assertIsInstance(out, np.ndarray)

    def test_preprocess_resizes_to_target_shape(self):
        # ARRANGE: random uint8 image with a size != target
        img = np.random.randint(0, 256, size=(120, 200, 3), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT
        self.assertEqual(out.shape, (224, 224, 3))

    def test_preprocess_converts_to_float(self):
        # ARRANGE: random uint8 image with a size != target
        img = np.random.randint(0, 256, size=(120, 200, 3), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT
        self.assertTrue(np.issubdtype(out.dtype, np.floating))

    def test_preprocess_normalizes_lower_bound(self):
        # ARRANGE: random uint8 image with a size != target
        img = np.random.randint(0, 256, size=(120, 200, 3), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT
        self.assertGreaterEqual(out.min(), 0.0)

    def test_preprocess_normalizes_upper_bound(self):
        # ARRANGE: random uint8 image with a size != target
        img = np.random.randint(0, 256, size=(120, 200, 3), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT
        self.assertLessEqual(out.max(), 1.0)

    def test_preprocess_converts_grayscale_to_three_channels(self):
        # ARRANGE: grayscale image (2D)
        img = np.random.randint(0, 256, size=(80, 80), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT: must become 3 channels
        self.assertEqual(out.shape, (224, 224, 3))

    def test_preprocess_raises_on_none_frame(self):
        proc = ImageProcessor()
        self.assertRaises(FrameError, proc.preprocess, None)

    def test_to_luminate_keeps_three_channels(self):
        # ARRANGE: pure red pixel image, RGB order (R=255, G=0, B=0)
        img = np.zeros((4, 4, 3), dtype=np.uint8)
        img[:, :, 0] = 255
        proc = ImageProcessor()

        # ACT
        out = proc.to_luminate(img)

        # ASSERT: shape stays 3-channel (not collapsed to a single Y plane)
        self.assertEqual(out.shape, (4, 4, 3))

    def test_to_luminate_first_channel_is_luminance(self):
        # ARRANGE: pure red pixel image, RGB order (R=255, G=0, B=0)
        img = np.zeros((4, 4, 3), dtype=np.uint8)
        img[:, :, 0] = 255
        proc = ImageProcessor()

        # ACT
        out = proc.to_luminate(img)

        # ASSERT: Y must match OpenCV's own YCrCb conversion (regression
        # guard: catches accidentally returning Y-only, or swapping/
        # mislabeling the B/R channels)
        expected_y = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)[:, :, 0]
        np.testing.assert_array_equal(out[:, :, 0], expected_y)

    def test_to_luminate_second_channel_is_raw_blue(self):
        # ARRANGE: pure red pixel image, RGB order (R=255, G=0, B=0)
        img = np.zeros((4, 4, 3), dtype=np.uint8)
        img[:, :, 0] = 255
        proc = ImageProcessor()

        # ACT
        out = proc.to_luminate(img)

        # ASSERT: channel order must be [Y, B, R] -- B is the raw input
        # channel, unchanged
        np.testing.assert_array_equal(out[:, :, 1], img[:, :, 2])

    def test_to_luminate_third_channel_is_raw_red(self):
        # ARRANGE: pure red pixel image, RGB order (R=255, G=0, B=0)
        img = np.zeros((4, 4, 3), dtype=np.uint8)
        img[:, :, 0] = 255
        proc = ImageProcessor()

        # ACT
        out = proc.to_luminate(img)

        # ASSERT: channel order must be [Y, B, R] -- R is the raw input
        # channel, unchanged
        np.testing.assert_array_equal(out[:, :, 2], img[:, :, 0])


if __name__ == "__main__":
    unittest.main()
