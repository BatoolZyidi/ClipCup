"""
Clip Cup Pipeline - Step 1: Ingestion and Audio Extraction.
Ensures no persistent source storage: uses isolated per-job temporary directory.
Supports:
  - Local file upload paths
  - Direct video URLs (.mp4, .mov, .mkv, .webm, .m4v, etc.)
  - YouTube and other platform URLs (via yt-dlp)
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
import cv2
import requests

logger = logging.getLogger("clipcup.pipeline.ingest")

MAX_DURATION_SECONDS = 600.0  # 10 minutes limit
CHUNK_SIZE = 1024 * 1024       # 1MB chunks for streaming download

# Extensions treated as direct video links (no yt-dlp needed)
DIRECT_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".flv", ".ts")

# Domains that serve video pages (require yt-dlp, not direct HTTP download)
PLATFORM_DOMAINS = (
    "youtube.com", "youtu.be",
    "vimeo.com",
    "tiktok.com",
    "instagram.com",
    "twitter.com", "x.com",
    "facebook.com", "fb.watch",
    "dailymotion.com",
    "twitch.tv",
)


def _is_platform_url(url: str) -> bool:
    """Returns True if the URL is a video-platform page that needs yt-dlp."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().lstrip("www.")
    return any(domain == d or domain.endswith("." + d) for d in PLATFORM_DOMAINS)


def _is_direct_video_url(url: str) -> bool:
    """Returns True if the URL path ends with a known video extension."""
    path_lower = urlparse(url).path.lower()
    return any(path_lower.endswith(ext) for ext in DIRECT_VIDEO_EXTENSIONS)


def validate_source(source: str) -> None:
    """
    Validates whether the provided source string is a supported local file
    or a supported video URL. All URLs (including YouTube) are accepted;
    only truly empty or missing local files are rejected.
    """
    if not source or not source.strip():
        raise ValueError("Source video path or URL cannot be empty.")

    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        # All HTTP(S) URLs are accepted; yt-dlp handles platforms, requests handles direct links
        return

    # Local file path validation
    local_path = Path(source)
    if not local_path.is_file():
        raise FileNotFoundError(f"Local video file not found: {source}")


def _download_with_ytdlp(url: str, output_path: Path, job_id: str) -> None:
    """
    Downloads a video from YouTube/Vimeo/TikTok etc. using yt-dlp.
    Enforces the 10-minute duration limit via --match-filter.
    Raises RuntimeError if yt-dlp is not installed or download fails.
    """
    import sys
    extra = {"job_id": job_id}

    # Check yt-dlp is available either as a binary on PATH or as a Python module
    ytdlp = shutil.which("yt-dlp")
    if ytdlp:
        cmd_prefix = [ytdlp]
    else:
        # Fall back to invoking via current Python interpreter module
        cmd_prefix = [sys.executable, "-m", "yt_dlp"]

    logger.info(f"Downloading via yt-dlp: {url}", extra=extra)

    cmd = cmd_prefix + [
        "--no-playlist",
        "--match-filter", f"duration <= {int(MAX_DURATION_SECONDS)}",  # reject > 10 min
        "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
        "--merge-output-format", "mp4",
        "--concurrent-fragments", "4",
        "--no-warnings",
        "--socket-timeout", "30",
        "-o", str(output_path),
        url,
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600,  # 10-minute download timeout
        )
        if proc.returncode != 0:
            stderr_snippet = proc.stderr[-800:] if proc.stderr else ""
            raise RuntimeError(
                f"yt-dlp exited with code {proc.returncode}. "
                f"stderr: {stderr_snippet}"
            )
    except subprocess.TimeoutExpired:
        raise RuntimeError("yt-dlp download timed out after 600 seconds.")


