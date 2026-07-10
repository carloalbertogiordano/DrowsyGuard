#!/usr/bin/env bash
# Valuta un modello gia' addestrato (models/drowsiness_model.keras) senza
# rifare il training: classification report, confusion matrix, ROC curve.
# Utile dopo un training completato con successo ma con la valutazione
# fallita/saltata.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="intel/intel-extension-for-tensorflow:2.15.0.3-xpu-pip-base"

mkdir -p "$PROJECT_DIR/.gpu-cache"

docker run --rm -it \
  --device /dev/dri \
  -e ONEDNN_VERBOSE=0 \
  -e TF_CPP_MIN_LOG_LEVEL=2 \
  -e NEO_CACHE_PERSISTENT=1 \
  -e NEO_CACHE_DIR=/workspace/.gpu-cache \
  -v "$PROJECT_DIR:/workspace" \
  -w /workspace \
  "$IMAGE" \
  bash -c "pip install --quiet 'numpy<2' 'opencv-python-headless<5' scipy pillow scikit-learn matplotlib && python -u -c '
import os
import sys
sys.path.insert(0, \"models\")
from tensorflow.keras.models import load_model
from train_model import build_generators, evaluate, OUTPUT_MODEL_PATH, EVAL_DIR

print(f\"Carico modello: {OUTPUT_MODEL_PATH}\")
model = load_model(OUTPUT_MODEL_PATH)
_, val_gen = build_generators()
os.makedirs(EVAL_DIR, exist_ok=True)
evaluate(model, val_gen)
'"

docker run --rm \
  -v "$PROJECT_DIR:/workspace" \
  "$IMAGE" \
  chown -R "$(id -u):$(id -g)" /workspace/models /workspace/.gpu-cache 2>/dev/null || true
