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
    uint8_t enc_buf[BUF_MAX_LEN];
    int bytes_read = mqttClient.read((uint8_t*)enc_buf, sizeof(enc_buf)-1);

    memset(enc_buf+bytes_read, '\0', BUF_MAX_LEN-bytes_read);

    char dec_buf[BUF_MAX_LEN];
    int dec_len = aes_decrypt((const char*)enc_buf, aesKey, dec_buf, BUF_MAX_LEN);

    if (dec_len < 0) {return;}

    handler.onMessage(dec_buf, millis());
}

void setup() {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
    }

    mqttClient.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    mqttClient.subscribe(MQTT_TOPIC);
    mqttClient.onMessage(onMqttMessage);
}

void loop() {
    mqttClient.poll();
    handler.update(millis());
}
