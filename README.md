# Clip Cup 🎬☕

**Turn Long Landscape Videos into Engaging 9:16 Shorts**

Clip Cup is an automated computer-vision and AI pipeline built for the Devpost Learn *Build With AI: Basics* hackathon. It ingests long-form videos (uploaded files or direct URLs, max 10 minutes), discovers viral highlights, reframes the video to 9:16 vertical using OpenCV YuNet face detection with Exponential Moving Average (EMA) smoothing and scene cut detection, and streams the finished 1080x1920 H.264 short with synchronized audio into AWS S3 with a 24-hour presigned URL. Job state is persisted in Supabase PostgreSQL.

---

## Key Features

- **No Persistent Source Storage**: Source videos are kept only inside an isolated per-job temporary workspace and purged in a `finally` block immediately after rendering.
- **Smart OpenCV 5 YuNet Reframing**:
  - `cv2.FaceDetectorYN` (YuNet ONNX model) detects speaker faces every $N=5$ frames.
  - Linear motion interpolation between detections.
  - Exponential Moving Average (EMA) smoothing prevents camera shake.
  - Max-pan-speed clamp ($\le 18\text{ px/frame}$) avoids dizzying camera snaps.
  - HSV histogram correlation detects camera scene cuts, immediately resetting smoothing centers.
  - Stable center-crop fallback when no faces are detected.
- **AI Highlight Selection**:
  - AssemblyAI speech-to-text with word-level timestamps and speaker utterances.
  - AWS Bedrock (Claude 3.5 Sonnet / Amazon Titan) generates strict JSON segment boundaries ($\le 90$s) snapped to utterance boundaries.
  - Automatic fallback to highest speech-density 60s window on API or JSON failure.
- **High-Quality Streaming Render**:
  - Streams frames via OpenCV `VideoCapture` directly into an FFmpeg subprocess stdin pipe.
  - Encodes 1080x1920 H.264 (`yuv420p`, `-movflags +faststart`) muxed with the segment's original AAC audio.
- **Dual Interface**:
  - Full-featured **React (Vite) + Tailwind CSS** web application with drag-and-drop file upload, live 3-second stage polling, and a 9:16 video player.
  - Standalone **Django CLI management command** (`python manage.py run_clip`).

---

## Repository Structure

```
ClipCup/
├── backend/
│   ├── manage.py
│   ├── requirements.txt         # Pinned Python dependencies
│   ├── clipcup/
│   │   ├── settings.py          # Environment-driven Django configuration
│   │   ├── urls.py              # API routing & local media serving
│   │   ├── models.py            # Job model tracking states & reframing stats
│   │   ├── views.py             # DRF endpoints (/api/jobs, /api/health)
│   │   ├── services.py          # Background ThreadPoolExecutor worker
│   │   ├── tests.py             # Unit & integration test suite
│   │   ├── pipeline/            # Core processing engine
│   │   │   ├── ingest.py        # Ingestion, validation & audio extraction
│   │   │   ├── transcribe.py    # AssemblyAI transcription
│   │   │   ├── select_segment.py# Bedrock highlight selection & fallback
│   │   │   ├── reframe.py       # OpenCV YuNet face detection & EMA smoothing
│   │   │   ├── render.py        # OpenCV + FFmpeg pipe rendering
│   │   │   ├── storage.py       # S3 upload & presigned URL generation
│   │   │   └── orchestrator.py  # Lifecycle & timeout management
│   │   └── management/
│   │       └── commands/
│   │           └── run_clip.py  # CLI management command
│   └── models/                  # Downloaded ONNX face detection weights
├── frontend/                    # React (Vite) + Tailwind web application
├── scripts/
│   ├── download_models.sh       # Bash model downloader
│   ├── download_models.ps1      # PowerShell model downloader
│   └── evaluate.py              # Automated 3-scenario benchmark suite
├── deploy/
│   └── README.md                # AWS EC2 deployment & IAM configuration guide
├── docs/
│   ├── architecture.md          # Architecture overview with Mermaid diagram
│   ├── evaluation.md            # Benchmark performance & quality results
│   └── REPORT.md                # Full technical report
├── devpost/                     # Devpost Learn Skill Pack specifications
├── Dockerfile                   # Multi-stage production container
├── docker-compose.yml           # Local multi-service orchestration
├── .env.example                 # Environment configuration template
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Python 3.12+
- FFmpeg (must be available on PATH)
- Node.js 20+ & npm

### 1. Clone & Configure Environment
```bash
git clone https://github.com/your-username/ClipCup.git
cd ClipCup

# Copy environment template
cp .env.example .env
```

Edit `.env` with your API credentials (optional for offline testing with built-in fallbacks):
```ini
ASSEMBLYAI_API_KEY=your_key_here
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_s3_bucket_name
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
```

### 2. Download Face Detection Model
```bash
# On Linux / macOS:
bash scripts/download_models.sh

# On Windows (PowerShell):
powershell -ExecutionPolicy Bypass -File .\scripts\download_models.ps1
```

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv backend/.venv

# Activate virtual environment
# Windows:
.\backend\.venv\Scripts\Activate.ps1
# Linux / macOS:
source backend/.venv/bin/activate

# Install pinned dependencies
pip install -r backend/requirements.txt

# Run migrations
python backend/manage.py migrate
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## Running the Application

### Option A: Web Application (Backend + Frontend)

1. Start the Django API Server:
```bash
python backend/manage.py runserver 8000
```

2. Start the React Frontend Dev Server:
```bash
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### Option B: Standalone CLI

Run the full pipeline directly on any local video file or direct URL:
```bash
python backend/manage.py run_clip <path_or_url> --output <destination.mp4>
```

Example with test video:
```bash
python backend/manage.py run_clip tests/sample_video.mp4 --output tests/output_short.mp4
```

---

## Running Tests & Benchmarks

### Unit & Integration Test Suite
```bash
python backend/manage.py test clipcup
```

### Automated Benchmark Evaluation
Run the 3-scenario computer vision benchmark suite:
```bash
python scripts/evaluate.py
```
Results are saved to `docs/evaluation.md`.

---

## Docker & Production Deployment

Run locally with Docker Compose:
```bash
docker compose up -d --build backend
```

For full AWS EC2 production deployment, IAM role policies, security groups, and Nginx SSL configuration, see [deploy/README.md](deploy/README.md).

---

## Deploying to Render (Backend) + Vercel (Frontend)

### Backend → Render

1. Go to [render.com](https://render.com) → **New Web Service** → connect your GitHub repo
2. Render will detect `render.yaml` automatically
3. In the Render dashboard **Environment** tab, add your secret values:
   - `DATABASE_URL` — your Supabase connection string
   - `ASSEMBLYAI_API_KEY`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
4. Deploy — your backend URL will be something like `https://clipcup-backend.onrender.com`

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project** → connect your GitHub repo
2. Set **Root Directory** to `frontend`
3. Add one Environment Variable:
   - `VITE_API_BASE_URL` = `https://clipcup-backend.onrender.com` *(your Render URL)*
4. Deploy — Vercel handles the Vite build automatically via `frontend/vercel.json`

---

## Test Credentials

A demo account is available for reviewers to try the app without signing up:

| Field | Value |
|---|---|
| **Username** | `test_user` |
| **Password** | `testuser@123` |

> These credentials are for demonstration only. Sign up to create your own account.

