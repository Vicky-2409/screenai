from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class NotificationLevel(str, enum.Enum):
    info = "info"
    success = "success"
    warning = "warning"
    error = "error"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(String(1024))
    level: Mapped[NotificationLevel] = mapped_column(
        Enum(NotificationLevel, name="notification_level"), default=NotificationLevel.info
    )
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
