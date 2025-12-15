from __future__ import annotations

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.notification import NotificationLevel
from app.models.resume import Resume
from app.services import screening
from app.services.activity import push_notification
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="resume.process", bind=True, max_retries=2, default_retry_delay=10)
def process_resume_task(self, resume_id: int) -> dict:
    db = SessionLocal()
    try:
        screening.process_resume(db, resume_id)
        return {"resume_id": resume_id, "status": "scored"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("process_resume_task failed for %s", resume_id)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="job.embed")
def embed_job_task(job_id: int) -> dict:
    from app.models.job import Job

    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job:
            screening.embed_job(db, job)
        return {"job_id": job_id, "status": "embedded"}
    finally:
        db.close()


@celery_app.task(name="resume.bulk_process")
def bulk_process_task(resume_ids: list[int], notify_user_id: int | None = None) -> dict:
    """Process many resumes, then notify the recruiter on completion."""
    succeeded, failed = 0, 0
    for rid in resume_ids:
        try:
            process_resume_task.run(rid)
            succeeded += 1
        except Exception:  # noqa: BLE001
            failed += 1

    if notify_user_id is not None:
        db = SessionLocal()
        try:
            push_notification(
                db,
                user_id=notify_user_id,
                title="Bulk processing complete",
                message=f"{succeeded} resumes scored, {failed} failed.",
                level=NotificationLevel.success if failed == 0 else NotificationLevel.warning,
            )
        finally:
            db.close()
    return {"succeeded": succeeded, "failed": failed, "total": len(resume_ids)}


@celery_app.task(name="resume.rescore_job")
def rescore_job_task(job_id: int) -> dict:
    db = SessionLocal()
    try:
        resumes = db.query(Resume).filter(Resume.job_id == job_id).all()
        count = 0
        for resume in resumes:
            try:
                screening.score_candidate(db, resume)
                count += 1
            except Exception:  # noqa: BLE001
                logger.exception("Re-scoring failed for resume %s", resume.id)
        return {"job_id": job_id, "rescored": count}
    finally:
        db.close()
