from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ResumeStatus(str, enum.Enum):
    uploaded = "uploaded"
    parsing = "parsing"
    parsed = "parsed"
    scoring = "scoring"
    scored = "scored"
    failed = "failed"


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    raw_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus, name="resume_status"), default=ResumeStatus.uploaded, index=True
    )
    error: Mapped[str | None] = mapped_column(Text)

    job: Mapped["Job"] = relationship(back_populates="resumes")  # noqa: F821
    candidate: Mapped["Candidate"] = relationship(  # noqa: F821
        back_populates="resume", uselist=False, cascade="all, delete-orphan"
    )
