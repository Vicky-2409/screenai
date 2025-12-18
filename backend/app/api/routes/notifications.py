from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.core.deps import CurrentUser, DbSession
from app.models.notification import Notification, NotificationLevel

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str | None
    level: NotificationLevel
    read: bool
    created_at: datetime


@router.get("", response_model=list[NotificationOut])
def list_notifications(db: DbSession, user: CurrentUser, unread_only: bool = False):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.read.is_(False))
    return q.order_by(Notification.created_at.desc()).limit(50).all()


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, db: DbSession, user: CurrentUser):
    note = db.get(Notification, notification_id)
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    note.read = True
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.post("/read-all", status_code=204)
def mark_all_read(db: DbSession, user: CurrentUser):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.read.is_(False)
    ).update({"read": True})
    db.commit()
