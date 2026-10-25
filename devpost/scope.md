---
doc: scope
status: approved
---

# Clip Cup

AI-powered tool converting long-form videos into engaging 9:16 vertical shorts with smart face tracking and audio muxing.

## The Unique Kernel
Clip Cup combines speech transcript intelligence (AssemblyAI + AWS Bedrock) with computer-vision face tracking (OpenCV YuNet FaceDetectorYN with scene cut reset and EMA smoothing) to automatically produce one ready-to-publish vertical 9:16 short without persistent storage of the raw source video.

## Who It's For
Content creators, podcast producers, and video marketers who need to turn landscape videos into polished vertical reels/shorts quickly and reliably without expensive manual video editing.

## The Core Loop
1. User provides a video file upload or a direct video URL (.mp4, max 10 min).
2. Clip Cup ingests and extracts audio, transcribes with word timestamps, and uses AWS Bedrock to identify the most engaging <=90s segment.
3. OpenCV reframes to 9:16 tracking speaker faces with EMA smoothing and scene-cut detection.
4. FFmpeg encodes 1080x1920 H.264 video muxed with audio, uploads to S3, and delivers a 24-hour presigned URL.

## What "Working" Looks Like
A user inputs a video file or direct URL, the pipeline executes end-to-end (CLI and Web UI), and produces an S3-hosted, presigned vertical video clip with smooth face cropping and synced audio within minutes.

## The POC Boundary
- Single-pass conversion of one video (max 10 min) to one vertical short (max 90 seconds).
- Direct video URLs (.mp4 etc.) or file upload; no YouTube page scraping.
- In-memory/temp workspace per job cleaned up immediately.
- SQLite + background thread pool (no Celery/Redis required for POC).
- OpenCV YuNet ONNX for face detection, scene-cut histogram analysis, EMA pan smoothing.
- AWS S3 presigned URL for output delivery.

## Explicitly Cut
- YouTube/TikTok/Instagram page scraping (direct URLs only).
- Multi-clip generation per video (POC delivers the single best highlight clip).
- Heavy message broker infrastructure (Celery/Redis) replaced by managed Python thread worker pool.
