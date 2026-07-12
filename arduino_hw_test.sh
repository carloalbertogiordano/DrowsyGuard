#!/usr/bin/env bash
# Test manuale su hardware reale: build/flash del firmware Arduino Uno R4
# WiFi + invio in loop di messaggi MQTT cifrati (drowsy / not_drowsy) per
# verificare che la LED matrix reagisca senza dover passare dalla pipeline
# camera/modello. Vedi security/mqtt_publish_loop.py per il publisher.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARDUINO_DIR="$REPO_ROOT/arduino"
PYTHON="$REPO_ROOT/.venv/bin/python"

MQTT_HOST="127.0.0.1"
MQTT_PORT="1883"
MQTT_TOPIC="v1/devices/me/telemetry"

ask_yes_no() {
    local prompt="$1" reply
    read -r -p "$prompt [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]]
}

step4_exit() {
    echo "Uscita."
    exit 0
}

step3_mqtt() {
    echo "Broker atteso su $MQTT_HOST:$MQTT_PORT (topic: $MQTT_TOPIC)."
    if ! (exec 3<>"/dev/tcp/$MQTT_HOST/$MQTT_PORT") 2>/dev/null; then
        echo "ATTENZIONE: impossibile raggiungere il broker ($MQTT_HOST:$MQTT_PORT)."
        echo "Controlla che 'docker compose up -d' sia stato lanciato."
    fi

    while true; do
        echo
        echo "1) invia 'drowsy' in continuo"
        echo "2) invia 'not_drowsy' in continuo"
        echo "3) esci"
        read -r -p "> " choice
        case "$choice" in
            1)
                "$PYTHON" "$REPO_ROOT/security/mqtt_publish_loop.py" \
                    --mode drowsy --host "$MQTT_HOST" --port "$MQTT_PORT" --topic "$MQTT_TOPIC"
                ;;
            2)
                "$PYTHON" "$REPO_ROOT/security/mqtt_publish_loop.py" \
                    --mode not_drowsy --host "$MQTT_HOST" --port "$MQTT_PORT" --topic "$MQTT_TOPIC"
                ;;
            3)
                step4_exit
                ;;
            *)
                echo "Scelta non valida."
                ;;
        esac
    done
}

step2_flash() {
    if ask_yes_no "Flashare il firmware sulla board?"; then
        (cd "$ARDUINO_DIR" && pio run -e uno_r4_wifi -t upload)
        step3_mqtt
    else
        step4_exit
    fi
}

step1_build() {
    if ask_yes_no "Compilare il firmware Arduino (uno_r4_wifi)?"; then
        (cd "$ARDUINO_DIR" && pio run -e uno_r4_wifi)
        step2_flash
    else
        step3_mqtt
    fi
}

step1_build
