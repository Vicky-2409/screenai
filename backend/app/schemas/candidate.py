from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.candidate_score import CandidateStatus


class CandidateBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    email: str | None
    phone: str | None
    location: str | None
    designation: str | None
    total_experience_years: float
    skills: list[str]


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overall_score: float
    semantic_score: float
    skill_score: float
    experience_score: float
    education_score: float
    keyword_score: float
    matching_skills: list[str]
    missing_skills: list[str]
    additional_skills: list[str]
    summary: str | None
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str | None
    culture_fit: str | None
    interview_questions: list[str]
    score_breakdown: dict
    status: CandidateStatus


class RankedCandidate(BaseModel):
    rank: int
    candidate: CandidateBase
    score: ScoreOut


class CandidateDetail(CandidateBase):
    education: list[dict]
    experience: list[dict]
    certifications: list[str]
    projects: list[dict]
    companies: list[str]
    notes: str | None
    resume_id: int
    created_at: datetime
    score: ScoreOut | None = None


class CandidateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RankedCandidate]


class StatusUpdate(BaseModel):
    status: CandidateStatus


class NotesUpdate(BaseModel):
    notes: str


class SkillGap(BaseModel):
    matched: list[str]
    missing: list[str]
    additional: list[str]
    job_skills: list[str]
    candidate_skills: list[str]
