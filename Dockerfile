# ==============================================================================
# Multi-stage Dockerfile for Clip Cup
# Stage 1: Build React Vite Frontend
# Stage 2: Python Backend with OpenCV, FFmpeg, and Production Environment
# ==============================================================================

# ----------------- Stage 1: Frontend Build -----------------
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ----------------- Stage 2: Backend & Runtime -----------------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies: FFmpeg, OpenGL/GLib for OpenCV, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

# Download YuNet ONNX model into backend/models
RUN mkdir -p /app/backend/models && \
    curl -L -o /app/backend/models/face_detection_yunet_2023mar.onnx \
    https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

# Copy backend code
COPY backend /app/backend

# Copy built frontend static assets into backend static
COPY --from=frontend-builder /app/frontend/dist /app/frontend-dist

# Create media directory for local storage fallback
RUN mkdir -p /app/backend/media/shorts

# Apply database migrations on startup and start Gunicorn server
WORKDIR /app/backend
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn clipcup.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 900"]
