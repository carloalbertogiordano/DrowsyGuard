"""
Dev tool: continuously publish an encrypted MQTT payload to smoke-test the
Arduino firmware's MQTT + AES + LED-matrix path, without running the full
camera/model pipeline. NOT covered by the unit test suite -- run manually.

"drowsy" sends the real status the system uses ("DROWSY_DETECTED", the only
status AlertNotifier ever actually publishes). "not_drowsy" sends a
synthetic, non-matching status ("NOT_DROWSY") that does not exist in the
real protocol -- it exists only to verify TelemetryHandler correctly
ignores anything that isn't "DROWSY_DETECTED" (buzzer/LED matrix stay off).

Usage:
    .venv/bin/python security/mqtt_publish_loop.py --mode drowsy
    .venv/bin/python security/mqtt_publish_loop.py --mode not_drowsy
"""

import argparse
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from security_manager import SecurityManager
import key


def build_payload(mode: str) -> dict:
    """Build the plaintext dict for the given mode, before encryption."""
    status = "DROWSY_DETECTED" if mode == "drowsy" else "NOT_DROWSY"
    probability = 0.95 if mode == "drowsy" else 0.05
    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "probability": probability,
    }


def main():
    """Connect and publish the chosen payload in a loop until Ctrl+C."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["drowsy", "not_drowsy"], required=True
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--topic", default="v1/devices/me/telemetry")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    security = SecurityManager(key.AES_KEY)
    client = mqtt.Client()
    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()

    print(f"Publishing '{args.mode}' to {args.topic} every "
          f"{args.interval}s. Ctrl+C to stop.")
    try:
        while True:
            payload = build_payload(args.mode)
            encrypted = security.encrypt_data(payload)
            client.publish(args.topic, encrypted)
            print(f"  sent: {payload}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
