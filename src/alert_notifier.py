import logging
import time

import paho.mqtt.client as mqtt

from security.security_manager import SecurityManager
from security import key

try:
    from RPi import GPIO
    GPIO_MOCK = False
except (ImportError, RuntimeError):
    from mocks import GPIO
    GPIO_MOCK = True

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

BUZZER_PIN = 17
FREQUENCY = 440  # Hz


class AlertNotifier:

    def __init__(self):
        # GPIO config
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)

        # PWM
        self.pwm = GPIO.PWM(BUZZER_PIN, FREQUENCY)

        # MQTT
        self.server = '127.0.0.1'
        self.port = 1883
        self.topic = 'v1/devices/me/telemetry'

        # Security
        self.security = SecurityManager(key.AES_KEY)

        # Alarm status
        self.is_alert_active = False
        self.last_alarm_trigger_time = 0
        self.min_alarm_duration = 2.0
        self._connected = False

        # Client MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.connect_async(self.server, self.port, keepalive=60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logging.info("MQTT Connected")
            return

        logging.error("MQTT Connection Error")

    def _on_disconnect(self, client, userdata, rc):
        if not self._connected:
            logging.warning('MQTT disconnected')

    def publish_via_mqtt(self, timestamp: str, confidence: float):
        if not self._connected:
            return

        data = {
            "status": "DROWSY_DETECTED",
            "timestamp": timestamp,
            "probability": round(confidence, 4)
        }

        encrypted_payload = self.security.encrypt_data(data)
        self.client.publish(self.topic, encrypted_payload)

    def notify(self, drowsy_detected: bool, timestamp: str, confidence: float):
        current_time = time.time()

        if drowsy_detected:
            self.last_alarm_trigger_time = current_time
            if not self.is_alert_active:
                self.pwm.start(50)
                self.is_alert_active = True
                self.publish_via_mqtt(timestamp, confidence)
            return

        if self.is_alert_active:
            elapsed = current_time - self.last_alarm_trigger_time
            if elapsed >= self.min_alarm_duration:
                self.pwm.stop()
                self.is_alert_active = False

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup()
        self.client.loop_stop()
