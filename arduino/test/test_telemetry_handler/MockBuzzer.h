#pragma once

#include "IBuzzer.h"

// Mock per i test nativi (PC): non pilota nessun pin reale, registra solo
// se/quante volte start()/stop() sono state chiamate -- stesso ruolo dei
// mock unittest.mock lato Python (es. mock_pwm_instance.start.assert_called...).
class MockBuzzer : public IBuzzer {
public:
    int start_calls = 0;
    int stop_calls = 0;
    bool is_running = false;

    void start() override {
        start_calls++;
        is_running = true;
    }

    void stop() override {
        stop_calls++;
        is_running = false;
    }
};
