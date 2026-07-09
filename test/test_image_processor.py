import unittest
import numpy as np

from src.exceptions.FrameError import FrameError
from src.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    def test_preprocess_resizes_and_normalizes(self):
        # ARRANGE: immagine uint8 casuale con dimensione != target
        img = np.random.randint(0, 256, size=(120, 200, 3), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT: dimensione, tipo float, range [0,1]
        self.assertIsInstance(out, np.ndarray)
        self.assertEqual(out.shape, (224, 224, 3))
        self.assertTrue(np.issubdtype(out.dtype, np.floating))
        self.assertGreaterEqual(out.min(), 0.0)
        self.assertLessEqual(out.max(), 1.0)

    def test_preprocess_converts_grayscale_to_three_channels(self):
        # ARRANGE: immagine in scala di grigi (2D)
        img = np.random.randint(0, 256, size=(80, 80), dtype=np.uint8)
        proc = ImageProcessor(target_size=(224, 224))

        # ACT
        out = proc.preprocess(img)

        # ASSERT: deve diventare 3 canali
        self.assertEqual(out.shape, (224, 224, 3))

    def test_preprocess_raises_on_none_frame(self):
        proc = ImageProcessor()
        self.assertRaises(FrameError, proc.preprocess, None)


if __name__ == "__main__":
    unittest.main()
