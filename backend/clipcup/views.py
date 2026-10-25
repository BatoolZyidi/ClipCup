"""
Clip Cup REST API Views.
Endpoints:
- POST /api/jobs         : Create processing job (authenticated users only)
- GET  /api/jobs/<id>   : Retrieve job status/result (owner or admin)
- GET  /api/jobs/history: List current user's past jobs
- GET  /api/health      : Service health check
"""

import logging
import os
import tempfile
from pathlib import Path

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Job
from .pipeline.ingest import validate_source
from .services import submit_job

logger = logging.getLogger("clipcup.views")


def _job_summary(job: Job) -> dict:
    """Dict for history list with full details."""
    return {
        "id": job.id,
        "status": job.status,
        "step": job.step,
        "source_type": job.source_type,
        "source_input": job.source_input,
        "topic": job.topic,
        "reason": job.reason,
        "stats": job.stats,
        "result_url": job.result_url,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


def _job_detail(job: Job) -> dict:
    """Full dict for single job response."""
    return {
        "id": job.id,
        "status": job.status,
        "step": job.step,
        "source_type": job.source_type,
        "source_input": job.source_input,
        "topic": job.topic,
        "reason": job.reason,
        "stats": job.stats,
        "result_url": job.result_url,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


def _check_api_key(request) -> bool:
    """Verifies optional legacy API key if CLIP_CUP_API_KEY is configured."""
    required_key = os.getenv("CLIP_CUP_API_KEY", "").strip()
    if not required_key:
        return True

    header_key = request.headers.get("X-API-Key", "")
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and not required_key:
        header_key = auth_header.split(" ", 1)[1].strip()

    return header_key == required_key


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({"status": "ok", "service": "clipcup"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_history(request):
    """
    GET /api/jobs/history
    Returns the authenticated user's past jobs, newest first.
    """
    jobs = Job.objects.filter(user=request.user).order_by("-created_at")[:50]
    return Response({"jobs": [_job_summary(j) for j in jobs]})


@api_view(["POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def create_job(request):
    """
    Submits a new video reframing job for the authenticated user.
    Accepts:
    1. Multipart file upload: request.FILES['file'] or request.FILES['video']
    2. JSON payload: {"url": "https://..."}
    """
    # 1. Handle uploaded file
    uploaded_file = request.FILES.get("file") or request.FILES.get("video")
    if uploaded_file:
        temp_dir = Path(tempfile.mkdtemp(prefix="clipcup_upload_"))
        temp_file_path = temp_dir / f"upload_{uploaded_file.name}"

        with open(temp_file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        try:
            validate_source(str(temp_file_path))
        except Exception as e:
            temp_file_path.unlink(missing_ok=True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        job = submit_job(
            str(temp_file_path),
            source_type="UPLOAD",
            is_temp_upload=True,
            user=request.user,
        )
        return Response(_job_detail(job), status=status.HTTP_201_CREATED)

    # 2. Handle direct URL payload
    url = request.data.get("url") if isinstance(request.data, dict) else None
    if url:
        url = str(url).strip()
        try:
            validate_source(url)
        except ValueError as val_err:
            return Response({"error": str(val_err)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            return Response({"error": f"Invalid URL: {err}"}, status=status.HTTP_400_BAD_REQUEST)

        job = submit_job(url, source_type="URL", is_temp_upload=False, user=request.user)
        return Response(_job_detail(job), status=status.HTTP_201_CREATED)

    return Response(
        {"error": "Please provide either a video file upload or a JSON body with a 'url'."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_job(request, job_id: str):
    """
    Retrieves status, progress step, viral topic, reframing stats, result_url, and error.
    Users can only view their own jobs.
    """
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": f"Job '{job_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

    # Only the owner or admin can view a job
    if job.user_id and job.user_id != request.user.id and not request.user.is_staff:
        return Response({"error": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    return Response(_job_detail(job))
