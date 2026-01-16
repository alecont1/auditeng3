"""File storage service for managing uploaded documents.

This module provides async file operations for storing and retrieving
uploaded commissioning reports. Files are organized by task_id.
"""

import shutil
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import UploadFile

from app.config import get_settings

# Chunk size for streaming file uploads (64KB)
CHUNK_SIZE: int = 64 * 1024

settings = get_settings()

# Upload directory from settings
UPLOAD_DIR: Path = Path(settings.UPLOAD_DIR)

# Ensure upload directory exists on module load
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_file_path(task_id: UUID, filename: str) -> Path:
    """Get the full path for a file within a task's directory.

    Args:
        task_id: The unique identifier for the task.
        filename: The name of the file.

    Returns:
        Path: The full path to the file.
    """
    return UPLOAD_DIR / str(task_id) / filename


async def save_file(task_id: UUID, file: UploadFile) -> tuple[Path, int]:
    """Save an uploaded file to disk using streaming.

    Creates a task subdirectory and streams the file to disk
    in chunks to avoid loading large files into memory.

    Args:
        task_id: The unique identifier for the task.
        file: The uploaded file from FastAPI.

    Returns:
        tuple[Path, int]: The file path and total file size in bytes.

    Raises:
        IOError: If file cannot be written.
    """
    # Create task subdirectory
    task_dir = UPLOAD_DIR / str(task_id)
    task_dir.mkdir(parents=True, exist_ok=True)

    # Determine file path
    filename = file.filename or "document"
    file_path = task_dir / filename

    # Stream file to disk in chunks
    total_size = 0
    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await file.read(CHUNK_SIZE):
            await out_file.write(chunk)
            total_size += len(chunk)

    return file_path, total_size


async def get_file(task_id: UUID, filename: str) -> Path | None:
    """Get a file path if it exists.

    Args:
        task_id: The unique identifier for the task.
        filename: The name of the file.

    Returns:
        Path | None: The file path if it exists, None otherwise.
    """
    file_path = get_file_path(task_id, filename)
    if file_path.exists():
        return file_path
    return None


def delete_task_files(task_id: UUID) -> None:
    """Delete all files for a task.

    Removes the task directory and all its contents.

    Args:
        task_id: The unique identifier for the task.
    """
    task_dir = UPLOAD_DIR / str(task_id)
    if task_dir.exists():
        shutil.rmtree(task_dir)
