---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- ✅ **1. Video Ingestion, FFmpeg Probe & Audio Extraction**
  Becomes usable: System accepts a direct video file or YouTube URL, verifies duration (<= 10 min), writes to a temporary workspace, and extracts clean 16kHz mono audio.
  Why now: Ingestion is the entry gate for all downstream audio and video intelligence.
  PRD ref: `prd.md > The Core Journey` (steps 1-2)
  Spec ref: `spec.md > Pipeline Components (ingest.py)`
  Build: Complete `ingest.py` supporting video file uploads, YouTube retrieval via `yt-dlp`, FFmpeg audio extraction, and video parameter probing.
  Verify (mechanical): Run probe and audio extraction on a sample video to ensure valid `audio.wav` and metadata output.
  Learner check: Submit a sample video URL/file and verify the ingestion stage succeeds.
  Commit: `Add video ingestion, yt-dlp handling, and FFmpeg audio extraction`

- ✅ **2. AssemblyAI Speech-to-Text Transcription**
  Becomes usable: Speech is transcribed with word-level timestamps and structured speaker utterances.
  Why now: Word timestamps provide the exact boundary timestamps needed for highlight selection.
  PRD ref: `prd.md > The Core Journey` (step 3)
  Spec ref: `spec.md > Pipeline Components (transcribe.py)`
  Build: Implement `transcribe.py` using `assemblyai` SDK with fallback mocking for offline development.
  Verify (mechanical): Run transcription against an audio sample and assert `utterances` and `words` are present with valid timestamps.
  Learner check: Verify the transcription step runs and outputs structured dialogue.
  Commit: `Implement AssemblyAI transcription with word-level timestamps`

- ✅ **3. Contextual Dialogue & Climax Highlight Selection**
  Becomes usable: System analyzes the full dialogue context to pinpoint the most engaging highlight (under 120s) with natural sentence boundaries.
  Why now: Must know start and end timestamps before initiating video reframing.
  PRD ref: `prd.md > The Core Journey` (step 4)
  Spec ref: `spec.md > Pipeline Components (select_segment.py)`
  Build: Implement `select_segment.py` with AWS Bedrock LLM and contextual dialogue/cadence ranking algorithm that scans the entire timeline.
  Verify (mechanical): Test segment selection on a transcript and assert start_ms < end_ms and duration <= 120s snapped to utterance boundaries.
  Learner check: Verify that the highlight selected captures a meaningful peak moment rather than just the beginning.
  Commit: `Implement contextual highlight selection with 120s limit`

- ✅ **4. OpenCV 5 Face & Visual Motion Tracking Reframing**
  Becomes usable: OpenCV tracks human faces and visual motion across the segment, applying bidirectional Gaussian smoothing to eliminate camera shake.
  Why now: Delivers the core computer vision differentiator for horizontal-to-vertical conversion.
  PRD ref: `prd.md > The Core Journey` (step 5)
  Spec ref: `spec.md > Pipeline Components (reframe.py)`
  Build: Implement `reframe.py` using YuNet ONNX neural detector, scene cut detection, visual motion fallback, and Gaussian smoothing.
  Verify (mechanical): Execute reframing on sample frames and verify `crop_boxes` and stability stats (`avg_jitter_px < 3.0`).
  Learner check: Verify that face tracking follows the subject smoothly without jitter or abrupt shaking.
  Commit: `Implement OpenCV 5 face tracking with bidirectional Gaussian stabilization`

- ✅ **5. FFmpeg Streaming Render, S3 Storage & REST API**
  Becomes usable: End-to-end processing pipeline produces an encoded vertical video, uploads to cloud storage, and serves the result via REST API.
  Why now: Connects all pipeline steps into a finished, deliverable product with strict temp file cleanup.
  PRD ref: `prd.md > The Core Journey` (steps 6-7)
  Spec ref: `spec.md > Pipeline Components (render.py, storage.py), spec.md > File Structure`
  Build: Implement `render.py`, `storage.py`, background worker orchestration, and Django REST API endpoints with auth.
  Verify (mechanical): Execute end-to-end job via REST API test and assert `DONE` status with presigned URL.
  Learner check: Create an account, submit a video, watch progress stages update in real time, and download the finished vertical short.
  Commit: `Complete end-to-end pipeline rendering, storage, and REST API`

## Hands-on Checkpoints

- ✅ Early usable behavior explored — Ingestion, transcription, and highlight selection verified
- ✅ Final kick-the-tires exploration and feedback completed — end-to-end pipeline tested with real video, S3 output confirmed, history playback and result screen verified

## Final Review

- ✅ Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- ✅ Learning activity complete — learner navigated all 6 pipeline stages (ingest → transcribe → select_segment → reframe → render → storage), React frontend components, and Django REST API during active build sessions
- ✅ Optional edit and transfer reflection addressed — covered during build
- ✅ `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: Active pair-programming sessions across all pipeline files
Route and stops: ingest.py → transcribe.py → select_segment.py → reframe.py → render.py → storage.py → views.py → App.jsx → ResultPlayer.jsx → StatsCard.jsx
Edit outcome: Learner directed all decisions; real credentials and Supabase migration completed
Reflection: Learner confirmed app is ready to ship
Activity mode: fast

## Revisions
