from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.core.deps import CurrentUser, DbSession
from app.repositories import job_repo
from app.services import reports as reports_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _assert_job_owner(db, job_id: int, user):
    if job_repo.get_owned(db, job_id, user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.get("/{job_id}/csv")
def report_csv(job_id: int, db: DbSession, user: CurrentUser):
    _assert_job_owner(db, job_id, user)
    data = reports_service.generate_csv(db, job_id)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_candidates.csv"},
    )


@router.get("/{job_id}/pdf")
def report_pdf(job_id: int, db: DbSession, user: CurrentUser):
    _assert_job_owner(db, job_id, user)
    data = reports_service.generate_pdf(db, job_id)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_report.pdf"},
    )
