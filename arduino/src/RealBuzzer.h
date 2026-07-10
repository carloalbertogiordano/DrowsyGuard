#pragma once

#include <Arduino.h>
#include "IBuzzer.h"

// Implementazione reale di IBuzzer: pilota un pin GPIO vero sulla scheda.
// Controparte di MockBuzzer (usato nei test nativi).
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
