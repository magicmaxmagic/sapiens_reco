"""Authentication schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response."""

    id: UUID
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: str
    last_login: str | None = None

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""

    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str