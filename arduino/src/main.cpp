#include <Arduino.h>
#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
#include "secrets.h"
#include "RealBuzzer.h"
#include "telemetry_handler.h"
#include "aes_decrypt.h"
#include <stdlib.h>

#define BUF_MAX_LEN 300

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);
RealBuzzer buzzer(2);  // GPIO pin 2, change if needed
TelemetryHandler handler(buzzer, 2000);
const uint8_t aesKey[32] = AES_KEY_BYTES;

void onMqttMessage(int messageSize) {
    Serial.print("[MQTT] message received, size=");
    Serial.println(messageSize);

    uint8_t enc_buf[BUF_MAX_LEN];
    int bytes_read = mqttClient.read((uint8_t*)enc_buf, sizeof(enc_buf)-1);
    Serial.print("[MQTT] bytes_read=");
    Serial.println(bytes_read);

    memset(enc_buf+bytes_read, '\0', BUF_MAX_LEN-bytes_read);

    char dec_buf[BUF_MAX_LEN];
    int dec_len = aes_decrypt((const char*)enc_buf, aesKey, dec_buf, BUF_MAX_LEN);
    Serial.print("[AES] dec_len=");
    Serial.println(dec_len);

    if (dec_len < 0) {
        Serial.println("[AES] decrypt FAILED (bad key/IV/padding), message dropped");
        return;
    }

    Serial.print("[AES] decrypted payload: ");
    Serial.println(dec_buf);

    handler.onMessage(dec_buf, millis());
    Serial.println("[HANDLER] onMessage() called");
}

void setup() {
    Serial.begin(115200);
    delay(2000);  // give the serial monitor time to attach
    Serial.println();
    Serial.println("=== DrowsyGuard Arduino companion booting ===");

    buzzer.begin();
    Serial.println("[HW] buzzer/LED matrix initialized");

    Serial.println("[WiFi] scanning nearby networks...");
    int numNetworks = WiFi.scanNetworks();
    Serial.print("[WiFi] found ");
    Serial.print(numNetworks);
    Serial.println(" networks:");
    for (int i = 0; i < numNetworks; i++) {
        Serial.print("  ");
        Serial.print(WiFi.SSID(i));
        Serial.print("  RSSI=");
        Serial.print(WiFi.RSSI(i));
        Serial.println(" dBm");
    }

    Serial.print("[WiFi] connecting to SSID: ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print("[WiFi] status=");
        Serial.print(WiFi.status());
        Serial.println(" (0=IDLE 1=NO_SSID_AVAIL 3=CONNECTED 4=CONNECT_FAILED 6=DISCONNECTED)");
    }
    Serial.println();
    Serial.print("[WiFi] connected, IP: ");
    Serial.println(WiFi.localIP());

    Serial.print("[MQTT] connecting to broker: ");
    Serial.print(MQTT_BROKER_HOST);
    Serial.print(":");
    Serial.println(MQTT_BROKER_PORT);
    if (mqttClient.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)) {
        Serial.println("[MQTT] connected");
    } else {
        Serial.print("[MQTT] connection FAILED, error code: ");
        Serial.println(mqttClient.connectError());
    }

    bool subscribed = mqttClient.subscribe(MQTT_TOPIC);
    Serial.print("[MQTT] subscribe(");
    Serial.print(MQTT_TOPIC);
    Serial.print(") -> ");
    Serial.println(subscribed ? "ok" : "FAILED");

    mqttClient.onMessage(onMqttMessage);
    Serial.println("=== setup() done, entering loop() ===");
}

void loop() {
    if (!mqttClient.connected()) {
        Serial.println("[MQTT] lost connection, reconnecting...");
        if (mqttClient.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)) {
            Serial.println("[MQTT] reconnected");
            mqttClient.subscribe(MQTT_TOPIC);
        } else {
            Serial.print("[MQTT] reconnect FAILED, error code: ");
            Serial.println(mqttClient.connectError());
            delay(1000);
        }
    }

    mqttClient.poll();
    handler.update(millis());
}
