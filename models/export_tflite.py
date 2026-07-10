"""
Converts the trained Keras model (models/drowsiness_model.keras) to TFLite
(models/drowsiness_model.tflite) -- the format used by InferenceEngine
(src/inference_engine.py) at runtime.

Must be run with the SAME TensorFlow/Keras version used for training
(2.15.0.3, inside the ITEX Docker container) to avoid compatibility issues
when loading the .keras file -- see export_tflite_docker.sh.
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

    # Verify: load the .tflite and check the expected input/output shape
    interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    print(f"Verifica -- input shape: {input_details['shape']}, output shape: {output_details['shape']}")


if __name__ == "__main__":
    export()
