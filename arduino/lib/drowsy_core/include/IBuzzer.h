#pragma once

// Abstract interface for the buzzer -- same role as mocks/GPIO.py on the
// Python side: the "core" code (telemetry_handler) only depends on this
// interface, never on real pins/hardware. Two implementations:
//   - RealBuzzer  (src/main.cpp, actually drives the GPIO pins on the board)
//   - MockBuzzer  (test/, records calls so they can be checked in tests)
class IBuzzer {
public:
    virtual ~IBuzzer() = default;
    virtual void start() = 0;
    virtual void stop() = 0;
};
