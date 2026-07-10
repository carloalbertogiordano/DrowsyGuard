#pragma once

#include "IBuzzer.h"

// Logica di stato del buzzer: equivalente C++ di AlertNotifier.notify() lato
// Python, ma adattata al fatto che via MQTT arrivano SOLO messaggi di
// "inizio allarme" (mai un messaggio esplicito di stop -- vedi
// AlertNotifier.publish_via_mqtt, chiamato solo quando drowsy_detected
// diventa True). Il buzzer si spegne quindi da solo dopo un timeout.
class TelemetryHandler {
public:
    // buzz_duration_ms: per quanto tempo restare accesi dopo un trigger,
    // se non arrivano altri messaggi nel frattempo.
    TelemetryHandler(IBuzzer& buzzer, unsigned long buzz_duration_ms);

    // Chiamata quando arriva un payload JSON GIA' DECIFRATO (stringa).
    // Se contiene "status":"DROWSY_DETECTED", attiva il buzzer (se non gia'
    // attivo) e aggiorna il timestamp dell'ultimo trigger.
    // now_ms: timestamp corrente in ms (iniettato, non letto da millis()
    // qui dentro -- serve per poter controllare il tempo nei test, stesso
    // principio di @patch('time.time') lato Python).
    void onMessage(const char* decrypted_json, unsigned long now_ms);

    // Va chiamata periodicamente (nel loop() reale). Spegne il buzzer se e'
    // trascorso buzz_duration_ms dall'ultimo trigger.
    void update(unsigned long now_ms);

private:
    IBuzzer& buzzer_;
    unsigned long buzz_duration_ms_;
    unsigned long last_trigger_ms_ = 0;
    bool is_active_ = false;
};
