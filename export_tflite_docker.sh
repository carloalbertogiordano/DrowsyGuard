#!/usr/bin/env bash
# Converte models/drowsiness_model.keras in models/drowsiness_model.tflite,
# usando lo stesso container/versione TensorFlow del training (evita problemi
# di compatibilita' nel caricare il file .keras con una versione diversa).
# Non serve la GPU (conversione unica, veloce).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="intel/intel-extension-for-tensorflow:2.15.0.3-xpu-pip-base"

docker run --rm -it \
  -e TF_CPP_MIN_LOG_LEVEL=2 \
  -v "$PROJECT_DIR:/workspace" \
  -w /workspace \
  "$IMAGE" \
  python -u models/export_tflite.py

# Il container gira come root: rimette il file generato di proprieta' host.
docker run --rm \
  -v "$PROJECT_DIR:/workspace" \
  "$IMAGE" \
  chown "$(id -u):$(id -g)" /workspace/models/drowsiness_model.tflite 2>/dev/null || true
