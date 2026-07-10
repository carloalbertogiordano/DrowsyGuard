"""
Converte il modello Keras allenato (models/drowsiness_model.keras) in TFLite
(models/drowsiness_model.tflite) -- formato usato da InferenceEngine
(src/inference_engine.py) a runtime.

Va eseguito con la STESSA versione di TensorFlow/Keras usata per il training
(2.15.0.3, dentro il container Docker ITEX) per evitare problemi di
compatibilita' nel caricamento del file .keras -- vedi export_tflite_docker.sh.
"""

import os

import tensorflow as tf

KERAS_MODEL_PATH = os.path.join("models", "drowsiness_model.keras")
TFLITE_MODEL_PATH = os.path.join("models", "drowsiness_model.tflite")


def export():
    if not os.path.exists(KERAS_MODEL_PATH):
        print(f"ERRORE: manca '{KERAS_MODEL_PATH}'. Allena prima il modello (train_model.py).")
        return

    print(f"Carico modello: {KERAS_MODEL_PATH}")
    model = tf.keras.models.load_model(KERAS_MODEL_PATH)

    print("Conversione in TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    with open(TFLITE_MODEL_PATH, "wb") as f:
        f.write(tflite_model)

    keras_size = os.path.getsize(KERAS_MODEL_PATH) / 1024
    tflite_size = os.path.getsize(TFLITE_MODEL_PATH) / 1024
    print(f"Modello TFLite salvato in: {TFLITE_MODEL_PATH}")
    print(f"Dimensione: {keras_size:.1f} KB (.keras) -> {tflite_size:.1f} KB (.tflite)")

    # Verifica: carica il .tflite e controlla input/output shape attesi
    interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    print(f"Verifica -- input shape: {input_details['shape']}, output shape: {output_details['shape']}")


if __name__ == "__main__":
    export()
