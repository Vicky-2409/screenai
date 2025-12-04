from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ReportType(str, enum.Enum):
    pdf = "pdf"
    csv = "csv"


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType, name="report_type"))
    stored_path: Mapped[str] = mapped_column(String(1024))
