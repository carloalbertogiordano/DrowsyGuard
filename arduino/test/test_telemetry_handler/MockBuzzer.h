#pragma once

#include "IBuzzer.h"

// Mock for native (PC) tests: does not drive any real pin, just records
// whether/how many times start()/stop() were called -- same role as the
// unittest.mock mocks on the Python side (e.g. mock_pwm_instance.start.assert_called...).
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
