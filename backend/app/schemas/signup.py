"""Signup schema for public registration."""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class SignupRequest(BaseModel):
    """Public signup request."""

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER


class SignupResponse(BaseModel):
    """Signup response."""

    id: str
    username: str
    email: str
    role: str
    message: str = "Account created successfully"