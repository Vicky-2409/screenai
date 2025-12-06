from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.user import UserOut
from app.services import auth_service
from app.services.activity import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, db: DbSession):
    user = auth_service.register_user(db, payload)
    access, refresh = auth_service.issue_tokens(db, user)
    log_activity(db, user_id=user.id, action="register", entity_type="user", entity_id=user.id)
    return AuthResponse(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: DbSession):
    user = auth_service.authenticate(db, payload.email, payload.password)
    access, refresh = auth_service.issue_tokens(db, user)
    log_activity(db, user_id=user.id, action="login", entity_type="user", entity_id=user.id)
    return AuthResponse(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/token", response_model=TokenPair, include_in_schema=False)
def token(db: DbSession, form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password flow endpoint to support Swagger 'Authorize'."""
    user = auth_service.authenticate(db, form_data.username, form_data.password)
    access, refresh = auth_service.issue_tokens(db, user)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(payload: RefreshRequest, db: DbSession):
    access, refresh = auth_service.rotate_refresh_token(db, payload.refresh_token)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: DbSession):
    from app.repositories import user_repo

    user = user_repo.get_by_email(db, payload.email)
    reset_token = auth_service.create_password_reset_token(user) if user else None
    # Always return the same message to avoid user enumeration.
    return ForgotPasswordResponse(
        message="If an account exists for that email, a reset link has been sent.",
        reset_token=reset_token if settings.debug else None,
    )


@router.post("/reset-password", status_code=204)
def reset_password(payload: ResetPasswordRequest, db: DbSession):
    auth_service.reset_password(db, payload.token, payload.new_password)


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser):
    return current_user
