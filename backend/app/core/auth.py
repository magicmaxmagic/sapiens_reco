"""Authentication utilities for FastAPI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import compare_digest
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_token
from app.models.session import Session as UserSession
from app.models.user import User, UserRole
from app.services.audit_log_service import append_audit_event

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthContext:
    """Authentication context extracted from token."""

    subject: str
    role: str
    user_id: str | None = None


def _epoch_seconds(value: datetime) -> int:
    return int(value.timestamp())


def validate_admin_password_policy(
    password: str,
    min_length: int,
) -> tuple[bool, list[str]]:
    """Validate admin password meets security requirements."""
    violations: list[str] = []

    if len(password) < min_length:
        violations.append(f"minimum_length<{min_length}")

    if not any(char.islower() for char in password):
        violations.append("missing_lowercase")

    if not any(char.isupper() for char in password):
        violations.append("missing_uppercase")

    if not any(char.isdigit() for char in password):
        violations.append("missing_digit")

    if not any((not char.isalnum()) and (not char.isspace()) for char in password):
        violations.append("missing_special_char")

    return len(violations) == 0, violations


def validate_admin_credentials(username: str, password: str) -> bool:
    """Validate admin credentials (legacy single-admin mode)."""
    settings = get_settings()
    return compare_digest(username, settings.admin_username) and compare_digest(
        password, settings.admin_password
    )


def create_access_token(subject: str, role: str = "admin") -> tuple[str, int]:
    """Create a JWT access token."""
    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.jwt_access_token_minutes)

    payload: dict[str, object] = {
        "sub": subject,
        "role": role,
        "iat": _epoch_seconds(issued_at),
        "exp": _epoch_seconds(expires_at),
    }

    encoded = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    expires_in = int((expires_at - issued_at).total_seconds())
    return encoded, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def try_extract_auth_context(authorization: str | None) -> AuthContext | None:
    """Extract auth context from Authorization header (JWT mode)."""
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        payload = decode_access_token(token.strip())
    except InvalidTokenError:
        return None

    subject = payload.get("sub")
    role = payload.get("role")

    if not isinstance(subject, str) or not subject:
        return None
    if not isinstance(role, str) or not role:
        role = "unknown"

    return AuthContext(subject=subject, role=role)


def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    db: Session = Depends(get_db),
) -> User | None:
    """Get current authenticated user from token or session."""
    settings = get_settings()

    # Dev mode - no auth required
    if not settings.auth_required:
        # Return a dev admin user
        dev_user = User(
            id="dev-admin",
            email="dev@localhost",
            role=UserRole.ADMIN,
            is_active=True,
        )
        return dev_user

    if credentials is None:
        return None

    # Try session-based auth first
    token = credentials.credentials
    token_hash = hash_token(token)

    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == token_hash,
            UserSession.is_revoked.is_(False),
            UserSession.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if session:
        user = db.query(User).filter(User.id == session.user_id).first()
        if user and user.is_active:
            # Update session last used
            session.last_used_at = datetime.utcnow()
            db.commit()
            return user
        return None

    # Fall back to JWT auth (legacy)
    context = try_extract_auth_context(f"Bearer {token}")
    if context is None:
        return None

    # For JWT auth, get user by email or id
    user = db.query(User).filter(
        (User.email == context.subject) | (User.id == context.subject)
    ).first()

    if user and user.is_active:
        return user

    return None


def require_auth(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    db: Session = Depends(get_db),
) -> User:
    """Require authentication and return current user."""
    settings = get_settings()

    # Dev mode - no auth required
    if not settings.auth_required:
        return User(
            id="dev-admin",
            email="dev@localhost",
            role=UserRole.ADMIN,
            is_active=True,
        )

    if credentials is None:
        append_audit_event(
            "auth_failure",
            {
                "reason": "missing_bearer_token",
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = get_current_user(request, credentials, db)
    if user is None:
        append_audit_event(
            "auth_failure",
            {
                "reason": "invalid_or_expired_token",
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user


def require_role(*roles: UserRole):
    """Require specific role(s) for access."""

    async def role_checker(current_user: User = Depends(require_auth)) -> User:
        if current_user.role not in roles and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return role_checker


def require_admin_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    db: Session = Depends(get_db),
) -> User:
    """Require admin role for access."""
    return Depends(require_role(UserRole.ADMIN))