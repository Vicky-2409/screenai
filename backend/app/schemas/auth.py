from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenPair):
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordResponse(BaseModel):
    message: str
    # In development we surface the reset token so the flow is testable end-to-end
    # without an email provider. In production this is hidden.
    reset_token: str | None = None
