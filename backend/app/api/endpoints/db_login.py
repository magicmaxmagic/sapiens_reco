"""Database-based login endpoint for user authentication."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.audit_log_service import append_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])
ph = PasswordHasher()


@router.post("/db-login", response_model=TokenResponse)
def db_login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Login using database-stored credentials."""
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.username)
    ).first()
    
    if not user:
        append_audit_event(
            "auth_failure",
            {"reason": "user_not_found", "username": payload.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Verify password
    try:
        ph.verify(user.password_hash, payload.password)
    except VerifyMismatchError:
        append_audit_event(
            "auth_failure",
            {"reason": "invalid_password", "username": payload.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Check if user is active
    if not user.is_active:
        append_audit_event(
            "auth_failure",
            {"reason": "user_inactive", "username": payload.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )
    
    # Create token
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    token, expires_in = create_access_token(subject=str(user.id), role=role_str)
    
    append_audit_event(
        "auth_success",
        {
            "user_id": str(user.id),
            "username": user.username,
            "role": role_str,
        },
    )
    
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
    )
