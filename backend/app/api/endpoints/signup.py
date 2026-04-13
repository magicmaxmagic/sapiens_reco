"""Public signup endpoint for user registration."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import brute_force_protection, hash_password, validate_password_strength
from app.models.user import User, UserRole
from app.schemas.signup import SignupRequest, SignupResponse
from app.services.audit_log_service import append_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    db: Session = Depends(get_db),
) -> SignupResponse:
    """Public signup endpoint for creating new user accounts."""
    # Check brute force protection for email
    if brute_force_protection.is_locked(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Please try again later.",
        )

    # Validate password strength
    is_valid, violations = validate_password_strength(data.password)
    if not is_valid:
        violation_msg = ", ".join(violations)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {violation_msg}",
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        brute_force_protection.record_failure(data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == data.email).first()
    if existing_email:
        brute_force_protection.record_failure(data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user (only viewer role allowed for public signup)
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.VIEWER,  # Always viewer for public signup
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log the signup event
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    append_audit_event(
        "user_signup",
        {
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": role_str,
        },
    )

    return SignupResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=role_str,
        message="Account created successfully. Please log in.",
    )