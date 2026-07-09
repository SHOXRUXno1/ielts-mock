"""S3 upload service for audio files (Timeweb S3-compatible storage)."""

import uuid

import boto3
from botocore.config import Config

from app.core.config import settings


def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def upload_audio(file_bytes: bytes, content_type: str = "audio/webm") -> str:
    """Upload audio bytes to S3 and return the public URL."""
    client = _get_client()
    key = f"audio/{uuid.uuid4()}.webm"

    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )

    if settings.s3_endpoint_url:
        return f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{key}"
    return f"https://{settings.s3_bucket_name}.s3.amazonaws.com/{key}"
