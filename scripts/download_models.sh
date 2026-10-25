#!/usr/bin/env bash
# Download OpenCV YuNet face detection ONNX model
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/../backend/models"
MODEL_FILE="${TARGET_DIR}/face_detection_yunet_2023mar.onnx"
MODEL_URL="https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"

mkdir -p "${TARGET_DIR}"

if [ -f "${MODEL_FILE}" ]; then
    echo "Model already exists at: ${MODEL_FILE}"
else
    echo "Downloading YuNet ONNX face detection model..."
    curl -L -o "${MODEL_FILE}" "${MODEL_URL}"
    echo "Download complete: ${MODEL_FILE}"
fi