def _probe_video(video_path: Path) -> dict:
    """
    Inspects video dimensions, fps, duration, and frame count using OpenCV
    with ffprobe fallback for highest precision.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    duration = total_frames / fps if fps > 0 else 0.0

    # Also try ffprobe if available for exact stream info
    ffprobe_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path),
    ]
    try:
        res = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        ff_duration = float(data.get("format", {}).get("duration", 0.0))
        if ff_duration > 0:
            duration = ff_duration
    except Exception:
        # Fall back to OpenCV duration
        pass

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "total_frames": total_frames,
        "duration": duration,
    }


def ingest_video(source: str, job_dir: Path, job_id: str = "default") -> dict:
    """
    Downloads or copies the source video into job_dir / 'source.mp4',
    enforces duration <= 10 min, and extracts audio via ffmpeg to job_dir / 'audio.wav'.
    Supports local files, direct video URLs, and YouTube / platform URLs.
    """
    extra = {"job_id": job_id}
    validate_source(source)

    target_video_path = job_dir / "source.mp4"
    audio_path = job_dir / "audio.wav"

    parsed = urlparse(source)
    is_url = parsed.scheme in ("http", "https")

    if is_url:
        if _is_platform_url(source) or not _is_direct_video_url(source):
            # Use yt-dlp for platform pages and ambiguous URLs
            logger.info(
                f"Platform URL detected — downloading via yt-dlp: {source}",
                extra=extra,
            )
            try:
                _download_with_ytdlp(source, target_video_path, job_id)
            except Exception as e:
                logger.error(f"yt-dlp download failed: {e}", extra=extra)
                raise ValueError(f"Could not download video: {e}") from e
        else:
            # Direct link to a raw video file — stream with requests
            logger.info(f"Downloading direct video URL: {source}", extra=extra)
            try:
                with requests.get(source, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    if "text/html" in content_type:
                        # Likely a page URL — retry with yt-dlp
                        logger.warning(
                            "URL returned HTML; falling back to yt-dlp.", extra=extra
                        )
                        _download_with_ytdlp(source, target_video_path, job_id)
                    else:
                        with open(target_video_path, "wb") as f:
                            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                                if chunk:
                                    f.write(chunk)
            except Exception as e:
                logger.error(f"Failed to download video URL: {e}", extra=extra)
                raise ValueError(f"Failed to download video: {e}") from e
    else:
        # Local file
        source_path = Path(source).resolve()
        logger.info(
            f"Copying local video from {source_path} to temp job directory",
            extra=extra,
        )
        shutil.copyfile(source_path, target_video_path)

    # Validate video readability and duration
    probe = _probe_video(target_video_path)
    logger.info(
        f"Video probed: {probe['width']}x{probe['height']} @ {probe['fps']:.2f}fps, "
        f"duration={probe['duration']:.2f}s ({probe['total_frames']} frames)",
        extra=extra,
    )

    if probe["duration"] > MAX_DURATION_SECONDS:
        raise ValueError(
            f"Video duration ({probe['duration']:.1f}s) exceeds maximum allowed limit of "
            f"{MAX_DURATION_SECONDS:.0f}s (10 minutes)."
        )

    if probe["duration"] <= 0:
        raise ValueError("Video duration is zero or invalid.")

    # Extract 16kHz mono audio via ffmpeg for transcription
    logger.info("Extracting audio stream using ffmpeg...", extra=extra)
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(target_video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(audio_path),
    ]

    try:
        subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.warning(
            f"FFmpeg audio extraction failed or no audio track found: {e.stderr}",
            extra=extra,
        )
        # If no audio track exists, synthesize silence so downstream can proceed
        silence_cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=16000:cl=mono",
            "-t", str(min(probe["duration"], 10.0)),
            str(audio_path),
        ]
        subprocess.run(silence_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    return {
        "video_path": target_video_path,
        "audio_path": audio_path,
        "width": probe["width"],
        "height": probe["height"],
        "fps": probe["fps"],
        "total_frames": probe["total_frames"],
        "duration": probe["duration"],
    }
