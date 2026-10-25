"""
Django Management Command: run_clip.
CLI interface to run the Clip Cup pipeline end-to-end on a video file or direct URL.
Usage:
    python manage.py run_clip <file_or_url> [--output <dest>] [--timeout <sec>]
"""

import sys
import time
from django.core.management.base import BaseCommand, CommandError
from clipcup.pipeline import run_pipeline, JobTimeoutError


class Command(BaseCommand):
    help = "Run the Clip Cup 9:16 vertical video conversion pipeline on a video file or direct URL."

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            type=str,
            help="Path to a local video file OR a direct video URL (.mp4, .mov, etc., max 10 min).",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Custom destination path for the rendered output MP4.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=900,
            help="Timeout in seconds for pipeline execution (default: 900 = 15 min).",
        )
        parser.add_argument(
            "--keep-temp",
            action="store_true",
            help="Retain temporary files after completion (debugging only; default false).",
        )
        parser.add_argument(
            "--job-id",
            type=str,
            default=None,
            help="Custom Job ID identifier.",
        )

    def handle(self, *args, **options):
        source = options["source"]
        output = options["output"]
        timeout = options["timeout"]
        keep_temp = options["keep_temp"]
        job_id = options["job_id"]

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        self.stdout.write(self.style.MIGRATE_HEADING("  CLIP CUP - Smart Vertical Video Reframing Pipeline"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        self.stdout.write(f"Source: {source}")
        if output:
            self.stdout.write(f"Custom Output: {output}")
        self.stdout.write(f"Timeout: {timeout}s\n")

        def progress_listener(step: str, data: dict):
            timestamp = time.strftime("%H:%M:%S")
            if step == "INGESTING":
                self.stdout.write(f"[{timestamp}] [1/6] Ingesting video & extracting audio stream...")
            elif step == "TRANSCRIBING":
                self.stdout.write(f"[{timestamp}] [2/6] Transcribing speech with word-level timestamps...")
            elif step == "SELECTING":
                self.stdout.write(f"[{timestamp}] [3/6] Analyzing transcript with Bedrock for viral highlight...")
            elif step == "REFRAMING":
                segment = data.get("segment", {})
                start_s = segment.get("start_ms", 0) / 1000.0
                end_s = segment.get("end_ms", 0) / 1000.0
                self.stdout.write(
                    f"[{timestamp}] [4/6] Reframing segment [{start_s:.1f}s - {end_s:.1f}s] with OpenCV YuNet..."
                )
            elif step == "RENDERING":
                self.stdout.write(f"[{timestamp}] [5/6] Rendering 1080x1920 H.264 video with segment audio...")
            elif step == "STORING":
                self.stdout.write(f"[{timestamp}] [6/6] Uploading short to S3 & generating presigned URL...")
            elif step == "DONE":
                self.stdout.write(self.style.SUCCESS(f"[{timestamp}] Pipeline execution finished successfully!"))
            elif step == "FAILED":
                self.stdout.write(self.style.ERROR(f"[{timestamp}] Pipeline failed: {data.get('error')}"))

        try:
            result = run_pipeline(
                source=source,
                job_id=job_id,
                progress_callback=progress_listener,
                timeout_seconds=timeout,
                keep_temp=keep_temp,
                output_path=output,
            )

            self.stdout.write("\n" + self.style.SUCCESS("=" * 70))
            self.stdout.write(self.style.SUCCESS("  JOB SUMMARY & RESULTS"))
            self.stdout.write(self.style.SUCCESS("=" * 70))
            self.stdout.write(f"Job ID:             {result['job_id']}")
            self.stdout.write(f"Status:             {result['status']}")
            self.stdout.write(f"Topic:              {result['topic']}")
            self.stdout.write(f"Reason:             {result['reason']}")
            self.stdout.write(
                f"Segment Window:     {result['start_ms']}ms - {result['end_ms']}ms "
                f"({result['segment_duration_s']:.1f}s)"
            )
            self.stdout.write(f"Processing Time:    {result['processing_time_s']}s")

            stats = result["stats"]
            self.stdout.write(self.style.MIGRATE_LABEL("\nOpenCV 5 Reframing Stats:"))
            self.stdout.write(f"  - Face Hit Rate:    {stats['face_hit_rate'] * 100:.1f}%")
            self.stdout.write(f"  - Avg Crop Jitter:  {stats['avg_jitter_px']} px/frame")
            self.stdout.write(f"  - Fallback Frames:  {stats['fallback_frames']} / {stats['total_frames']}")
            self.stdout.write(f"  - Scene Cuts:       {stats['scene_cuts']}")

            self.stdout.write(self.style.SUCCESS("\nOutput Delivery:"))
            self.stdout.write(f"  Result URL: {result['result_url']}")
            self.stdout.write("=" * 70 + "\n")

        except JobTimeoutError as e:
            self.stderr.write(self.style.ERROR(f"\nExecution timed out: {e}"))
            sys.exit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\nExecution failed: {e}"))
            sys.exit(1)
