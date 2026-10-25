# Clip Cup 🎬☕

**Turn Long Landscape Videos into Engaging 9:16 Shorts — Automatically**

Clip Cup is an AI-powered computer vision pipeline built for the Devpost Learn *Build With AI: Basics* hackathon. It ingests long-form videos (uploaded files or direct URLs, max 10 minutes), discovers the most engaging highlight using LLM transcript analysis, reframes it to 9:16 vertical using OpenCV YuNet face detection with EMA smoothing, and delivers a finished 1080×1920 H.264 short via AWS S3 presigned URL. Job state is persisted in Supabase PostgreSQL.

---

## What It Does

1. **Upload or submit** a direct video URL (MP4, MOV, max 10 min)
2. **AssemblyAI** transcribes speech with word-level timestamps
3. **AWS Bedrock (Claude 3.5 Sonnet)** picks the best ≤90s highlight
4. **OpenCV YuNet** tracks faces and reframes to 9:16 with smooth EMA panning
5. **FFmpeg** encodes 1080×1920 H.264 with synced audio
6. **AWS S3** delivers a 24-hour presigned URL — no source video stored

---

## Key Features

- **Smart Face Tracking**: `cv2.FaceDetectorYN` (YuNet ONNX) detects faces every 5 frames, linear interpolation between detections
- **EMA Smoothing**: Exponential Moving Average (α = 0.15) + max-pan-speed clamp (≤18 px/frame) eliminates camera shake
- **Scene Cut Detection**: HSV histogram correlation detects camera cuts and immediately resets EMA for crisp transitions
- **Center-Crop Fallback**: Stable center crop when no face is detected (B-roll, graphics, landscape shots)
- **AI Highlight Selection**: Bedrock generates strict JSON boundaries snapped to utterance timestamps; falls back to highest speech-density 60s window on failure
- **No Persistent Source Storage**: Per-job temp workspace purged immediately in a `finally` block
- **JWT Auth**: Full account system — register, log in, view personal job history
- **Dual Interface**: React web app + Django CLI management command

---

## Pipeline Architecture

```
┌─────────────┐   ┌──────────────┐   ┌────────────────┐   ┌──────────────────┐   ┌───────────────┐
│ 1. Ingest   │ → │ 2. Transcribe│ → │ 3. Select      │ → │ 4. Reframe       │ → │ 5. Render     │
│ Source probe│   │ AssemblyAI   │   │ Segment        │   │ OpenCV YuNet     │   │ FFmpeg pipe   │
│ Max 10 min  │   │ Word times   │   │ AWS Bedrock    │   │ EMA + scene cut  │   │ 1080×1920 H.264│
│ Audio strip │   │ Utterances   │   │ ≤90s JSON      │   │ Max-pan clamp    │   │ Synced audio  │
└─────────────┘   └──────────────┘   └────────────────┘   └──────────────────┘   └───────┬───────┘
                                                                                           │
                                                                               6. AWS S3 Storage
                                                                               24h Presigned URL
                                                                               Temp workspace wiped
```

---

## Repository Structure

```
ClipCup/
├── backend/
│   ├── manage.py
│   ├── requirements.txt              # Pinned Python dependencies
│   ├── clipcup/
│   │   ├── settings.py              # Environment-driven Django config
│   │   ├── urls.py                  # API routing
│   │   ├── models.py                # Job model (states + reframing stats)
│   │   ├── views.py                 # DRF endpoints (/api/jobs, /api/health)
│   │   ├── auth_views.py            # Register, login, refresh, logout, me
│   │   ├── services.py              # ThreadPoolExecutor background worker
│   │   ├── tests.py                 # Unit & integration tests
│   │   └── pipeline/
│   │       ├── ingest.py            # Validation, download, audio extraction
│   │       ├── transcribe.py        # AssemblyAI transcription
│   │       ├── select_segment.py    # Bedrock highlight selection + fallback
│   │       ├── reframe.py           # OpenCV YuNet + EMA smoothing
│   │       ├── render.py            # OpenCV + FFmpeg pipe rendering
│   │       ├── storage.py           # S3 upload + presigned URL
│   │       └── orchestrator.py      # Lifecycle + timeout management
├── frontend/                        # React (Vite) + Tailwind CSS
│   ├── src/
│   │   ├── App.jsx                  # Main app + routing
│   │   ├── api.js                   # API base URL helper
│   │   ├── context/AuthContext.jsx  # JWT auth context + authFetch
│   │   └── components/
│   │       ├── LandingPage.jsx
│   │       ├── AuthPage.jsx
│   │       ├── Header.jsx
│   │       ├── InputTabs.jsx        # URL + file upload tabs
│   │       ├── ProgressBar.jsx      # Live stage polling
│   │       ├── ResultPlayer.jsx     # 9:16 video player
│   │       ├── StatsCard.jsx        # AI metrics + face tracking stats
│   │       └── HistoryPanel.jsx     # Personal job history
│   └── vercel.json
├── scripts/
│   ├── download_models.sh           # Bash model downloader
│   ├── download_models.ps1          # PowerShell model downloader
│   └── evaluate.py                  # 3-scenario benchmark suite
├── docs/
│   ├── architecture.md
│   └── evaluation.md
├── devpost/                         # Hackathon planning docs
│   ├── scope.md
│   ├── prd.md
│   ├── spec.md
│   ├── checklist.md
│   └── app-map.html
├── Dockerfile                       # Multi-stage production container
├── docker-compose.yml
├── render.yaml                      # Render deployment config
├── .env.example                     # Environment config template
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Python 3.12+
- FFmpeg (must be on PATH)
- Node.js 20+ & npm

### 1. Clone & Configure

```bash
git clone https://github.com/BatoolZyidi/ClipCup.git
cd ClipCup
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
SECRET_KEY=your-django-secret-key
DATABASE_URL=postgresql://user:pass@host:6543/postgres?sslmode=require
ASSEMBLYAI_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-southeast-2
S3_BUCKET_NAME=clipcup
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
```

> Leave `DATABASE_URL` blank to fall back to local SQLite for offline development.

### 2. Download Face Detection Model

```bash
# Linux / macOS
bash scripts/download_models.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File .\scripts\download_models.ps1
```

### 3. Backend Setup

```bash
python -m venv backend/.venv

