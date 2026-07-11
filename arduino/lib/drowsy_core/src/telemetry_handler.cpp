#include "telemetry_handler.h"
#include <ArduinoJson.h>

TelemetryHandler::TelemetryHandler(IBuzzer& buzzer, unsigned long buzz_duration_ms)
    : buzzer_(buzzer), buzz_duration_ms_(buzz_duration_ms) {
}

void TelemetryHandler::onMessage(const char* decrypted_json, unsigned long now_ms) {
    JsonDocument jdoc;
    DeserializationError err = deserializeJson(jdoc, decrypted_json);
    
    if (err) return;
    const char* status = jdoc["status"];

    if (status == nullptr) {return;}

    if (strncmp(status, "DROWSY_DETECTED", 15) == 0) {
        last_trigger_ms_ = now_ms;
        
        if (!is_active_) {
            buzzer_.start();
            is_active_ = true;
        }
    }

    return;
}

void TelemetryHandler::update(unsigned long now_ms) {
    if (!is_active_) return;
        // Time elapsed        >= buzzer duration
    if ((now_ms - last_trigger_ms_) >= buzz_duration_ms_) {
        buzzer_.stop();
        is_active_ = false;
    }

    return;
}
