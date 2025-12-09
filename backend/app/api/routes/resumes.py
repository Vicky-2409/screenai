from __future__ import annotations

import os

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DbSession
from app.models.resume import Resume, ResumeStatus
from app.repositories import job_repo
from app.schemas.resume import BulkProgress, ResumeOut, UploadResponse
from app.services.activity import log_activity
from app.utils.files import save_upload
from app.workers.tasks import bulk_process_task, process_resume_task

router = APIRouter(tags=["resumes"])


def _get_owned_job_or_404(db, job_id: int, user):
    job = job_repo.get_owned(db, job_id, user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/upload", response_model=UploadResponse, status_code=201)
def upload_resumes(
    job_id: int,
    db: DbSession,
    user: CurrentUser,
    files: list[UploadFile] = File(...),
):
    """Upload one or many resumes for a job. Processing happens asynchronously."""
    _get_owned_job_or_404(db, job_id, user)
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    created: list[Resume] = []
    for file in files:
        meta = save_upload(file, job_id)
        resume = Resume(
            job_id=job_id,
            uploader_id=user.id,
            status=ResumeStatus.uploaded,
            **meta,
        )
        db.add(resume)
        created.append(resume)
    db.commit()
    for resume in created:
        db.refresh(resume)

    resume_ids = [r.id for r in created]
    if len(resume_ids) > 1:
        bulk_process_task.delay(resume_ids, notify_user_id=user.id)
        task_ids = ["bulk"]
    else:
        task = process_resume_task.delay(resume_ids[0])
        task_ids = [task.id]

    log_activity(
        db, user_id=user.id, action="resumes_uploaded", entity_type="job", entity_id=job_id,
        message=f"Uploaded {len(created)} resume(s)", meta={"count": len(created)},
    )
    return UploadResponse(
        job_id=job_id,
        uploaded=[ResumeOut.model_validate(r) for r in created],
        task_ids=task_ids,
        message=f"{len(created)} resume(s) queued for processing.",
    )


@router.get("/jobs/{job_id}/resumes", response_model=list[ResumeOut])
def list_resumes(job_id: int, db: DbSession, user: CurrentUser):
    _get_owned_job_or_404(db, job_id, user)
    resumes = db.query(Resume).filter(Resume.job_id == job_id).order_by(Resume.created_at.desc()).all()
    return [ResumeOut.model_validate(r) for r in resumes]


@router.get("/jobs/{job_id}/progress", response_model=BulkProgress)
def processing_progress(job_id: int, db: DbSession, user: CurrentUser):
    _get_owned_job_or_404(db, job_id, user)
    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()
    total = len(resumes)
    parsed = sum(1 for r in resumes if r.status in (ResumeStatus.parsed, ResumeStatus.scoring, ResumeStatus.scored))
    scored = sum(1 for r in resumes if r.status == ResumeStatus.scored)
    failed = sum(1 for r in resumes if r.status == ResumeStatus.failed)
    pending = total - scored - failed
    return BulkProgress(job_id=job_id, total=total, parsed=parsed, scored=scored, failed=failed, pending=pending)


@router.get("/resumes/{resume_id}/file")
def get_resume_file(resume_id: int, db: DbSession, user: CurrentUser):
    """Stream the original uploaded resume file (owner only)."""
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    if job_repo.get_owned(db, resume.job_id, user.id) is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if not resume.stored_path or not os.path.exists(resume.stored_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        resume.stored_path,
        media_type=resume.content_type or "application/octet-stream",
        filename=resume.original_filename,
    )


@router.delete("/resumes/{resume_id}", status_code=204)
def delete_resume(resume_id: int, db: DbSession, user: CurrentUser):
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    job = job_repo.get_owned(db, resume.job_id, user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    db.delete(resume)
    db.commit()
    log_activity(db, user_id=user.id, action="resume_deleted", entity_type="resume", entity_id=resume_id)
