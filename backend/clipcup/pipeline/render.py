"""
Clip Cup Pipeline - Step 5: Render and FFmpeg Video/Audio Muxing.
Reads frames via OpenCV VideoCapture, crops to 9:16, resizes to 1080x1920,
and streams raw BGR24 frames into an FFmpeg subprocess that encodes H.264 (yuv420p)
and muxes original segment audio (-c:a aac -movflags +faststart).
Uses a temporary file for stderr to guarantee deadlock-free streaming on Windows.
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any
import cv2

logger = logging.getLogger("clipcup.pipeline.render")

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def render_short(
    source_video: Path,
    segment: Dict[str, Any],
    crop_boxes: List[Tuple[int, int, int, int]],
    fps: float,
    output_path: Path,
    job_id: str = "default",
) -> Path:
    """
    Renders the vertical 9:16 short at 1080x1920 with synchronized segment audio.
    """
    extra = {"job_id": job_id}
    start_ms = segment["start_ms"]
    end_ms = segment["end_ms"]
    duration_s = (end_ms - start_ms) / 1000.0

    start_frame = int(round((start_ms / 1000.0) * fps))
    total_frames = len(crop_boxes)

    logger.info(
        f"Rendering {total_frames} frames ({duration_s:.2f}s @ {fps:.2f}fps) to {output_path}...",
        extra=extra,
    )

    cap = cv2.VideoCapture(str(source_video))
    if not cap.isOpened():
        raise ValueError(f"Failed to open source video for rendering: {source_video}")

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the ffmpeg muxing command
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{TARGET_WIDTH}x{TARGET_HEIGHT}",
        "-pix_fmt", "bgr24",
        "-r", f"{fps:.4f}",
        "-i", "-",  # Video input from stdin pipe
        "-ss", f"{start_ms / 1000.0:.3f}",
        "-to", f"{end_ms / 1000.0:.3f}",
        "-i", str(source_video),  # Audio input from trimmed source
        "-map", "0:v:0",
        "-map", "1:a:0?",  # Audio is mapped if present
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]

    with tempfile.TemporaryFile() as err_file:
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=err_file,
        )

        frames_written = 0
        try:
            for i, (cx, cy, cw, ch) in enumerate(crop_boxes):
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning(
                        f"Video stream ended early at frame {i}/{total_frames}", extra=extra
                    )
                    break

                # Crop according to computed bounding box
                cropped = frame[cy : cy + ch, cx : cx + cw]

                # Resize to strict 1080x1920
                resized = cv2.resize(
                    cropped,
                    (TARGET_WIDTH, TARGET_HEIGHT),
                    interpolation=cv2.INTER_LINEAR,
                )

                # Stream raw bytes into FFmpeg stdin
                proc.stdin.write(resized.tobytes())
                frames_written += 1

                if frames_written % 150 == 0:
                    logger.info(
                        f"Rendering progress: {frames_written}/{total_frames} frames ({(frames_written / total_frames) * 100:.1f}%)",
                        extra=extra,
                    )

            proc.stdin.close()
            proc.wait()

            if proc.returncode != 0:
                err_file.seek(0)
                err_msg = err_file.read().decode("utf-8", errors="replace")
                logger.error(f"FFmpeg encoding error (code {proc.returncode}): {err_msg}", extra=extra)
                raise RuntimeError(f"FFmpeg render failed: {err_msg}")

        except Exception as e:
            logger.error(f"Render pipeline failed: {e}", extra=extra)
            if proc.poll() is None:
                proc.kill()
            raise
        finally:
            cap.release()

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Rendered file is missing or zero bytes: {output_path}")

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(
        f"Render finished successfully: {output_path.name} ({size_mb:.2f} MB, {frames_written} frames)",
        extra=extra,
    )

    return output_path
