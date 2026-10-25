---
doc: prd
status: approved
---

# Clip Cup — Product Requirements

Automated AI service that converts long-form video (upload or direct URL, max 10 min) into one vertical 9:16 short (max 90s, 1080x1920 H.264 with audio) stored in S3 with a presigned URL.

## The Core Journey
1. **Input Submission**: User uploads a video file (MP4, MOV, etc.) or submits a direct video URL (e.g. `https://domain.com/video.mp4`, max 10 minutes).
2. **Ingestion & Validation**: System validates duration and format, downloads/saves to a per-job temporary directory, and extracts audio.
3. **Transcription**: AssemblyAI generates full transcript with word-level timestamps and speaker utterances.
4. **Segment Selection**: AWS Bedrock analyzes transcript and selects the single best highlight (strict JSON `start_ms`, `end_ms`, `topic`, `reason`), bounded to <=90s, snapped to utterance boundaries.
5. **Computer Vision Reframing**: OpenCV YuNet detects face coordinates every N frames, tracks between frames, applies EMA smoothing with max-pan-speed limit, resets on scene cuts, and falls back to center crop when no face is found.
6. **Rendering**: OpenCV and FFmpeg stream and crop 9:16 frames, upscale/scale to 1080x1920, encode H.264 video muxed with segment audio.
7. **Storage & Delivery**: Output is pushed to AWS S3, a 24-hour presigned URL is generated, temporary files are destroyed, and job status is updated to DONE with metrics.

## Features and Behavior
- **Job Status Tracking**: States `PENDING`, `TRANSCRIBING`, `SELECTING`, `REFRAMING`, `RENDERING`, `DONE`, `FAILED`.
- **Reframing Metrics**: Tracks `face_hit_rate`, `avg_jitter_px`, and `fallback_frames`.
- **Temporary Lifecycle**: "No persistent source storage" — per-job temp folders are strictly wiped in a `finally` block.
- **REST API & CLI**: Both programmatic API (`/api/jobs`, `/api/jobs/<id>`, `/api/health`) and management command CLI (`python manage.py run_clip <file_or_url>`).

## Non-Goals
- No YouTube page URL scraping or web scraping.
- No user authentication / multi-tenant billing in POC (optional API key only).
- No Celery/Redis dependencies.
