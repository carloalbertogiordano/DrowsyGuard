#pragma once

#include <Arduino.h>
#include <Arduino_LED_Matrix.h>
#include "IBuzzer.h"

// Real implementation of IBuzzer: drives an actual GPIO pin on the board.
// Counterpart of MockBuzzer (used in native tests).
//
// TEMPORARY: no physical buzzer wired yet, so start()/stop() also drive the
// Uno R4 WiFi's built-in LED matrix (monochrome 12x8, ships with the
// renesas-ra core) as a visual stand-in -- all LEDs on = alarm, off =
// cleared. Kept inside RealBuzzer (real-hardware-only, not compiled in the
// native test env) so IBuzzer/TelemetryHandler and their tests are
// untouched. Remove the matrix_ calls once the real buzzer is wired.
//
// NOTE: hardware init (pinMode/matrix_.begin()) lives in begin(), NOT the
// constructor. `buzzer` is a global object, so its constructor runs during
// C++ static init, before the board's own init() (clocks/peripherals) has
// executed. matrix_.begin() allocates an FSP hardware timer for the LED
// refresh ISR -- doing that too early makes the allocation silently fail
// (loadFrame() still "works" in software, but nothing physically lights
// up). Must call buzzer.begin() from setup(), after the board is ready.
class RealBuzzer : public IBuzzer {
public:
    explicit RealBuzzer(uint8_t pin) : pin_(pin) {}

    void begin() {
        pinMode(pin_, OUTPUT);
        digitalWrite(pin_, LOW);
        matrix_.begin();
        matrix_.clear();
    }

    void start() override {
        digitalWrite(pin_, HIGH);
        const uint32_t all_on[] = {0xffffffff, 0xffffffff, 0xffffffff};
        matrix_.loadFrame(all_on);
    }

    void stop() override {
        digitalWrite(pin_, LOW);
        matrix_.clear();
    }

private:
    uint8_t pin_;
    ArduinoLEDMatrix matrix_;
};
