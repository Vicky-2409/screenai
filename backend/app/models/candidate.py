from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, index=True
    )

    name: Mapped[str | None] = mapped_column(String(255), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(String(255))
    designation: Mapped[str | None] = mapped_column(String(255))
    total_experience_years: Mapped[float] = mapped_column(Float, default=0)

    # Normalized structured data extracted by the parser.
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    education: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    experience: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    certifications: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    projects: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    companies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    notes: Mapped[str | None] = mapped_column(Text)

    resume: Mapped["Resume"] = relationship(back_populates="candidate")  # noqa: F821
    scores: Mapped[list["CandidateScore"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
    candidate_skills: Mapped[list["CandidateSkill"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
