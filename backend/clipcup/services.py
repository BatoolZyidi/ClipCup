"""
Clip Cup Background Worker Service.
Manages asynchronous job execution using a managed ThreadPoolExecutor (no Celery/Redis).
Updates Job database model as each pipeline stage progresses.
"""

import logging
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from django.db import close_old_connections

from .models import Job, JobStatus
from .pipeline import run_pipeline

logger = logging.getLogger("clipcup.services")

# Thread pool executor for background jobs
_EXECUTOR = ThreadPoolExecutor(max_workers=int(os.getenv("MAX_CONCURRENT_JOBS", "4")))


def _execute_job_in_background(job_id: str, source_path_or_url: str, is_temp_upload: bool):
    """
    Worker task executed inside the ThreadPoolExecutor.
    Closes stale database connections, runs the pipeline, updates Job model.
    """
    close_old_connections()
    extra = {"job_id": job_id}
    logger.info(f"Background worker picked up job {job_id}", extra=extra)

    def progress_callback(step: str, data: dict):
        close_old_connections()
        try:
            job = Job.objects.get(id=job_id)
            # Map pipeline step to JobStatus
            if hasattr(JobStatus, step):
                job.status = getattr(JobStatus, step)
            job.step = step.lower()
            if "topic" in data:
                job.topic = data["topic"]
            if "reason" in data:
                job.reason = data["reason"]
            if "stats" in data:
                job.stats = data["stats"]
            if "result_url" in data:
                job.result_url = data["result_url"]
            job.save(update_fields=["status", "step", "topic", "reason", "stats", "result_url", "updated_at"])
        except Exception as e:
            logger.warning(f"Failed to update job status for {job_id} at step {step}: {e}", extra=extra)

    try:
        result = run_pipeline(
            source=source_path_or_url,
            job_id=job_id,
            progress_callback=progress_callback,
        )

        close_old_connections()
        job = Job.objects.get(id=job_id)
        job.status = JobStatus.DONE
        job.step = "done"
        job.topic = result["topic"]
        job.reason = result["reason"]
        job.stats = result["stats"]
        job.result_url = result["result_url"]
        job.save()

        logger.info(f"Background execution of {job_id} finished successfully.", extra=extra)

    except Exception as exc:
        logger.error(f"Background execution of {job_id} failed: {exc}", exc_info=True, extra=extra)
        close_old_connections()
        try:
            job = Job.objects.get(id=job_id)
            job.status = JobStatus.FAILED
            job.step = "failed"
            job.error = str(exc)
            job.save(update_fields=["status", "step", "error", "updated_at"])
        except Exception as db_err:
            logger.error(f"Failed to record failure state for {job_id}: {db_err}", extra=extra)

    finally:
        # If the input was an uploaded file in a temp directory, clean up the upload copy
        if is_temp_upload:
            try:
                upload_file = Path(source_path_or_url)
                if upload_file.exists():
                    upload_file.unlink(missing_ok=True)
                    if upload_file.parent.name.startswith("clipcup_upload_"):
                        shutil.rmtree(upload_file.parent, ignore_errors=True)
            except Exception as cleanup_err:
                logger.warning(f"Error cleaning uploaded file: {cleanup_err}", extra=extra)
        close_old_connections()


def submit_job(source: str, source_type: str = "URL", is_temp_upload: bool = False, user=None) -> Job:
    """
    Creates a Job in PENDING status and enqueues it to the background thread pool.
    user: optional Django User instance — links the job to the authenticated user's history.
    """
    job = Job.objects.create(
        status=JobStatus.PENDING,
        step="pending",
        source_type=source_type,
        source_input=source if source_type == "URL" else Path(source).name,
        user=user,
    )

    logger.info(f"Submitting job {job.id} ({source_type}) to background thread pool.")
    _EXECUTOR.submit(_execute_job_in_background, job.id, source, is_temp_upload)
    return job

