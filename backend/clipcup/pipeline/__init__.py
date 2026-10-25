"""
Clip Cup Processing Pipeline.

Orchestrates:
1. Ingestion & Validation (ingest.py)
2. Speech Transcription (transcribe.py)
3. Bedrock Segment Selection (select_segment.py)
4. OpenCV Smart Face-Tracking Reframing (reframe.py)
5. FFmpeg Streaming Render (render.py)
6. AWS S3 Storage & Presigning (storage.py)
"""

from .ingest import ingest_video, validate_source
from .transcribe import transcribe_audio
from .select_segment import select_segment
from .reframe import reframe_video
from .render import render_short
from .storage import upload_and_presign
from .orchestrator import run_pipeline, JobTimeoutError

__all__ = [
    "ingest_video",
    "validate_source",
    "transcribe_audio",
    "select_segment",
    "reframe_video",
    "render_short",
    "upload_and_presign",
    "run_pipeline",
    "JobTimeoutError",
]
