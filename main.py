"""
Entry point: runs DrowsinessMonitor end-to-end (webcam or video file ->
preprocessing -> inference -> alert). Not covered by the unit test suite
-- manual/demo script, same treatment as train_model.py.

Usage:
    .venv/bin/python main.py                       # webcam (device 0)
    .venv/bin/python main.py --video path/to.mp4    # video file
    Ctrl+C to stop.
"""

import argparse

from src.drowsiness_monitor import DrowsinessMonitor

MODEL_PATH = "models/drowsiness_model.tflite"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--video", default="0",
        help="Video file path, or camera index (default: 0 = webcam)"
    )
    parser.add_argument("--model", default=MODEL_PATH)
    args = parser.parse_args()

    video_source = int(args.video) if args.video.isdigit() else args.video

    monitor = DrowsinessMonitor(video_path=video_source, model_path=args.model)
    try:
        monitor.run()
    except KeyboardInterrupt:
        monitor.stop()


if __name__ == "__main__":
    main()
