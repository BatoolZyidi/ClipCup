"""
Clip Cup Pipeline Orchestrator.
Coordinates the end-to-end 6-stage video processing flow with:
- Strict per-job temporary workspace lifecycle (deleted in a finally block)
- Structured logging per job
- Configurable timeout enforcement (default 15 minutes)
- Clean exception propagation and status updates
"""

import logging
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from .ingest import ingest_video
from .transcribe import transcribe_audio
from .select_segment import select_segment
from .reframe import reframe_video
from .render import render_short
from .storage import upload_and_presign

logger = logging.getLogger("clipcup.pipeline.orchestrator")

DEFAULT_TIMEOUT_SECONDS = int(os.getenv("JOB_TIMEOUT_SECONDS", "900"))  # 15 min


class JobTimeoutError(Exception):
    """Raised when job processing exceeds designated timeout."""
    pass


def run_pipeline(
    source: str,
    job_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    keep_temp: bool = False,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the end-to-end pipeline:
    1. INGESTING: validate URL or local file, extract audio.
    2. TRANSCRIBING: AssemblyAI speech-to-text with timestamps.
    3. SELECTING: Bedrock LLM highlight selection (<=90s).
    4. REFRAMING: OpenCV YuNet face detection & EMA smoothing.
    5. RENDERING: VideoCapture + FFmpeg muxing to 1080x1920 H.264.
    6. STORING: Upload to S3 & generate presigned URL.

    The per-job temp directory is guaranteed to be deleted in a finally block.
    """
    job_id = job_id or f"job_{uuid.uuid4().hex[:12]}"
    extra = {"job_id": job_id}
    start_time = time.time()

    def _check_timeout():
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            raise JobTimeoutError(
                f"Job {job_id} exceeded maximum timeout of {timeout_seconds}s (elapsed: {elapsed:.1f}s)."
            )

    def _notify(step: str, data: Dict[str, Any] = None):
        _check_timeout()
        if progress_callback:
            try:
                progress_callback(step, data or {})
            except Exception as e:
                logger.warning(f"Progress callback error: {e}", extra=extra)

    # Create isolated per-job temporary workspace
    temp_dir_base = Path(tempfile.gettempdir()) / "clipcup"
    temp_dir_base.mkdir(parents=True, exist_ok=True)
    job_temp_dir = Path(tempfile.mkdtemp(prefix=f"clipcup_{job_id}_", dir=temp_dir_base))

    logger.info(
        f"Initialized job {job_id}. Temporary workspace: {job_temp_dir}",
        extra=extra,
    )

    try:
        # STEP 1: INGESTION
        logger.info("Stage 1/6: Ingesting source video...", extra=extra)
        _notify("INGESTING", {"step": "ingesting", "job_id": job_id})
        _check_timeout()
        ingest_result = ingest_video(source, job_temp_dir, job_id=job_id)

        video_path = ingest_result["video_path"]
        audio_path = ingest_result["audio_path"]
        duration_s = ingest_result["duration"]
        video_duration_ms = int(duration_s * 1000)

        # STEP 2: TRANSCRIPTION
        logger.info("Stage 2/6: Transcribing speech with AssemblyAI...", extra=extra)
        _notify("TRANSCRIBING", {"step": "transcribing", "duration_s": duration_s})
        _check_timeout()
        transcript_data = transcribe_audio(audio_path, job_id=job_id)

        # STEP 3: SEGMENT SELECTION
        logger.info("Stage 3/6: Selecting highlight segment with Bedrock...", extra=extra)
        _notify("SELECTING", {"step": "selecting", "utterance_count": len(transcript_data.get("utterances", []))})
        _check_timeout()
        segment = select_segment(transcript_data, video_duration_ms, job_id=job_id)

        # STEP 4: REFRAMING
        logger.info("Stage 4/6: Smart face tracking & reframing with OpenCV YuNet...", extra=extra)
        _notify("REFRAMING", {"step": "reframing", "segment": segment})
        _check_timeout()
        reframe_result = reframe_video(
            video_path=video_path,
            start_ms=segment["start_ms"],
            end_ms=segment["end_ms"],
            job_id=job_id,
        )

        # STEP 5: RENDERING
        logger.info("Stage 5/6: Rendering 1080x1920 vertical video via FFmpeg...", extra=extra)
        _notify("RENDERING", {"step": "rendering", "stats": reframe_result["stats"]})
        _check_timeout()

        if output_path:
            render_dest = Path(output_path).resolve()
        else:
            render_dest = job_temp_dir / f"{job_id}_short.mp4"

        rendered_file = render_short(
            source_video=video_path,
            segment=segment,
            crop_boxes=reframe_result["crop_boxes"],
            fps=reframe_result["fps"],
            output_path=render_dest,
            job_id=job_id,
        )

        # STEP 6: STORAGE & PRESIGNING
        logger.info("Stage 6/6: Storing short and generating presigned URL...", extra=extra)
        _notify("STORING", {"step": "storing", "file_size": rendered_file.stat().st_size})
        _check_timeout()
        result_url = upload_and_presign(rendered_file, job_id=job_id)

        total_elapsed = time.time() - start_time
        logger.info(
            f"Job {job_id} completed successfully in {total_elapsed:.1f}s. Result URL: {result_url}",
            extra=extra,
        )

        _notify("DONE", {
            "step": "done",
            "result_url": result_url,
            "topic": segment["topic"],
            "stats": reframe_result["stats"],
            "duration_s": (segment["end_ms"] - segment["start_ms"]) / 1000.0,
        })

        return {
            "job_id": job_id,
            "status": "DONE",
            "topic": segment["topic"],
            "reason": segment["reason"],
            "start_ms": segment["start_ms"],
            "end_ms": segment["end_ms"],
            "segment_duration_s": (segment["end_ms"] - segment["start_ms"]) / 1000.0,
            "stats": reframe_result["stats"],
            "result_url": result_url,
            "rendered_file": str(rendered_file),
            "processing_time_s": round(total_elapsed, 2),
        }

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True, extra=extra)
        _notify("FAILED", {"step": "failed", "error": str(e)})
        raise
    finally:
        # Strict enforcement: "Source video is never kept after a job: use a per-job temp directory and delete it in a finally block."
        if not keep_temp:
            try:
                if job_temp_dir.exists():
                    shutil.rmtree(job_temp_dir, ignore_errors=True)
                    logger.info(
                        f"Cleaned up temporary workspace: {job_temp_dir} (no persistent source storage).",
                        extra=extra,
                    )
            except Exception as cleanup_err:
                logger.warning(
                    f"Error cleaning up temp directory {job_temp_dir}: {cleanup_err}",
                    extra=extra,
                )
