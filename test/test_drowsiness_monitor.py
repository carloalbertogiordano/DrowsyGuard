import unittest
from unittest.mock import MagicMock, patch, ANY
import numpy as np

from src.drowsiness_monitor import DrowsinessMonitor


class TestDrowsinessMonitor(unittest.TestCase):

    def setUp(self):
        self.dummy_frame = np.zeros((224, 224, 3), dtype=np.uint8)

    @patch('src.drowsiness_monitor.cv2')
    @patch('src.drowsiness_monitor.AlertNotifier')
    @patch('src.drowsiness_monitor.InferenceEngine')
    @patch('src.drowsiness_monitor.ImageProcessor')
    @patch('src.drowsiness_monitor.FrameProvider')
    def test_drowsy_detected_logic(self, MockProvider, MockProcessor, MockEngine, MockNotifier, MockCv2):
        mock_provider_instance = MockProvider.return_value
        mock_provider_instance.get_frame.side_effect = [self.dummy_frame, None]
        mock_provider_instance.capturer.get.return_value = 30

        mock_engine_instance = MockEngine.return_value
        mock_engine_instance.predict.return_value = 0.9
        mock_engine_instance.width = 224
        mock_engine_instance.height = 224

        mock_notifier_instance = MockNotifier.return_value

        monitor = DrowsinessMonitor("dummy.mp4", "dummy.tflite")
        monitor.run()

        mock_notifier_instance.notify.assert_called_with(
            drowsy_detected=True,
            timestamp=ANY,
            confidence=0.9
        )

    @patch('src.drowsiness_monitor.cv2')
    @patch('src.drowsiness_monitor.AlertNotifier')
    @patch('src.drowsiness_monitor.InferenceEngine')
    @patch('src.drowsiness_monitor.ImageProcessor')
    @patch('src.drowsiness_monitor.FrameProvider')
    def test_no_drowsy_logic(self, MockProvider, MockProcessor, MockEngine, MockNotifier, MockCv2):
        mock_provider_instance = MockProvider.return_value
        mock_provider_instance.get_frame.side_effect = [self.dummy_frame, None]

        mock_engine_instance = MockEngine.return_value
        mock_engine_instance.predict.return_value = 0.1
        mock_engine_instance.width = 224
        mock_engine_instance.height = 224

        mock_notifier_instance = MockNotifier.return_value

        monitor = DrowsinessMonitor("dummy.mp4", "dummy.tflite")
        monitor.run()

        mock_notifier_instance.notify.assert_called_with(
            drowsy_detected=False,
            timestamp=ANY,
            confidence=0.1
        )

    @patch('src.drowsiness_monitor.cv2')
    @patch('src.drowsiness_monitor.AlertNotifier')
    @patch('src.drowsiness_monitor.InferenceEngine')
    @patch('src.drowsiness_monitor.ImageProcessor')
    @patch('src.drowsiness_monitor.FrameProvider')
    def test_video_end_handling(self, MockProvider, MockProcessor, MockEngine, MockNotifier, MockCv2):
        mock_provider_instance = MockProvider.return_value
        mock_provider_instance.get_frame.return_value = None

        mock_engine_instance = MockEngine.return_value
        mock_engine_instance.width = 224
        mock_engine_instance.height = 224

        monitor = DrowsinessMonitor("dummy.mp4", "dummy.tflite")
        monitor.run()

        mock_engine_instance.predict.assert_not_called()
        MockCv2.destroyAllWindows.assert_called()

    @patch('src.drowsiness_monitor.cv2')
    @patch('src.drowsiness_monitor.AlertNotifier')
    @patch('src.drowsiness_monitor.InferenceEngine')
    @patch('src.drowsiness_monitor.ImageProcessor')
    @patch('src.drowsiness_monitor.FrameProvider')
    def test_video_end_also_cleans_up_the_alert_notifier(
        self, MockProvider, MockProcessor, MockEngine, MockNotifier, MockCv2
    ):
        # Real bug found via coverage: AlertNotifier.cleanup() (stops the
        # buzzer, releases GPIO, stops the MQTT loop) exists but was never
        # called anywhere -- _cleanup() only closed the cv2 window. On real
        # hardware this means GPIO pins are never released on shutdown.
        mock_provider_instance = MockProvider.return_value
        mock_provider_instance.get_frame.return_value = None

        mock_engine_instance = MockEngine.return_value
        mock_engine_instance.width = 224
        mock_engine_instance.height = 224

        mock_notifier_instance = MockNotifier.return_value

        monitor = DrowsinessMonitor("dummy.mp4", "dummy.tflite")
        monitor.run()

        mock_notifier_instance.cleanup.assert_called_once()

    @patch('src.drowsiness_monitor.cv2')
    @patch('src.drowsiness_monitor.AlertNotifier')
    @patch('src.drowsiness_monitor.InferenceEngine')
    @patch('src.drowsiness_monitor.ImageProcessor')
    @patch('src.drowsiness_monitor.FrameProvider')
    def test_q_keypress_stops_the_monitor(self, MockProvider, MockProcessor, MockEngine, MockNotifier, MockCv2):
        mock_provider_instance = MockProvider.return_value
        # single frame: after handling 'q', is_running goes False and the
        # loop exits on its own, no second get_frame() call needed
        mock_provider_instance.get_frame.side_effect = [self.dummy_frame]

        mock_engine_instance = MockEngine.return_value
        mock_engine_instance.predict.return_value = 0.1
        mock_engine_instance.width = 224
        mock_engine_instance.height = 224

        # waitKey must return a real int (not a further MagicMock) for the
        # "& 0xFF == ord('q')" bitwise check to behave like real cv2
        MockCv2.waitKey.return_value = ord('q')

        monitor = DrowsinessMonitor("dummy.mp4", "dummy.tflite")
        monitor.run()

        self.assertFalse(monitor.is_running)


if __name__ == "__main__":
    unittest.main()
