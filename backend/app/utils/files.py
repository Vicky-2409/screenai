from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}


def _ensure_upload_dir(job_id: int) -> Path:
    base = Path(settings.upload_dir) / f"job_{job_id}"
    base.mkdir(parents=True, exist_ok=True)
    return base


def validate_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{suffix}'. Allowed: PDF, DOCX, TXT.",
        )
    return suffix


def save_upload(file: UploadFile, job_id: int) -> dict:
    """Persist an upload to disk safely and return file metadata."""
    suffix = validate_upload(file)
    contents = file.file.read()

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit.",
        )
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")

    content_hash = hashlib.sha256(contents).hexdigest()
    target_dir = _ensure_upload_dir(job_id)
    # Randomized stored name avoids path traversal and collisions.
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    stored_path = target_dir / stored_name
    stored_path.write_bytes(contents)

    return {
        "original_filename": Path(file.filename or stored_name).name,
        "stored_path": str(stored_path),
        "content_type": file.content_type,
        "file_size": len(contents),
        "content_hash": content_hash,
    }
