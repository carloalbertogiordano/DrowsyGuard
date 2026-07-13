from unittest import TestCase
from unittest.mock import patch
import numpy as np

import src.inference_engine as ie_module


class TestInferenceEngine(TestCase):

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_interpreter_created_with_given_model_path(self, mock_exists, mock_interpreter_class):
        """The Interpreter must be instantiated with the correct path."""
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

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_allocate_tensors_called_on_init(self, mock_exists, mock_interpreter_class):
        """allocate_tensors() must run once right after construction."""
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
        mock_interpreter_instance.allocate_tensors.assert_called_once()

    def _make_predict_engine(self, mock_exists, mock_interpreter_class):
        mock_exists.return_value = True
        mock_interpreter_instance = mock_interpreter_class.return_value
        mock_interpreter_instance.get_input_details.return_value = [
            {'index': 10, 'shape': [1, 224, 224, 3]}
        ]
        mock_interpreter_instance.get_output_details.return_value = [{'index': 20}]
        # The fake inference "result"
        mock_interpreter_instance.get_tensor.return_value = np.array([[0.8]], dtype=np.float32)
        engine = ie_module.InferenceEngine(model_path="models/dummy.tflite")
        return engine, mock_interpreter_instance

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_predict_returns_a_float(self, mock_exists, mock_interpreter_class):
        """predict must return a Python float, not a numpy scalar/array."""
        # --- ARRANGE ---
        engine, _ = self._make_predict_engine(mock_exists, mock_interpreter_class)
        img = np.random.rand(224, 224, 3).astype(np.float32)

        # --- ACT ---
        prob = engine.predict(img)

        # --- ASSERT ---
        self.assertIsInstance(prob, float)

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_predict_returns_correct_value(self, mock_exists, mock_interpreter_class):
        """predict must return the value produced by the interpreter."""
        # --- ARRANGE ---
        engine, _ = self._make_predict_engine(mock_exists, mock_interpreter_class)
        img = np.random.rand(224, 224, 3).astype(np.float32)

        # --- ACT ---
        prob = engine.predict(img)

        # --- ASSERT ---
        self.assertAlmostEqual(prob, 0.8, places=6)

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_predict_sets_input_tensor_once(self, mock_exists, mock_interpreter_class):
        """predict must feed the input image to the interpreter exactly once."""
        # --- ARRANGE ---
        engine, mock_interpreter_instance = self._make_predict_engine(mock_exists, mock_interpreter_class)
        img = np.random.rand(224, 224, 3).astype(np.float32)

        # --- ACT ---
        engine.predict(img)

        # --- ASSERT ---
        mock_interpreter_instance.set_tensor.assert_called_once()

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_predict_invokes_interpreter_once(self, mock_exists, mock_interpreter_class):
        """predict must run inference exactly once per call."""
        # --- ARRANGE ---
        engine, mock_interpreter_instance = self._make_predict_engine(mock_exists, mock_interpreter_class)
        img = np.random.rand(224, 224, 3).astype(np.float32)

        # --- ACT ---
        engine.predict(img)

        # --- ASSERT ---
        mock_interpreter_instance.invoke.assert_called_once()

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_predict_reads_correct_output_tensor(self, mock_exists, mock_interpreter_class):
        """predict must read the output tensor at the model's own output index."""
        # --- ARRANGE ---
        engine, mock_interpreter_instance = self._make_predict_engine(mock_exists, mock_interpreter_class)
        img = np.random.rand(224, 224, 3).astype(np.float32)

        # --- ACT ---
        engine.predict(img)

        # --- ASSERT ---
        mock_interpreter_instance.get_tensor.assert_called_with(20)

    @patch('src.inference_engine.tflite.Interpreter')
    @patch('os.path.exists')
    def test_raises_when_model_file_missing(self, mock_exists, mock_interpreter_class):
        """If the .tflite file does not exist, it must raise FileNotFoundError."""
        # --- ARRANGE ---
        mock_exists.return_value = False

        # --- ACT & ASSERT ---
        self.assertRaises(
            FileNotFoundError,
            ie_module.InferenceEngine,
            model_path="models/does_not_exist.tflite"
        )
