from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession
from app.models.candidate_score import CandidateStatus
from app.repositories import candidate_repo, job_repo
from app.schemas.candidate import (
    CandidateBase,
    CandidateDetail,
    CandidateListResponse,
    NotesUpdate,
    RankedCandidate,
    ScoreOut,
    SkillGap,
    StatusUpdate,
)
from app.services.activity import log_activity

router = APIRouter(tags=["candidates"])


def _assert_job_owner(db, job_id: int, user):
    if job_repo.get_owned(db, job_id, user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.get("/jobs/{job_id}/candidates", response_model=CandidateListResponse)
def list_candidates(
    job_id: int,
    db: DbSession,
    user: CurrentUser,
    search: str | None = None,
    candidate_status: CandidateStatus | None = Query(default=None, alias="status"),
    min_score: float | None = None,
    sort_by: str = "overall_score",
    sort_dir: str = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    _assert_job_owner(db, job_id, user)
    total, rows = candidate_repo.list_ranked(
        db,
        job_id=job_id,
        search=search,
        status=candidate_status,
        min_score=min_score,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    items = [
        RankedCandidate(
            rank=(page - 1) * page_size + idx + 1,
            candidate=CandidateBase.model_validate(cand),
            score=ScoreOut.model_validate(score),
        )
        for idx, (cand, score) in enumerate(rows)
    ]
    return CandidateListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/candidates/{candidate_id}", response_model=CandidateDetail)
def get_candidate(candidate_id: int, db: DbSession, user: CurrentUser, job_id: int | None = None):
    candidate = candidate_repo.get(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    resume = candidate.resume
    _assert_job_owner(db, resume.job_id, user)

    detail = CandidateDetail.model_validate(candidate)
    target_job = job_id or resume.job_id
    score = candidate_repo.get_score(db, candidate_id, target_job)
    if score:
        detail.score = ScoreOut.model_validate(score)
    return detail


@router.get("/candidates/{candidate_id}/skill-gap", response_model=SkillGap)
def skill_gap(candidate_id: int, db: DbSession, user: CurrentUser, job_id: int | None = None):
    candidate = candidate_repo.get(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    _assert_job_owner(db, candidate.resume.job_id, user)
    target_job = job_id or candidate.resume.job_id
    score = candidate_repo.get_score(db, candidate_id, target_job)
    job = job_repo.get(db, target_job)
    return SkillGap(
        matched=score.matching_skills if score else [],
        missing=score.missing_skills if score else [],
        additional=score.additional_skills if score else [],
        job_skills=job.skills if job else [],
        candidate_skills=candidate.skills,
    )


@router.patch("/candidates/{candidate_id}/status", response_model=ScoreOut)
def update_status(
    candidate_id: int, payload: StatusUpdate, db: DbSession, user: CurrentUser, job_id: int | None = None
):
    candidate = candidate_repo.get(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    _assert_job_owner(db, candidate.resume.job_id, user)
    target_job = job_id or candidate.resume.job_id
    score = candidate_repo.get_score(db, candidate_id, target_job)
    if score is None:
        raise HTTPException(status_code=404, detail="Score not found")
    score.status = payload.status
    db.add(score)
    log_activity(
        db, user_id=user.id, action="status_changed", entity_type="candidate",
        entity_id=candidate_id, message=f"Status -> {payload.status.value}", commit=False,
    )
    db.commit()
    db.refresh(score)
    return ScoreOut.model_validate(score)


@router.patch("/candidates/{candidate_id}/notes", response_model=CandidateBase)
def update_notes(candidate_id: int, payload: NotesUpdate, db: DbSession, user: CurrentUser):
    candidate = candidate_repo.get(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    _assert_job_owner(db, candidate.resume.job_id, user)
    candidate.notes = payload.notes
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return CandidateBase.model_validate(candidate)
