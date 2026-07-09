from unittest import TestCase
from unittest.mock import patch
import numpy as np

import src.inference_engine as ie_module


class TestInferenceEngine(TestCase):

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_loads_model_with_given_path(self, mock_exists, mock_interpreter_class):
        """L'Interpreter deve essere istanziato con il percorso corretto."""
        # --- ARRANGE ---
        mock_exists.return_value = True
        mock_interpreter_instance = mock_interpreter_class.return_value
        mock_interpreter_instance.get_input_details.return_value = [
            {'index': 0, 'shape': [1, 224, 224, 3]}
        ]
        mock_interpreter_instance.get_output_details.return_value = [{'index': 0}]

        # --- ACT ---
        ie_module.InferenceEngine(model_path="models/dummy.tflite")

        # --- ASSERT ---
        mock_interpreter_class.assert_called_once_with(model_path="models/dummy.tflite")
        mock_interpreter_instance.allocate_tensors.assert_called_once()

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_predict_returns_float(self, mock_exists, mock_interpreter_class):
        """predict deve eseguire il flusso TFLite e ritornare una probabilita' float."""
        # --- ARRANGE ---
        mock_exists.return_value = True
        mock_interpreter_instance = mock_interpreter_class.return_value

        mock_interpreter_instance.get_input_details.return_value = [
            {'index': 10, 'shape': [1, 224, 224, 3]}
        ]
        mock_interpreter_instance.get_output_details.return_value = [{'index': 20}]

        # Il "risultato" finto dell'inferenza
        mock_interpreter_instance.get_tensor.return_value = np.array([[0.8]], dtype=np.float32)

        engine = ie_module.InferenceEngine(model_path="models/dummy.tflite")
        img = np.random.rand(224, 224, 3).astype(np.float32)

        # --- ACT ---
        prob = engine.predict(img)

        # --- ASSERT ---
        self.assertIsInstance(prob, float)
        self.assertAlmostEqual(prob, 0.8, places=6)

        mock_interpreter_instance.set_tensor.assert_called_once()
        mock_interpreter_instance.invoke.assert_called_once()
        mock_interpreter_instance.get_tensor.assert_called_with(20)

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_raises_when_model_file_missing(self, mock_exists, mock_interpreter_class):
        """Se il file .tflite non esiste, deve sollevare FileNotFoundError."""
        # --- ARRANGE ---
        mock_exists.return_value = False

        # --- ACT & ASSERT ---
        self.assertRaises(
            FileNotFoundError,
            ie_module.InferenceEngine,
            model_path="models/non_esiste.tflite"
        )
