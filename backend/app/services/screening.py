"""Orchestration of parse -> embed -> score -> analyze for resumes and jobs."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.cache import cache_delete, dashboard_cache_key
from app.core.logging import get_logger
from app.models.candidate import Candidate
from app.models.candidate_score import CandidateScore
from app.models.job import Job
from app.models.resume import Resume, ResumeStatus
from app.repositories import embedding_repo
from app.services import matching
from app.services.activity import log_activity
from app.services.ai import get_ai_provider
from app.services.parsing import parse_resume_file

logger = get_logger(__name__)


def embed_job(db: Session, job: Job) -> list[float]:
    provider = get_ai_provider()
    text = matching.build_job_text(job)
    vector = provider.embed_texts([text])[0]
    emb = embedding_repo.upsert(db, "job", job.id, vector, provider.name)
    job.embedding_id = emb.id
    db.add(job)
    db.commit()
    return vector


def parse_resume(db: Session, resume: Resume) -> Candidate:
    """Extract text and structured fields, persisting a Candidate row."""
    resume.status = ResumeStatus.parsing
    db.add(resume)
    db.commit()

    parsed = parse_resume_file(resume.stored_path, resume.content_type)
    resume.raw_text = parsed.raw_text

    candidate = db.query(Candidate).filter(Candidate.resume_id == resume.id).one_or_none()
    if candidate is None:
        candidate = Candidate(resume_id=resume.id)

    candidate.name = parsed.name
    candidate.email = parsed.email
    candidate.phone = parsed.phone
    candidate.location = parsed.location
    candidate.designation = parsed.designation
    candidate.total_experience_years = parsed.total_experience_years
    candidate.skills = parsed.skills
    candidate.education = parsed.education
    candidate.experience = parsed.experience
    candidate.certifications = parsed.certifications
    candidate.projects = parsed.projects
    candidate.companies = parsed.companies

    db.add(candidate)
    resume.status = ResumeStatus.parsed
    db.add(resume)
    db.commit()
    db.refresh(candidate)
    return candidate


def score_candidate(db: Session, resume: Resume, run_ai: bool = True) -> CandidateScore:
    """Embed the resume, compute weighted match, and run AI analysis."""
    job: Job = db.get(Job, resume.job_id)
    candidate = db.query(Candidate).filter(Candidate.resume_id == resume.id).one()

    resume.status = ResumeStatus.scoring
    db.add(resume)
    db.commit()

    provider = get_ai_provider()

    # Ensure the job has an embedding.
    job_emb = embedding_repo.get(db, "job", job.id)
    if job_emb is None:
        job_vector = embed_job(db, job)
    else:
        job_vector = list(job_emb.vector)

    # Embed the resume text.
    resume_text = matching.build_resume_text(candidate, resume.raw_text or "")
    resume_vector = provider.embed_texts([resume_text])[0]
    embedding_repo.upsert(db, "resume", resume.id, resume_vector, provider.name)

    result = matching.compute_match(
        job=job,
        candidate=candidate,
        resume_text=resume.raw_text or "",
        job_vector=job_vector,
        resume_vector=resume_vector,
    )

    score = db.query(CandidateScore).filter(
        CandidateScore.candidate_id == candidate.id, CandidateScore.job_id == job.id
    ).one_or_none()
    if score is None:
        score = CandidateScore(candidate_id=candidate.id, job_id=job.id)

    score.overall_score = result.overall_score
    score.semantic_score = result.semantic_score
    score.skill_score = result.skill_score
    score.experience_score = result.experience_score
    score.education_score = result.education_score
    score.keyword_score = result.keyword_score
    score.matching_skills = result.matching_skills
    score.missing_skills = result.missing_skills
    score.additional_skills = result.additional_skills
    score.score_breakdown = result.breakdown

    if run_ai:
        analysis_context = {
            "overall_score": result.overall_score,
            "semantic_score": result.semantic_score,
            "education_score": result.education_score,
            "matching_skills": result.matching_skills,
            "missing_skills": result.missing_skills,
            "total_experience_years": candidate.total_experience_years,
            "min_experience_years": job.min_experience_years,
            "name": candidate.name,
        }
        analysis = provider.analyze_candidate(
            matching.build_job_text(job), resume.raw_text or "", analysis_context
        )
        score.summary = analysis.summary
        score.strengths = analysis.strengths
        score.weaknesses = analysis.weaknesses
        score.recommendation = analysis.recommendation
        score.culture_fit = analysis.culture_fit
        score.interview_questions = analysis.interview_questions
        if analysis.missing_skills:
            score.missing_skills = analysis.missing_skills
        if analysis.matching_skills:
            score.matching_skills = analysis.matching_skills

    db.add(score)
    resume.status = ResumeStatus.scored
    db.add(resume)
    log_activity(
        db,
        user_id=resume.uploader_id,
        action="candidate_scored",
        entity_type="candidate",
        entity_id=candidate.id,
        message=f"{candidate.name or 'Candidate'} scored {result.overall_score:.0f}%",
        commit=False,
    )
    db.commit()
    db.refresh(score)
    # New scores change dashboard aggregates: drop the owner's cached analytics.
    if job is not None and job.owner_id is not None:
        cache_delete(dashboard_cache_key(job.owner_id))
    return score


def process_resume(db: Session, resume_id: int) -> None:
    """Full pipeline for one resume: parse then score."""
    resume = db.get(Resume, resume_id)
    if resume is None:
        return
    try:
        parse_resume(db, resume)
        score_candidate(db, resume)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Resume processing failed for %s", resume_id)
        resume.status = ResumeStatus.failed
        resume.error = str(exc)[:1000]
        db.add(resume)
        db.commit()
        raise
