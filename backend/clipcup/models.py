"""
Clip Cup Database Models.
Tracks video processing jobs per user, lifecycle stages, reframing metrics, and delivery URLs.
"""

import uuid
from django.contrib.auth.models import User
from django.db import models


def generate_job_id() -> str:
    return f"job_{uuid.uuid4().hex[:12]}"


class JobStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    INGESTING = "INGESTING", "Ingesting"
    TRANSCRIBING = "TRANSCRIBING", "Transcribing"
    SELECTING = "SELECTING", "Selecting"
    REFRAMING = "REFRAMING", "Reframing"
    RENDERING = "RENDERING", "Rendering"
    STORING = "STORING", "Storing"
    DONE = "DONE", "Done"
    FAILED = "FAILED", "Failed"


class Job(models.Model):
    """
    Represents an automated short-form reframing job tied to a user account.
    Anonymous jobs (user=None) are allowed only when CLIP_CUP_API_KEY auth is used.
    """
    id = models.CharField(max_length=64, primary_key=True, default=generate_job_id, editable=False)
    # Link job to authenticated user — null for API-key-only flows
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs",
    )
    status = models.CharField(max_length=32, choices=JobStatus.choices, default=JobStatus.PENDING)
    step = models.CharField(max_length=64, default="pending")
    source_type = models.CharField(max_length=16, default="URL")  # URL or UPLOAD
    source_input = models.CharField(max_length=1024, blank=True, null=True)

    topic = models.CharField(max_length=256, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    stats = models.JSONField(default=dict, blank=True)

    result_url = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        owner = self.user.username if self.user_id else "anon"
        return f"{self.id} [{self.status}] by {owner}"
