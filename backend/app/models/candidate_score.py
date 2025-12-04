from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CandidateStatus(str, enum.Enum):
    new = "new"
    shortlisted = "shortlisted"
    rejected = "rejected"
    interviewing = "interviewing"
    hired = "hired"


class CandidateScore(Base, TimestampMixin):
    __tablename__ = "candidate_scores"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)

    overall_score: Mapped[float] = mapped_column(Float, default=0, index=True)
    semantic_score: Mapped[float] = mapped_column(Float, default=0)
    skill_score: Mapped[float] = mapped_column(Float, default=0)
    experience_score: Mapped[float] = mapped_column(Float, default=0)
    education_score: Mapped[float] = mapped_column(Float, default=0)
    keyword_score: Mapped[float] = mapped_column(Float, default=0)

    matching_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    missing_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    additional_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # AI analysis output
    summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    weaknesses: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    recommendation: Mapped[str | None] = mapped_column(String(255))
    culture_fit: Mapped[str | None] = mapped_column(Text)
    interview_questions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    score_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)

    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus, name="candidate_status"), default=CandidateStatus.new, index=True
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="scores")  # noqa: F821
    job: Mapped["Job"] = relationship(back_populates="scores")  # noqa: F821
