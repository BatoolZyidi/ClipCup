---
doc: spec
status: approved
---

# Clip Cup — Technical Spec

## How This Works, In Plain Language
Clip Cup processes videos through an orchestrated 6-step pipeline: Ingestion -> Speech Transcription -> LLM Segment Selection -> OpenCV Face-Tracking Reframing -> FFmpeg Streaming Render -> S3 Storage & Presigned URL generation. Each job runs inside an isolated temporary directory that is guaranteed to be deleted immediately upon completion or error.

## Stack
- **Backend**: Python 3.12+, Django 5.x, Django REST Framework, SQLite
- **Job Execution**: ThreadPoolExecutor background worker pool (no Celery/Redis)
- **AI & Speech**: `assemblyai` SDK, `boto3` (AWS Bedrock Runtime)
- **Computer Vision & Video**: `opencv-python-headless` (OpenCV with `cv2.FaceDetectorYN` YuNet ONNX model), `ffmpeg` subprocess with pipe streaming
- **Cloud Storage**: `boto3` (AWS S3)
- **Frontend**: React (Vite) + Tailwind CSS

## Pipeline Components (backend/clipcup/pipeline/)
1. `ingest.py`: Validates direct video URL or uploaded file, enforces 10 min max, writes to temporary job directory, extracts audio stream via FFmpeg.
2. `transcribe.py`: Calls AssemblyAI with word-level timestamps, returns structured utterances with start/end time.
3. `select_segment.py`: Prompts AWS Bedrock for strict JSON `{start_ms, end_ms, topic, reason}`, validates `<= 90000ms`, snaps to utterance boundaries, retries once, falls back to highest speech density window if needed.
4. `reframe.py`: Face detection with `cv2.FaceDetectorYN` (YuNet ONNX), sampled every N frames, tracked in-between, exponential moving average (EMA) center smoothing with max-pan-speed clamp, histogram difference scene cut detection with EMA reset, fallback to center crop. Computes face hit rate, average jitter, fallback frames count.
5. `render.py`: OpenCV `VideoCapture` frame reader, 9:16 crop, 1080x1920 scale, piped into FFmpeg subprocess encoding `libx264` (`yuv420p`) + `aac` audio with `+faststart`.
6. `storage.py`: S3 upload, generates 24-hour presigned URL.

## File Structure
```
ClipCup/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── clipcup/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py
│   │   │   ├── transcribe.py
│   │   │   ├── select_segment.py
│   │   │   ├── reframe.py
│   │   │   ├── render.py
│   │   │   └── storage.py
│   │   └── management/
│   │       └── commands/
│   │           └── run_clip.py
├── frontend/
├── scripts/
│   ├── download_models.sh
│   ├── download_models.ps1
│   └── evaluate.py
├── docs/
│   ├── architecture.md
│   ├── evaluation.md
│   └── REPORT.md
├── devpost/
│   ├── learner-profile.md
│   ├── scope.md
│   ├── prd.md
│   └── spec.md
├── .env.example
└── README.md
```
