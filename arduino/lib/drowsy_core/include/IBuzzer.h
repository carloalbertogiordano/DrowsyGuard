#pragma once

// Interfaccia astratta per il buzzer -- stesso ruolo di mocks/GPIO.py lato
// Python: il codice "core" (telemetry_handler) dipende solo da questa
// interfaccia, mai da pin/hardware reali. Due implementazioni:
//   - RealBuzzer  (src/main.cpp, usa davvero i pin GPIO sulla scheda)
//   - MockBuzzer  (test/, registra le chiamate per verificarle nei test)
class IBuzzer {
public:
    virtual ~IBuzzer() = default;
    virtual void start() = 0;
    virtual void stop() = 0;
};
