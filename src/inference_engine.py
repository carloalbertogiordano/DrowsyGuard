import os
import numpy as np

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite


class InferenceEngine:

    def __init__(self, model_path=None):
        # Model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found on path {model_path}")
        # Alloc interpreter
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        # Save index
        self.input_index = self.interpreter.get_input_details()[0]['index']
        self.output_index = self.interpreter.get_output_details()[0]['index']
        input_shape = self.interpreter.get_input_details()[0]['shape']
        self.height = input_shape[1]
        self.width = input_shape[2]

    def predict(self, processed_image: np.ndarray) -> float:
        img = processed_image.astype(np.float32)

        # Expand image dim for numpy
        if img.ndim == 3:
            img = np.expand_dims(img, axis=0)   # (224,224,3) --> (1,224,224,3)

        # Load data
        self.interpreter.set_tensor(self.input_index, img)

        # Execute
        self.interpreter.invoke()

        # Read result
        output_data = self.interpreter.get_tensor(self.output_index)
        return float(output_data.flatten()[0])
