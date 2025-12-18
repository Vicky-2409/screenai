from __future__ import annotations

import os
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func

from app.core.config import settings
from app.core.deps import AdminUser, DbSession
from app.models.activity_log import ActivityLog
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminStats(BaseModel):
    total_users: int
    total_jobs: int
    total_resumes: int
    total_candidates: int


class StorageBreakdown(BaseModel):
    label: str
    files: int
    bytes: int


class StorageStats(BaseModel):
    total_bytes: int
    total_files: int
    breakdown: list[StorageBreakdown]


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    message: str | None
    created_at: datetime


@router.get("/stats", response_model=AdminStats)
def admin_stats(db: DbSession, admin: AdminUser):
    return AdminStats(
        total_users=db.query(func.count(User.id)).scalar() or 0,
        total_jobs=db.query(func.count(Job.id)).scalar() or 0,
        total_resumes=db.query(func.count(Resume.id)).scalar() or 0,
        total_candidates=db.query(func.count(Candidate.id)).scalar() or 0,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: DbSession, admin: AdminUser):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/toggle-active", response_model=UserOut)
def toggle_active(user_id: int, db: DbSession, admin: AdminUser):
    user = db.get(User, user_id)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/logs", response_model=list[ActivityLogOut])
def list_logs(db: DbSession, admin: AdminUser, limit: int = 100):
    return db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit).all()


def _format_label(ext: str) -> str:
    ext = ext.lstrip(".").lower()
    if ext == "pdf":
        return "PDF"
    if ext in ("docx", "doc"):
        return "DOCX"
    if ext == "txt":
        return "TXT"
    return ext.upper() or "Other"


@router.get("/storage", response_model=StorageStats)
def storage_stats(admin: AdminUser):
    """Walk the upload directory and report total/per-format storage usage."""
    upload_dir = settings.upload_dir
    total_bytes = 0
    total_files = 0
    buckets: dict[str, dict[str, int]] = {}

    if os.path.isdir(upload_dir):
        for root, _dirs, files in os.walk(upload_dir):
            for name in files:
                fpath = os.path.join(root, name)
                try:
                    size = os.path.getsize(fpath)
                except OSError:
                    continue
                total_bytes += size
                total_files += 1
                label = _format_label(os.path.splitext(name)[1])
                entry = buckets.setdefault(label, {"files": 0, "bytes": 0})
                entry["files"] += 1
                entry["bytes"] += size

    breakdown = [
        StorageBreakdown(label=label, files=v["files"], bytes=v["bytes"])
        for label, v in sorted(buckets.items(), key=lambda kv: kv[1]["bytes"], reverse=True)
    ]
    return StorageStats(total_bytes=total_bytes, total_files=total_files, breakdown=breakdown)
