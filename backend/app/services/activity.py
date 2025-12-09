from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.notification import Notification, NotificationLevel


def log_activity(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    message: str | None = None,
    meta: dict | None = None,
    commit: bool = True,
) -> ActivityLog:
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
        meta=meta or {},
    )
    db.add(entry)
    if commit:
        db.commit()
    return entry


def push_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str | None = None,
    level: NotificationLevel = NotificationLevel.info,
    commit: bool = True,
) -> Notification:
    note = Notification(user_id=user_id, title=title, message=message, level=level)
    db.add(note)
    if commit:
        db.commit()
    return note
