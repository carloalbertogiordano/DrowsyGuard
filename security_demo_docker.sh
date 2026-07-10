#!/usr/bin/env bash
# Esegue la demo attacco adversarial patch + difesa (security/demo_adversarial.py),
# nello stesso container/versione TensorFlow del training (serve poter
# calcolare gradienti sul modello .keras, .tflite non e' differenziabile).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="intel/intel-extension-for-tensorflow:2.15.0.3-xpu-pip-base"

docker run --rm -it \
  -e TF_CPP_MIN_LOG_LEVEL=2 \
  -v "$PROJECT_DIR:/workspace" \
  -w /workspace \
  "$IMAGE" \
  bash -c "pip install --quiet 'numpy<2' 'opencv-python-headless<5' && python -u security/demo_adversarial.py"

# Il container gira come root: rimette i file generati di proprieta' host.
docker run --rm \
  -v "$PROJECT_DIR:/workspace" \
  "$IMAGE" \
  chown -R "$(id -u):$(id -g)" /workspace/security/adversarial_demo 2>/dev/null || true
