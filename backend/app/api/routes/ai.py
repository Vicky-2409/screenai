from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.deps import CurrentUser, DbSession
from app.models.resume import Resume
from app.repositories import candidate_repo, embedding_repo, job_repo
from app.schemas.candidate import CandidateBase, RankedCandidate, ScoreOut
from app.services import screening
from app.services.ai import get_ai_provider
from app.workers.tasks import rescore_job_task

router = APIRouter(tags=["ai"])


class ScreenRequest(BaseModel):
    job_id: int


class AnalyzeRequest(BaseModel):
    candidate_id: int
    job_id: int | None = None


class MatchRequest(BaseModel):
    resume_id: int


class SemanticSearchRequest(BaseModel):
    query: str
    job_id: int | None = None
    limit: int = 20


def _assert_job_owner(db, job_id: int, user):
    if job_repo.get_owned(db, job_id, user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.post("/screen")
def screen_job(payload: ScreenRequest, db: DbSession, user: CurrentUser):
    """(Re)score every resume attached to a job asynchronously."""
    _assert_job_owner(db, payload.job_id, user)
    task = rescore_job_task.delay(payload.job_id)
    return {"job_id": payload.job_id, "task_id": task.id, "message": "Screening started"}


@router.post("/match", response_model=ScoreOut)
def match_single(payload: MatchRequest, db: DbSession, user: CurrentUser):
    """Synchronously parse, embed and score a single resume (useful for quick checks)."""
    resume = db.get(Resume, payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    _assert_job_owner(db, resume.job_id, user)
    if resume.candidate is None:
        screening.parse_resume(db, resume)
    score = screening.score_candidate(db, resume)
    return ScoreOut.model_validate(score)


@router.post("/analyze", response_model=ScoreOut)
def analyze_candidate(payload: AnalyzeRequest, db: DbSession, user: CurrentUser):
    """Re-run AI analysis (summary, strengths, recommendation) for a candidate."""
    candidate = candidate_repo.get(db, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    _assert_job_owner(db, candidate.resume.job_id, user)
    score = screening.score_candidate(db, candidate.resume, run_ai=True)
    return ScoreOut.model_validate(score)


@router.post("/search", response_model=list[RankedCandidate])
def semantic_search(payload: SemanticSearchRequest, db: DbSession, user: CurrentUser):
    """Vector similarity search over candidate resumes using pgvector."""
    if payload.job_id is not None:
        _assert_job_owner(db, payload.job_id, user)

    provider = get_ai_provider()
    query_vector = provider.embed_texts([payload.query])[0]
    results = embedding_repo.semantic_search_resume_ids(
        db, query_vector, payload.job_id, payload.limit
    )

    ranked: list[RankedCandidate] = []
    for rank, (resume_id, distance) in enumerate(results, start=1):
        candidate = candidate_repo.get_by_resume(db, resume_id)
        if candidate is None:
            continue
        resume = candidate.resume
        # Only surface candidates from jobs the recruiter owns.
        if job_repo.get_owned(db, resume.job_id, user.id) is None:
            continue
        score = candidate_repo.get_score(db, candidate.id, resume.job_id)
        if score is None:
            continue
        # Convert cosine distance (0=identical) to a similarity percentage.
        similarity = max(0.0, (1 - distance)) * 100
        score_out = ScoreOut.model_validate(score)
        score_out.semantic_score = round(similarity, 2)
        ranked.append(
            RankedCandidate(
                rank=rank, candidate=CandidateBase.model_validate(candidate), score=score_out
            )
        )
    return ranked
