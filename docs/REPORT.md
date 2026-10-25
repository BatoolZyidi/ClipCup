# Clip Cup — Technical Report

**Project**: Clip Cup — Automated 9:16 Vertical Video Reframing  
**Author**: Hackathon Engineering Team  
**Date**: October 2026  
**License**: MIT  

---

## 1. Problem Statement

Long-form landscape videos (such as podcasts, interviews, keynote speeches, and tutorials) contain valuable content, but short-form vertical platforms (TikTok, Instagram Reels, YouTube Shorts) command the majority of digital content consumption. 

Repurposing landscape video into vertical 9:16 shorts is traditionally labor-intensive:
1. **Manual Highlight Discovery**: An editor must review the entire video to spot a 30–90 second self-contained moment.
2. **Keyframe Pan-and-Scan**: In horizontal 16:9 framing, subjects frequently shift positions or multiple speakers take turns. Center-cropping cuts off speakers, while manually keyframing horizontal motion is tedious.
3. **Storage & Infrastructure Overhead**: Storing raw video files incurs high storage and egress costs.

**Clip Cup solves this** by executing an automated, zero-persistent-source-storage pipeline that discovers viral moments via LLM transcripts, tracks speakers dynamically using OpenCV YuNet face detection with EMA smoothing and scene cut detection, and streams rendered 1080x1920 H.264 video directly to AWS S3.

---

## 2. System Architecture

Clip Cup is structured into three clean layers:
- **Presentation Layer**: A modern React (Vite) + Tailwind CSS web interface supporting direct video URL input and drag-and-drop file upload, with live 3-second stage polling and an interactive 9:16 video player.
- **Service Tier**: Django 5 + Django REST Framework with an internal `ThreadPoolExecutor` background worker (eliminating external Celery/Redis infrastructure for lean deployments).
- **Processing Core (`backend/clipcup/pipeline/`)**: A modular 6-stage pipeline executing inside an isolated per-job temporary workspace.

```
+---------------------------------------------------------------------------------------------------------+
|                                        CLIP CUP PIPELINE                                                |
+-------------------+--------------------+--------------------+--------------------+----------------------+
|  1. Ingest        |  2. Transcribe     |  3. Select Segment |  4. Smart Reframe  |  5. Render & Mux     |
|  - Source probe   |  - AssemblyAI SDK  |  - AWS Bedrock     |  - OpenCV YuNet    |  - Pipe to FFmpeg    |
|  - Max 10 min     |  - Word timestamps |  - <=90s JSON      |  - EMA center pan  |  - 1080x1920 H.264   |
|  - Extract audio  |  - Utterances      |  - Utterance snap  |  - Scene cut reset |  - Synced AAC audio  |
+-------------------+--------------------+--------------------+--------------------+----------------------+
                                                                                       |
                                                                             6. AWS S3 Storage
                                                                             - 24h Presigned URL
                                                                             - Wipe temp workspace
```

---

## 3. OpenCV Computer Vision Implementation

The reframing engine (`backend/clipcup/pipeline/reframe.py`) addresses key challenges in automated video cropping:

### A. YuNet Face Detection (`cv2.FaceDetectorYN`)
- Uses the YuNet ONNX model (`face_detection_yunet_2023mar.onnx`), a lightweight, high-performance deep learning face detector integrated natively into OpenCV.
- Evaluates video frames sampled every $N=5$ frames to balance CPU utilization and tracking fidelity.
- When multiple faces are present in a scene, ranks detections by bounding box area and confidence score to prioritize the primary speaker.

### B. Exponential Moving Average (EMA) & Max-Pan Clamping
- Pure bounding box centering produces jarring camera shaking ("micro-jitter").
- Clip Cup applies Exponential Moving Average smoothing to the horizontal crop center:
  $$\hat{x}_t = \alpha \cdot x_t + (1 - \alpha) \cdot \hat{x}_{t-1}$$
  where $\alpha = 0.15$.
- To prevent dizzying pans when a speaker gestures widely, displacement per frame is clamped to a maximum velocity ($\le 18\text{ px/frame}$).

### C. Scene Cut Detection & Smoothing Reset
- When a video switches camera angles, continuous smoothing would cause the camera to "drag" slowly from the old speaker's position to the new one.
- Clip Cup computes a 2D HSV color histogram for consecutive frames:
  $$\text{Correlation} = \text{compareHist}(H_{t-1}, H_t, \text{HISTCMP\_CORREL})$$
