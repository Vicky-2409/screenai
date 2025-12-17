from __future__ import annotations

from pydantic import BaseModel


class StatPoint(BaseModel):
    label: str
    value: float


class DashboardStats(BaseModel):
    total_jobs: int
    total_resumes: int
    candidates_screened: int
    average_match_score: float
    processing_queue: int


class DashboardAnalytics(BaseModel):
    stats: DashboardStats
    skill_distribution: list[StatPoint]
    score_distribution: list[StatPoint]
    top_skills: list[StatPoint]
    missing_skills: list[StatPoint]
    hiring_funnel: list[StatPoint]
    resume_sources: list[StatPoint]
    job_performance: list[StatPoint]
    recent_activity: list[dict]
    time_saved_hours: float
