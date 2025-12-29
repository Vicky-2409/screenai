"""Service-level tests for auth flows that are awkward to exercise via HTTP."""
from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.services import auth_service


def _make_user(db_session) -> User:
    user = User(
        email=f"svc_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Svc User",
        hashed_password=auth_service.hash_password("originalpass1"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_password_reset_flow(db_session):
    user = _make_user(db_session)
    token = auth_service.create_password_reset_token(user)

    auth_service.reset_password(db_session, token, "brandnewpass2")
    db_session.refresh(user)

    # Old password no longer authenticates; new one does.
    with pytest.raises(HTTPException):
        auth_service.authenticate(db_session, user.email, "originalpass1")
    assert auth_service.authenticate(db_session, user.email, "brandnewpass2").id == user.id


def test_reset_password_invalid_token(db_session):
    with pytest.raises(HTTPException) as exc:
        auth_service.reset_password(db_session, "not-a-valid-token", "whatever12")
    assert exc.value.status_code == 400


def test_authenticate_wrong_password(db_session):
    user = _make_user(db_session)
    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate(db_session, user.email, "wrongpassword")
    assert exc.value.status_code == 401


def test_issue_and_rotate_tokens(db_session):
    user = _make_user(db_session)
    _access, refresh = auth_service.issue_tokens(db_session, user)
    new_access, new_refresh = auth_service.rotate_refresh_token(db_session, refresh)
    assert new_access and new_refresh

    # Reusing the rotated (now revoked) token must fail.
    with pytest.raises(HTTPException) as exc:
        auth_service.rotate_refresh_token(db_session, refresh)
    assert exc.value.status_code == 401
