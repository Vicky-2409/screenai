from __future__ import annotations

from collections import Counter

from fastapi import APIRouter
from sqlalchemy import func

from app.core.cache import cache_get, cache_set, dashboard_cache_key
from app.core.deps import CurrentUser, DbSession
from app.models.activity_log import ActivityLog
from app.models.candidate import Candidate
from app.models.candidate_score import CandidateScore, CandidateStatus
from app.models.job import Job
from app.models.resume import Resume, ResumeStatus
from app.schemas.analytics import DashboardAnalytics, DashboardStats, StatPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Rough estimate: manual screening of one resume costs ~10 minutes.
MINUTES_SAVED_PER_RESUME = 10


@router.get("/dashboard", response_model=DashboardAnalytics)
def dashboard(db: DbSession, user: CurrentUser):
    cache_key = dashboard_cache_key(user.id)
    cached = cache_get(cache_key)
    if cached is not None:
        return DashboardAnalytics(**cached)

    job_ids = [j.id for j in db.query(Job.id).filter(Job.owner_id == user.id).all()]

    total_jobs = len(job_ids)
    if not job_ids:
        empty = DashboardStats(
            total_jobs=0, total_resumes=0, candidates_screened=0,
            average_match_score=0, processing_queue=0,
        )
        empty_result = DashboardAnalytics(
            stats=empty, skill_distribution=[], score_distribution=[], top_skills=[],
            missing_skills=[], hiring_funnel=[], resume_sources=[], job_performance=[],
            recent_activity=[], time_saved_hours=0,
        )
        cache_set(cache_key, empty_result.model_dump(mode="json"), ttl_seconds=30)
        return empty_result

    total_resumes = db.query(func.count(Resume.id)).filter(Resume.job_id.in_(job_ids)).scalar() or 0
    screened = (
        db.query(func.count(Resume.id))
        .filter(Resume.job_id.in_(job_ids), Resume.status == ResumeStatus.scored)
        .scalar()
        or 0
    )
    avg = db.query(func.avg(CandidateScore.overall_score)).filter(CandidateScore.job_id.in_(job_ids)).scalar()
    queue = (
        db.query(func.count(Resume.id))
        .filter(Resume.job_id.in_(job_ids), Resume.status.notin_([ResumeStatus.scored, ResumeStatus.failed]))
        .scalar()
        or 0
    )

    stats = DashboardStats(
        total_jobs=total_jobs,
        total_resumes=total_resumes,
        candidates_screened=screened,
        average_match_score=round(float(avg), 2) if avg else 0.0,
        processing_queue=queue,
    )

    # Skill distribution + top skills from candidate skills.
    candidates = (
        db.query(Candidate)
        .join(Resume, Resume.id == Candidate.resume_id)
        .filter(Resume.job_id.in_(job_ids))
        .all()
    )
    skill_counter: Counter = Counter()
    for c in candidates:
        skill_counter.update(c.skills or [])
    top_skills = [StatPoint(label=k, value=v) for k, v in skill_counter.most_common(10)]
    skill_distribution = [StatPoint(label=k, value=v) for k, v in skill_counter.most_common(8)]

    # Missing skills aggregated across scores.
    missing_counter: Counter = Counter()
    scores = db.query(CandidateScore).filter(CandidateScore.job_id.in_(job_ids)).all()
    for s in scores:
        missing_counter.update(s.missing_skills or [])
    missing_skills = [StatPoint(label=k, value=v) for k, v in missing_counter.most_common(10)]

    # Score distribution buckets.
    buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for s in scores:
        v = s.overall_score
        if v < 20:
            buckets["0-20"] += 1
        elif v < 40:
            buckets["20-40"] += 1
        elif v < 60:
            buckets["40-60"] += 1
        elif v < 80:
            buckets["60-80"] += 1
        else:
            buckets["80-100"] += 1
    score_distribution = [StatPoint(label=k, value=v) for k, v in buckets.items()]

    # Hiring funnel by status.
    funnel_counter: Counter = Counter(s.status.value for s in scores)
    funnel_order = [s.value for s in CandidateStatus]
    hiring_funnel = [
        StatPoint(label=st.replace("_", " ").title(), value=funnel_counter.get(st, 0))
        for st in funnel_order
    ]

    # Resume sources: distribution by file format (proxy for source channel).
    source_counter: Counter = Counter()
    resume_rows = (
        db.query(Resume.original_filename, Resume.content_type)
        .filter(Resume.job_id.in_(job_ids))
        .all()
    )
    for filename, content_type in resume_rows:
        ext = (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
        if ext in ("pdf",) or (content_type and "pdf" in content_type):
            source_counter["PDF"] += 1
        elif ext in ("docx", "doc") or (content_type and "word" in content_type):
            source_counter["DOCX"] += 1
        elif ext in ("txt",) or (content_type and "text" in content_type):
            source_counter["TXT"] += 1
        else:
            source_counter["Other"] += 1
    resume_sources = [StatPoint(label=k, value=v) for k, v in source_counter.most_common()]

    # Job performance: average overall score per job.
    job_perf_rows = (
        db.query(Job.title, func.avg(CandidateScore.overall_score))
        .join(CandidateScore, CandidateScore.job_id == Job.id)
        .filter(Job.id.in_(job_ids))
        .group_by(Job.id, Job.title)
        .all()
    )
    job_performance = [
        StatPoint(label=(title or "Untitled")[:24], value=round(float(avg_score), 1))
        for title, avg_score in job_perf_rows
        if avg_score is not None
    ]

    recent = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {
            "action": a.action,
            "message": a.message,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "created_at": a.created_at.isoformat(),
        }
        for a in recent
    ]

    time_saved_hours = round(screened * MINUTES_SAVED_PER_RESUME / 60, 1)

    result = DashboardAnalytics(
        stats=stats,
        skill_distribution=skill_distribution,
        score_distribution=score_distribution,
        top_skills=top_skills,
        missing_skills=missing_skills,
        hiring_funnel=hiring_funnel,
        resume_sources=resume_sources,
        job_performance=job_performance,
        recent_activity=recent_activity,
        time_saved_hours=time_saved_hours,
    )
    cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=30)
    return result
