# Download OpenCV YuNet face detection ONNX model (PowerShell for Windows)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetDir = Join-Path $scriptDir "..\backend\models"
$modelFile = Join-Path $targetDir "face_detection_yunet_2023mar.onnx"
$modelUrl = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

if (Test-Path $modelFile) {
    Write-Host "Model already exists at: $modelFile"
} else {
    Write-Host "Downloading YuNet ONNX face detection model to $modelFile..."
    Invoke-WebRequest -Uri $modelUrl -OutFile $modelFile
    Write-Host "Download complete: $modelFile"
}
