import cv2
import argparse
from datetime import datetime
import time
from collections import deque
import numpy as np

from src.frame_provider import FrameProvider
from src.image_processor import ImageProcessor
from src.inference_engine import InferenceEngine
from src.alert_notifier import AlertNotifier


class DrowsinessMonitor:

    def __init__(self, video_path: str, model_path: str):
        self.inference_engine = InferenceEngine(model_path=model_path)
        req_w = self.inference_engine.width
        req_h = self.inference_engine.height
        self.image_processor = ImageProcessor(target_size=[req_w, req_h])
        self.frame_provider = FrameProvider(path=video_path)
        self.alert_notifier = AlertNotifier()
        self.is_running = True
        self.threshold = 0.70
        self.window_size = 5
        self.prob_buffer = deque(maxlen=self.window_size)

    def run(self):
        while self.is_running:
            frame = self.frame_provider.get_frame()
            if frame is None:
                self._cleanup()
                break
            input_tensor = self.image_processor.preprocess(frame)
            confidence = self.inference_engine.predict(input_tensor)
            self.prob_buffer.append(confidence)
            avg_confidence = sum(x for x in self.prob_buffer) / len(self.prob_buffer)

            is_drowsy = avg_confidence > self.threshold
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.alert_notifier.notify(drowsy_detected=is_drowsy, timestamp=timestamp, confidence=avg_confidence)
            self._display_frame(frame, is_drowsy, avg_confidence)

    def _display_frame(self, frame, is_drowsy, confidence, fps=0.0):
        cv2.imshow("Drowsiness Monitor", frame)

    def stop(self):
        self.is_running = False

    def _cleanup(self):
        cv2.destroyAllWindows()