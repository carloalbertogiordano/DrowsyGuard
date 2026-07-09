from unittest import TestCase
from unittest.mock import patch, MagicMock, ANY
import paho.mqtt.client as mqtt

from src.alert_notifier import AlertNotifier
import mocks.GPIO as GPIO


class TestAlertNotifier(TestCase):

    @patch.object(mqtt, 'Client')
    def test_connects_to_broker_on_init(self, mock_client_class):
        # --- ARRANGE ---
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance

        # --- ACT ---
        notifier = AlertNotifier()

        # --- ASSERT ---
        mock_instance.connect_async.assert_called_with("127.0.0.1", 1883, keepalive=60)

    @patch.object(mqtt, 'Client')
    def test_publish_via_mqtt_publishes_encrypted_payload_at_right_topic(self, mock_client_class):
        # --- ARRANGE ---
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        notifier = AlertNotifier()
        notifier._connected = True

        # --- ACT ---
        notifier.publish_via_mqtt(timestamp="2026-07-09 20:12:00", confidence=0.85)

        # --- ASSERT ---
        # topic corretto, payload = ANY perche' e' cifrato (stringa diversa ogni volta per IV random)
        mock_instance.publish.assert_called_once_with("v1/devices/me/telemetry", ANY)
        # il payload pubblicato deve essere una stringa (base64), non il dict in chiaro
        published_payload = mock_instance.publish.call_args[0][1]
        self.assertIsInstance(published_payload, str)

    @patch.object(mqtt, 'Client')
    def test_notify_does_not_publish_multiple_times_while_drowsy_persists(self, mock_client_class):
        # --- ARRANGE ---
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        notifier = AlertNotifier()
        notifier._connected = True

        # --- ACT 1: primo rilevamento ---
        notifier.notify(drowsy_detected=True, timestamp="10:00:00", confidence=0.90)

        # --- ASSERT 1 ---
        self.assertTrue(notifier.is_alert_active)
        mock_instance.publish.assert_called_once()

        mock_instance.publish.reset_mock()

        # --- ACT 2: rilevamento consecutivo (stesso stato) ---
        notifier.notify(drowsy_detected=True, timestamp="10:00:01", confidence=0.92)

        # --- ASSERT 2: nessuna nuova pubblicazione ---
        mock_instance.publish.assert_not_called()

    @patch.object(mqtt, 'Client')
    @patch('time.time')
    def test_resets_alert_state_after_min_duration_when_drowsy_stops(self, mock_time, mock_client_class):
        # --- ARRANGE ---
        mock_client_class.return_value = MagicMock()
        notifier = AlertNotifier()
        notifier.is_alert_active = True
        notifier.last_alarm_trigger_time = 1000.0
        mock_time.return_value = 1005.0  # 5s dopo, > min_alarm_duration (2s)

        # --- ACT ---
        notifier.notify(drowsy_detected=False, timestamp="12:00:00", confidence=0.0)

        # --- ASSERT ---
        self.assertFalse(notifier.is_alert_active)

    @patch('src.alert_notifier.mqtt.Client')
    @patch.object(GPIO, "PWM")
    def test_buzzer_starts_when_drowsy_detected(self, mock_pwm_class, mock_mqtt_class):
        # --- ARRANGE ---
        mock_pwm_instance = MagicMock()
        mock_pwm_class.return_value = mock_pwm_instance
        mock_mqtt_class.return_value = MagicMock()
        notifier = AlertNotifier()
        notifier._connected = True

        # --- ACT ---
        notifier.notify(drowsy_detected=True, timestamp="12:00:00", confidence=0.9)

        # --- ASSERT ---
        mock_pwm_instance.start.assert_called_once_with(50)

    @patch('src.alert_notifier.mqtt.Client')
    @patch.object(GPIO, "PWM")
    @patch('time.time')
    def test_buzzer_stops_after_min_duration_when_drowsy_ends(self, mock_time, mock_pwm_class, mock_mqtt_class):
        # --- ARRANGE ---
        mock_pwm_instance = MagicMock()
        mock_pwm_class.return_value = mock_pwm_instance
        mock_mqtt_class.return_value = MagicMock()
        notifier = AlertNotifier()
        notifier.is_alert_active = True
        notifier.last_alarm_trigger_time = 1000.0
        mock_time.return_value = 1005.0

        # --- ACT ---
        notifier.notify(drowsy_detected=False, timestamp="12:00:00", confidence=0.9)

        # --- ASSERT ---
        mock_pwm_instance.stop.assert_called_once()