# Activate — Windows:
.\backend\.venv\Scripts\Activate.ps1
# Activate — Linux/macOS:
source backend/.venv/bin/activate

pip install -r backend/requirements.txt
python backend/manage.py migrate
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

---

## Running the Application

### Web App (Backend + Frontend)

```bash
# Terminal 1 — Django API
python backend/manage.py runserver 8000

# Terminal 2 — React dev server
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### CLI — Process a Single Video

```bash
python backend/manage.py run_clip <path_or_url> --output output_short.mp4
```

### Docker (Local)

```bash
docker compose up -d --build backend
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health` | None | Health check |
| `POST` | `/api/auth/register` | None | Create account |
| `POST` | `/api/auth/login` | None | Login → JWT tokens |
| `POST` | `/api/auth/refresh` | None | Refresh access token |
| `POST` | `/api/auth/logout` | JWT | Invalidate refresh token |
| `GET` | `/api/auth/me` | JWT | Current user profile |
| `POST` | `/api/jobs` | JWT | Submit video (URL or file upload) |
| `GET` | `/api/jobs/<id>` | JWT | Poll job status + result |
| `GET` | `/api/jobs/history` | JWT | List all personal jobs |

### Job Status Flow

```
PENDING → TRANSCRIBING → SELECTING → REFRAMING → RENDERING → DONE
                                                            ↘ FAILED
```

---

## OpenCV Computer Vision Details

### YuNet Face Detection
- `cv2.FaceDetectorYN` with the YuNet ONNX model — lightweight, high-performance deep learning detector
- Samples every N=5 frames; interpolates between detections
- Multi-face: ranks by bounding box area × confidence to follow the primary speaker

### EMA Smoothing & Pan Clamping
$$\hat{x}_t = \alpha \cdot x_t + (1 - \alpha) \cdot \hat{x}_{t-1}, \quad \alpha = 0.15$$

Displacement per frame clamped to ≤18 px/frame to prevent dizzying snaps.

### Scene Cut Detection
HSV histogram correlation between consecutive frames:

$$\text{Correlation} = \text{compareHist}(H_{t-1}, H_t, \text{HISTCMP\_CORREL})$$

When correlation < 0.55, a scene cut is detected and the EMA center immediately resets.

---

## Failure Modes & Fallbacks

| Scenario | Reaction |
|----------|----------|
| YouTube page URL submitted | HTTP 400 — direct video URL required |
| Video > 10 minutes | Rejected before processing |
| No Bedrock API key | Falls back to highest speech-density 60s window |
| No AssemblyAI key | Falls back to synthetic transcript (local dev) |
| No faces detected | Stable center crop — 0% face hit rate reported |
| No S3 configured | Writes to local `media/shorts/` |
| Job > 15 min | `JobTimeoutError` — job marked FAILED cleanly |

---

## Running Tests & Benchmarks

```bash
# Unit & integration tests
python backend/manage.py test clipcup

# 3-scenario computer vision benchmark
python scripts/evaluate.py
```

Results saved to `docs/evaluation.md`.

---

## Ethical Use & Responsible AI

- **No facial recognition**: YuNet is used for geometric crop centering only — no embeddings, no identification, no biometric storage
- **No persistent source storage**: Source video purged immediately after rendering
- **User consent**: Designed for creators processing their own content

---

## Test Credentials

A demo account is available for reviewers:

| Field | Value |
|-------|-------|
| **Username** | `test_user` |
| **Password** | `testuser@123` |

> Sign up to create your own account.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 5, Django REST Framework |
| Auth | djangorestframework-simplejwt (JWT) |
| Database | Supabase PostgreSQL (SQLite fallback for local dev) |
| Speech-to-Text | AssemblyAI SDK |
| LLM | AWS Bedrock (Claude 3.5 Sonnet) |
| Computer Vision | OpenCV 4 (`cv2.FaceDetectorYN`, YuNet ONNX) |
| Video Encoding | FFmpeg (subprocess pipe) |
| Storage | AWS S3 + presigned URLs |
| Frontend | React, Vite, Tailwind CSS |
| Job Workers | Python `ThreadPoolExecutor` (no Celery/Redis needed) |
| Container | Docker + Docker Compose |

---


