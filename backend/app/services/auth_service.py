from __future__ import annotations

from datetime import datetime, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.repositories import user_repo
from app.schemas.auth import RegisterRequest

PASSWORD_RESET_TYPE = "password_reset"


def register_user(db: Session, payload: RegisterRequest) -> User:
    if user_repo.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    # First user becomes an admin so the admin panel is reachable out of the box.
    role = UserRole.admin if user_repo.count(db) == 0 else UserRole.recruiter
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=role,
    )
    return user_repo.create(db, user)


def authenticate(db: Session, email: str, password: str) -> User:
    user = user_repo.get_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access = create_access_token(str(user.id), extra={"role": user.role.value})
    refresh, jti, expires_at = create_refresh_token(str(user.id))
    db.add(RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at))
    db.commit()
    return access, refresh


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[str, str]:
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    stored = db.query(RefreshToken).filter(RefreshToken.jti == jti).one_or_none()
    if not stored or stored.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or unknown"
        )
    if stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = user_repo.get_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate: revoke the old token, issue a fresh pair.
    stored.revoked = True
    db.add(stored)
    return issue_tokens(db, user)


def create_password_reset_token(user: User) -> str:
    return create_access_token(str(user.id), extra={"type_override": PASSWORD_RESET_TYPE})


def reset_password(db: Session, token: str, new_password: str) -> None:
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
        ) from exc
    user = user_repo.get_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.hashed_password = hash_password(new_password)
    # Revoke all refresh tokens on password change.
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked": True})
    db.add(user)
    db.commit()