- When correlation drops below the threshold ($0.55$), a scene transition is declared. The EMA filter immediately resets to the new subject's center, creating a crisp, natural cut.

### D. Center-Crop Fallback
- When no face is detected (e.g. landscape shots, graphics, product b-roll), the crop box gracefully defaults to the horizontal center of the frame ($W / 2$).

---

## 4. AWS Services Integration

1. **Amazon Bedrock (`bedrock-runtime`)**:
   - Analyzes timestamped transcripts using Claude 3.5 Sonnet / Titan Text models.
   - Constrained to strict JSON output: `{"start_ms", "end_ms", "topic", "reason"}` bounded to $\le 90$ seconds.
   - Snapped to nearest utterance timestamps to avoid cutting speakers off mid-word.
   - Retries once on invalid JSON with an error-correcting prompt; falls back to the highest speech-density 60s sliding window on API failure.

2. **Amazon Simple Storage Service (S3)**:
   - Stores the generated 1080x1920 MP4 files under `shorts/<job_id>.mp4`.
   - Generates secure 24-hour presigned GET URLs with `Content-Disposition: inline` for immediate in-browser playback and direct download.

3. **AWS IAM Integration**:
   - Production EC2 instances utilize IAM Instance Profiles (`ClipCupEC2Role`), allowing Boto3 to authenticate via IMDSv2 without storing credentials on disk.

---

## 5. Evaluation & Performance

Benchmarks were conducted using `scripts/evaluate.py` across three synthetic and real-world test patterns:
1. **Dynamic Moving Face**: Verifies face tracking and EMA smoothing during horizontal subject motion.
2. **Scene Cut Transitions**: Verifies camera cut resets and multi-shot stabilization.
3. **Static Fallback**: Verifies center-crop stability without face false-positives.

*Detailed numerical metrics are recorded in `docs/evaluation.md`.*

---

## 6. Failure Modes & Graceful Fallbacks

| Failure Scenario | System Reaction | User Experience |
|------------------|-----------------|-----------------|
| **YouTube Webpage URL submitted** | Ingestion regex validation rejects non-direct URL with HTTP 400. | Descriptive error message advising direct video link. |
| **Video duration > 10 minutes** | Video probe checks duration and rejects before heavy processing. | Clear notice of 10-minute limit. |
| **No Bedrock API Key / Quota Exceeded** | `select_segment.py` falls back to 60s highest speech-density window. | Job finishes successfully with "Key Highlight" topic. |
| **No AssemblyAI API Key** | `transcribe.py` falls back to synthetic transcript for local testing. | Pipeline executes end-to-end without crashing. |
| **No faces in video** | `reframe.py` applies stable center crop for 9:16 ratio. | Video rendered with 0% face hit rate and 100% center crop fallback. |
| **Unconfigured S3 Bucket** | `storage.py` writes to local `media/shorts/` and returns local URI. | Video plays locally in development. |
| **Timeout (> 15 minutes)** | `orchestrator.py` raises `JobTimeoutError`, marks job as FAILED. | Job state terminates cleanly without hanging workers. |

---

## 7. Known Limitations

- **Direct URLs Only**: Does not scrape YouTube, TikTok, or Instagram landing pages. Source video must be a raw accessible video file (.mp4, .mov, etc.) or file upload.
- **Single Short per Job**: In this proof-of-concept version, one short is generated per input video.
- **CPU Bound Rendering**: Video encoding runs on CPU via FFmpeg. GPU acceleration (NVENC) can be enabled in production on GPU-enabled EC2 instances (`g4dn.xlarge`).

---

## 8. Responsible AI & Ethical Use

- **Consent for Source Videos**: Clip Cup is designed for content creators and editors to repurpose their own footage. Users are instructed to only process content they hold distribution rights to.
- **No Facial Identification or Biometrics**: Clip Cup utilizes face **detection** solely for geometric bounding box calculation (finding $(x, y, w, h)$ coordinates to center the 9:16 crop window). It does **not** perform facial recognition, does not extract facial embeddings, does not store biometric signatures, and does not identify individuals.
- **No Persistent Source Storage**: Source videos and audio extractions are stored strictly inside a transient per-job directory that is purged immediately in a `finally` block upon completion or failure.
