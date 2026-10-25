"""
Tests for Clip Cup REST API and Job Worker integration.
"""

import os
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Job, JobStatus


class ClipCupAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_create_job_rejects_youtube(self):
        response = self.client.post(
            "/api/jobs",
            {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("YouTube and web video page URLs are not supported", response.json()["error"])

    def test_create_job_missing_payload(self):
        response = self.client.post("/api/jobs", {}, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("clipcup.services._EXECUTOR.submit")
    def test_create_job_with_url(self, mock_submit):
        response = self.client.post(
            "/api/jobs",
            {"url": "https://example.com/test_video.mp4"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["status"], "PENDING")

        job = Job.objects.get(id=data["id"])
        self.assertEqual(job.source_type, "URL")
        self.assertEqual(job.source_input, "https://example.com/test_video.mp4")
        self.assertTrue(mock_submit.called)

    @patch("clipcup.services._EXECUTOR.submit")
    def test_create_job_with_file_upload(self, mock_submit):
        fake_video = SimpleUploadedFile(
            "test_clip.mp4",
            b"fake video content header bytes",
            content_type="video/mp4",
        )
        response = self.client.post(
            "/api/jobs",
            {"file": fake_video},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)

        job = Job.objects.get(id=data["id"])
        self.assertEqual(job.source_type, "UPLOAD")
        self.assertTrue(mock_submit.called)

    def test_get_job_status(self):
        job = Job.objects.create(
            status=JobStatus.DONE,
            step="done",
            topic="Viral Moment",
            reason="High engagement hook",
            stats={"face_hit_rate": 0.95, "avg_jitter_px": 2.1},
            result_url="https://s3.amazonaws.com/test-bucket/shorts/test.mp4",
        )

        response = self.client.get(f"/api/jobs/{job.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], job.id)
        self.assertEqual(data["status"], "DONE")
        self.assertEqual(data["topic"], "Viral Moment")
        self.assertEqual(data["stats"]["face_hit_rate"], 0.95)
        self.assertEqual(data["result_url"], job.result_url)

    def test_get_nonexistent_job(self):
        response = self.client.get("/api/jobs/job_nonexistent_999")
        self.assertEqual(response.status_code, 404)

    def test_api_key_auth(self):
        with patch.dict(os.environ, {"CLIP_CUP_API_KEY": "supersecretkey"}):
            # Unauthorized request
            unauth_res = self.client.get("/api/jobs/job_123")
            self.assertEqual(unauth_res.status_code, 401)

            # Authorized with X-API-Key
            client_auth = APIClient()
            client_auth.credentials(HTTP_X_API_KEY="supersecretkey")
            auth_res = self.client.get("/api/health")
            self.assertEqual(auth_res.status_code, 200)
