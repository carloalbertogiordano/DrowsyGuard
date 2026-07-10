#pragma once

#include "IBuzzer.h"

// Buzzer state logic: C++ equivalent of AlertNotifier.notify() on the
// Python side, but adapted to the fact that only "alarm start" messages
// ever arrive via MQTT (never an explicit stop message -- see
// AlertNotifier.publish_via_mqtt, only called when drowsy_detected
// becomes True). The buzzer therefore turns itself off after a timeout.
class TelemetryHandler {
public:
    // buzz_duration_ms: how long to stay on after a trigger, if no other
    // messages arrive in the meantime.
    TelemetryHandler(IBuzzer& buzzer, unsigned long buzz_duration_ms);

    // Called when an ALREADY DECRYPTED JSON payload (string) arrives.
    // If it contains "status":"DROWSY_DETECTED", activates the buzzer (if
    // not already active) and updates the last-trigger timestamp.
    // now_ms: current timestamp in ms (injected, not read from millis()
    // in here -- needed to control time in tests, same principle as
    // @patch('time.time') on the Python side).
    void onMessage(const char* decrypted_json, unsigned long now_ms);

    // Must be called periodically (in the real loop()). Turns the buzzer
    // off if buzz_duration_ms has elapsed since the last trigger.
    void update(unsigned long now_ms);

private:
    IBuzzer& buzzer_;
    unsigned long buzz_duration_ms_;
    unsigned long last_trigger_ms_ = 0;
    bool is_active_ = false;
};
