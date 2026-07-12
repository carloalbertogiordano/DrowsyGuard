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

logging.basicConfig(
    level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s'
)

BUZZER_PIN = 17
FREQUENCY = 440  # Hz

# How often to re-publish while drowsy_detected stays True. Must stay well
# under the Arduino's own buzz_duration_ms (2000ms, telemetry_handler.cpp):
# the Arduino has no notion of "still active", it just self-times-out after
# its last received message. Without a keep-alive, a drowsy episode longer
# than 2s would go dark on the physical alarm while Python still correctly
# considers it active, since notify() only used to publish on the initial
# False->True transition.
REPUBLISH_INTERVAL = 1.0  # seconds


class AlarmState:
    """
    Encapsulates the alarm's start/stop hysteresis logic (min duration
    before turning off), independent of MQTT/GPIO. Extracted from
    AlertNotifier to reduce instance attribute count (pylint R0902) and to
    make the timing logic testable on its own.
    """

    def __init__(self, min_duration: float):
        self.min_duration = min_duration
        self.is_active = False
        self.last_trigger_time = 0

    def trigger(self, current_time: float) -> bool:
        """Records a trigger event. Returns True only on the transition
        from inactive to active (i.e. the alarm just started)."""
        self.last_trigger_time = current_time
        if not self.is_active:
            self.is_active = True
            return True
        return False

    def maybe_clear(self, current_time: float) -> bool:
        """Turns the alarm off if min_duration has elapsed since the last
        trigger. Returns True only on the transition from active to
        inactive (i.e. the alarm was just turned off)."""
        if not self.is_active:
            return False
        elapsed = current_time - self.last_trigger_time
        if elapsed >= self.min_duration:
            self.is_active = False
            return True
        return False


class MqttConfig:
    """Groups the MQTT connection parameters into a single value object."""

    def __init__(self, server: str, port: int, topic: str):
        self.server = server
        self.port = port
        self.topic = topic


class AlertNotifier:

    def __init__(self):
        # GPIO config
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)

        # PWM
        self.pwm = GPIO.PWM(BUZZER_PIN, FREQUENCY)

        # MQTT
        self.mqtt_config = MqttConfig(
            server='127.0.0.1', port=1883, topic='v1/devices/me/telemetry'
        )

        # Security
        self.security = SecurityManager(key.AES_KEY)

        # Alarm state
        self.alarm_state = AlarmState(min_duration=2.0)
        self._connected = False
        self._last_publish_time = 0

        # Client MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.connect_async(
            self.mqtt_config.server, self.mqtt_config.port, keepalive=60
        )
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
        self.client.publish(self.mqtt_config.topic, encrypted_payload)

    def notify(self, drowsy_detected: bool, timestamp: str, confidence: float):
        current_time = time.time()

        if drowsy_detected:
            just_activated = self.alarm_state.trigger(current_time)
            if just_activated:
                self.pwm.start(50)
                self.publish_via_mqtt(timestamp, confidence)
                self._last_publish_time = current_time
            elif current_time - self._last_publish_time >= REPUBLISH_INTERVAL:
                # Keep-alive: alarm is already active, but the Arduino
                # needs a fresh message before its own timeout expires.
                self.publish_via_mqtt(timestamp, confidence)
                self._last_publish_time = current_time
            return

        just_deactivated = self.alarm_state.maybe_clear(current_time)
        if just_deactivated:
            self.pwm.stop()

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup()
        self.client.loop_stop()
