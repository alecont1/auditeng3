"""File storage service using Cloudflare R2.

Files are stored in R2 bucket organized by task_id.
S3-compatible API via boto3.
"""

import io
import logging
from uuid import UUID

import boto3
from botocore.config import Config
from fastapi import UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_r2_client():
    """Get configured R2 client."""
    return boto3.client(
        service_name="s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def get_object_key(task_id: UUID, filename: str) -> str:
    """Get the R2 object key for a file.

    Args:
        task_id: The unique identifier for the task.
        filename: The name of the file.

    Returns:
        str: The object key (path) in R2.
    """
    return f"{task_id}/{filename}"


async def save_file(task_id: UUID, file: UploadFile) -> tuple[str, int]:
    """Save an uploaded file to R2.

    Args:
        task_id: The unique identifier for the task.
        file: The uploaded file from FastAPI.

    Returns:
        tuple[str, int]: The object key and file size in bytes.
    """
    filename = file.filename or "document"
    object_key = get_object_key(task_id, filename)

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Upload to R2
    client = get_r2_client()
    client.upload_fileobj(
        io.BytesIO(content),
        settings.R2_BUCKET_NAME,
        object_key,
        ExtraArgs={"ContentType": file.content_type or "application/octet-stream"}
    )

    logger.info(f"Uploaded {object_key} to R2 ({file_size} bytes)")
    return object_key, file_size


async def get_file(task_id: UUID, filename: str) -> bytes | None:
    """Download a file from R2.

    Args:
        task_id: The unique identifier for the task.
        filename: The name of the file.

    Returns:
        bytes | None: The file content if exists, None otherwise.
    """
    object_key = get_object_key(task_id, filename)
    client = get_r2_client()

    try:
        response = client.get_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=object_key
        )
        return response["Body"].read()
    except client.exceptions.NoSuchKey:
        logger.warning(f"File not found in R2: {object_key}")
        return None
    except Exception as e:
        logger.error(f"Error downloading from R2: {e}")
        return None


def delete_task_files(task_id: UUID) -> None:
    """Delete all files for a task from R2.

    Args:
        task_id: The unique identifier for the task.
    """
    client = get_r2_client()
    prefix = f"{task_id}/"

    try:
        # List objects with prefix
        response = client.list_objects_v2(
            Bucket=settings.R2_BUCKET_NAME,
            Prefix=prefix
        )

        if "Contents" in response:
            objects = [{"Key": obj["Key"]} for obj in response["Contents"]]
            if objects:
                client.delete_objects(
                    Bucket=settings.R2_BUCKET_NAME,
                    Delete={"Objects": objects}
                )
                logger.info(f"Deleted {len(objects)} files for task {task_id}")
    except Exception as e:
        logger.error(f"Error deleting files from R2: {e}")
