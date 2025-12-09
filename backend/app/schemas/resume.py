from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.resume import ResumeStatus


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    original_filename: str
    content_type: str | None
    file_size: int
    status: ResumeStatus
    error: str | None
    created_at: datetime


class UploadResponse(BaseModel):
    job_id: int
    uploaded: list[ResumeOut]
    task_ids: list[str]
    message: str


class BulkProgress(BaseModel):
    job_id: int
    total: int
    parsed: int
    scored: int
    failed: int
    pending: int
