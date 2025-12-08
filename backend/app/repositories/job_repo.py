from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.candidate_score import CandidateScore
from app.models.job import Job
from app.models.resume import Resume, ResumeStatus


def get(db: Session, job_id: int) -> Job | None:
    return db.get(Job, job_id)


def get_owned(db: Session, job_id: int, owner_id: int) -> Job | None:
    return db.execute(
        select(Job).where(Job.id == job_id, Job.owner_id == owner_id)
    ).scalar_one_or_none()


def list_for_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 50) -> list[Job]:
    return list(
        db.execute(
            select(Job)
            .where(Job.owner_id == owner_id)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).scalars()
    )


def stats_for_job(db: Session, job_id: int) -> dict:
    resume_count = db.query(func.count(Resume.id)).filter(Resume.job_id == job_id).scalar() or 0
    scored_count = (
        db.query(func.count(Resume.id))
        .filter(Resume.job_id == job_id, Resume.status == ResumeStatus.scored)
        .scalar()
        or 0
    )
    avg = (
        db.query(func.avg(CandidateScore.overall_score))
        .filter(CandidateScore.job_id == job_id)
        .scalar()
    )
    return {
        "resume_count": resume_count,
        "scored_count": scored_count,
        "average_score": round(float(avg), 2) if avg else 0.0,
    }


def create(db: Session, job: Job) -> Job:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def save(db: Session, job: Job) -> Job:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def delete(db: Session, job: Job) -> None:
    db.delete(job)
    db.commit()
