from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class EmploymentType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    internship = "internship"
    temporary = "temporary"


class JobStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    draft = "draft"


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    experience: Mapped[str | None] = mapped_column(String(120))
    min_experience_years: Mapped[float] = mapped_column(default=0)
    salary: Mapped[str | None] = mapped_column(String(120))
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="employment_type"), default=EmploymentType.full_time
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.open, index=True
    )

    description: Mapped[str | None] = mapped_column(Text)  # rich text / responsibilities
    responsibilities: Mapped[str | None] = mapped_column(Text)
    qualifications: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    embedding_id: Mapped[int | None] = mapped_column(
        ForeignKey("embeddings.id", ondelete="SET NULL")
    )

    owner: Mapped["User"] = relationship(back_populates="jobs")  # noqa: F821
    resumes: Mapped[list["Resume"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan"
    )
    scores: Mapped[list["CandidateScore"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan"
    )
    embedding: Mapped["Embedding"] = relationship(foreign_keys=[embedding_id])  # noqa: F821
