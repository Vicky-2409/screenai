from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.candidate import Candidate
from app.models.candidate_score import CandidateScore, CandidateStatus


def get(db: Session, candidate_id: int) -> Candidate | None:
    return db.get(Candidate, candidate_id)


def get_by_resume(db: Session, resume_id: int) -> Candidate | None:
    return db.execute(
        select(Candidate).where(Candidate.resume_id == resume_id)
    ).scalar_one_or_none()


def get_score(db: Session, candidate_id: int, job_id: int) -> CandidateScore | None:
    return db.execute(
        select(CandidateScore).where(
            CandidateScore.candidate_id == candidate_id, CandidateScore.job_id == job_id
        )
    ).scalar_one_or_none()


def list_ranked(
    db: Session,
    *,
    job_id: int,
    search: str | None = None,
    status: CandidateStatus | None = None,
    min_score: float | None = None,
    sort_by: str = "overall_score",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 20,
    restrict_ids: list[int] | None = None,
) -> tuple[int, list[tuple[Candidate, CandidateScore]]]:
    stmt = (
        select(Candidate, CandidateScore)
        .join(CandidateScore, CandidateScore.candidate_id == Candidate.id)
        .options(joinedload(Candidate.scores))
        .where(CandidateScore.job_id == job_id)
    )

    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Candidate.name).like(like)
            | func.lower(Candidate.email).like(like)
            | func.lower(Candidate.designation).like(like)
        )
    if status is not None:
        stmt = stmt.where(CandidateScore.status == status)
    if min_score is not None:
        stmt = stmt.where(CandidateScore.overall_score >= min_score)
    if restrict_ids is not None:
        if not restrict_ids:
            return 0, []
        stmt = stmt.where(Candidate.id.in_(restrict_ids))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    sort_column = {
        "overall_score": CandidateScore.overall_score,
        "experience": Candidate.total_experience_years,
        "name": Candidate.name,
        "created_at": Candidate.created_at,
    }.get(sort_by, CandidateScore.overall_score)
    sort_column = sort_column.desc() if sort_dir == "desc" else sort_column.asc()

    stmt = stmt.order_by(sort_column).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(stmt).unique().all()
    return total, [(row[0], row[1]) for row in rows]
