# 😴 DrowsyGuard — Secure Driver Drowsiness Detection

**Corso:** Embedded Systems & IoT Security
**Piattaforma:** Raspberry Pi (emulato) | **Linguaggio:** Python

## 📜 Panoramica
Sistema **real-time di rilevamento colpo di sonno** del guidatore su Raspberry Pi tramite AI.
Unisce **Embedded Engineering** e **IoT Security**. Frame video → CNN → allarme (buzzer + MQTT cifrato).

## 🏗 Architettura (Single Responsibility)
Cinque componenti core:

* **`FrameProvider`**: acquisizione frame da PiCamera o video.
* **`ImageProcessor`**: pre-processing e sanitizzazione input.
* **`InferenceEngine`**: wrapper del modello ML (TFLite).
* **`DrowsinessMonitor`**: orchestratore, controlla il loop logico.
* **`AlertNotifier`**: allarme buzzer (GPIO) + comunicazione MQTT.

## 🛡 IoT Security
1. **Attacco:** adversarial patch nel frame acceca il modello (evasion attack).
2. **Difesa:** hardening del modello contro l'attacco.
3. Telemetria MQTT cifrata con **AES-CBC**.

## 🚀 Esecuzione
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.drowsiness_monitor --video videos/drowsy1.mp4 --model models/drowsiness_model.tflite
```

## 🧪 Test
```bash
python -m unittest discover -s test
```

## 🔌 Emulazione hardware
Nessun hardware richiesto: `mocks/GPIO.py` sostituisce `RPi.GPIO` via import fallback.
