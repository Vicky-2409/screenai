from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession
from app.models.job import Job
from app.repositories import job_repo
from app.schemas.job import JobCreate, JobOut, JobUpdate, JobWithStats
from app.services.activity import log_activity
from app.workers.tasks import embed_job_task, rescore_job_task

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _get_owned_or_404(db, job_id: int, user) -> Job:
    job = job_repo.get_owned(db, job_id, user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, db: DbSession, user: CurrentUser):
    job = Job(owner_id=user.id, **payload.model_dump())
    job = job_repo.create(db, job)
    log_activity(
        db, user_id=user.id, action="job_created", entity_type="job", entity_id=job.id,
        message=f"Created job '{job.title}'",
    )
    # Embed the job description asynchronously for semantic search.
    embed_job_task.delay(job.id)
    return job


@router.get("", response_model=list[JobWithStats])
def list_jobs(db: DbSession, user: CurrentUser, skip: int = 0, limit: int = 50):
    jobs = job_repo.list_for_owner(db, user.id, skip=skip, limit=limit)
    results: list[JobWithStats] = []
    for job in jobs:
        stats = job_repo.stats_for_job(db, job.id)
        results.append(JobWithStats(**JobOut.model_validate(job).model_dump(), **stats))
    return results


@router.get("/{job_id}", response_model=JobWithStats)
def get_job(job_id: int, db: DbSession, user: CurrentUser):
    job = _get_owned_or_404(db, job_id, user)
    stats = job_repo.stats_for_job(db, job.id)
    return JobWithStats(**JobOut.model_validate(job).model_dump(), **stats)


@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: int, payload: JobUpdate, db: DbSession, user: CurrentUser):
    job = _get_owned_or_404(db, job_id, user)
    data = payload.model_dump(exclude_unset=True)
    requires_reembed = any(
        k in data for k in ("title", "description", "responsibilities", "qualifications", "skills")
    )
    for key, value in data.items():
        setattr(job, key, value)
    job = job_repo.save(db, job)
    log_activity(db, user_id=user.id, action="job_updated", entity_type="job", entity_id=job.id)
    if requires_reembed:
        # Re-embed the JD and re-score existing candidates against the new requirements.
        embed_job_task.delay(job.id)
        rescore_job_task.delay(job.id)
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: DbSession, user: CurrentUser):
    job = _get_owned_or_404(db, job_id, user)
    job_repo.delete(db, job)
    log_activity(db, user_id=user.id, action="job_deleted", entity_type="job", entity_id=job_id)
