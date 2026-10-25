"""
Clip Cup Pipeline - Step 6: AWS S3 Storage and 24-Hour Presigned URL Generation.
Uploads processed vertical video to S3 and creates presigned GET URL (expiry 24h / 86400s).
Provides fallback to local media directory when S3 is not configured.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("clipcup.pipeline.storage")

DEFAULT_EXPIRY_SECONDS = 86400  # 24 hours


def upload_and_presign(
    file_path: Path,
    job_id: str,
    expiry_seconds: int = DEFAULT_EXPIRY_SECONDS,
    bucket_name: Optional[str] = None,
    aws_region: Optional[str] = None,
) -> str:
    """
    Uploads the rendered MP4 file to AWS S3 and returns a 24-hour presigned URL.
    If S3 bucket is unconfigured, stores in local media folder and returns file URI.
    """
    extra = {"job_id": job_id}
    bucket = bucket_name or os.getenv("S3_BUCKET_NAME", "").strip()
    region = aws_region or os.getenv("AWS_REGION", "us-east-1").strip()

    if not bucket:
        logger.warning(
            "S3_BUCKET_NAME is not configured. Saving rendered output to local media storage.",
            extra=extra,
        )
        return _store_locally(file_path, job_id)

    object_key = f"shorts/{job_id}.mp4"
    logger.info(
        f"Uploading {file_path.name} ({file_path.stat().st_size / (1024*1024):.2f} MB) to s3://{bucket}/{object_key}...",
        extra=extra,
    )

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        s3_client = boto3.client("s3", region_name=region)

        s3_client.upload_file(
            Filename=str(file_path),
            Bucket=bucket,
            Key=object_key,
            ExtraArgs={
                "ContentType": "video/mp4",
                "ContentDisposition": f'inline; filename="clipcup_{job_id}.mp4"',
            },
        )

        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": object_key},
            ExpiresIn=expiry_seconds,
        )

        logger.info(
            f"Presigned S3 URL generated successfully (expires in {expiry_seconds}s).",
            extra=extra,
        )
        return presigned_url

    except Exception as e:
        logger.error(f"S3 upload or presigning failed: {e}", extra=extra)
        logger.warning("Falling back to local media storage due to S3 error.", extra=extra)
        return _store_locally(file_path, job_id)


def _store_locally(file_path: Path, job_id: str) -> str:
    """Stores output file in local media directory for offline/local access."""
    # Place in backend/media/shorts
    base_dir = Path(__file__).resolve().parent.parent.parent
    local_media_dir = base_dir / "media" / "shorts"
    local_media_dir.mkdir(parents=True, exist_ok=True)

    dest_file = local_media_dir / f"{job_id}.mp4"
    shutil.copyfile(file_path, dest_file)
    logger.info(f"Stored local copy at: {dest_file.resolve()}")

    return dest_file.resolve().as_uri()
