#!/usr/bin/env bash
# Allena il modello dentro il container Docker Intel ITEX (GPU Iris Xe via
# oneAPI/Level-Zero), montando questa cartella progetto dentro al container.
# Vedi models/train_model.py per lo script di training vero e proprio.
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
  bash -c "pip install --quiet 'numpy<2' 'opencv-python-headless<5' scipy pillow scikit-learn matplotlib && python -u models/train_model.py"

# Il container gira come root: rimette i file generati (modello, cache) di
# proprieta' dell'utente host invece di root.
docker run --rm \
  -v "$PROJECT_DIR:/workspace" \
  "$IMAGE" \
  chown -R "$(id -u):$(id -g)" /workspace/models /workspace/dataset /workspace/.gpu-cache 2>/dev/null || true
