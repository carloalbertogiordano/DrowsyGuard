#pragma once

#include <Arduino.h>
#include "IBuzzer.h"

// Real implementation of IBuzzer: drives an actual GPIO pin on the board.
// Counterpart of MockBuzzer (used in native tests).
class RealBuzzer : public IBuzzer {
public:
    explicit RealBuzzer(uint8_t pin) : pin_(pin) {
        pinMode(pin_, OUTPUT);
        digitalWrite(pin_, LOW);
    }

    void start() override {
        digitalWrite(pin_, HIGH);
    }

    void stop() override {
        digitalWrite(pin_, LOW);
    }

private:
    uint8_t pin_;
};
