from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import compare_digest
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.services.audit_log_service import append_audit_event

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthContext:
    subject: str
    role: str


def _epoch_seconds(value: datetime) -> int:
    return int(value.timestamp())


def validate_admin_password_policy(
    password: str,
    min_length: int,
) -> tuple[bool, list[str]]:
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
    settings = get_settings()
    return compare_digest(username, settings.admin_username) and compare_digest(
        password,
        settings.admin_password,
    )


def create_access_token(subject: str, role: str = "admin") -> tuple[str, int]:
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
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def try_extract_auth_context(authorization: str | None) -> AuthContext | None:
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


def require_admin_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
) -> AuthContext:
    settings = get_settings()

    if not settings.auth_required:
        return AuthContext(subject="dev-admin", role="admin")

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
            detail="Missing Bearer token",
        )

    if credentials.scheme.lower() != "bearer":
        append_audit_event(
            "auth_failure",
            {
                "reason": "invalid_auth_scheme",
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
        )

    context = try_extract_auth_context(f"Bearer {credentials.credentials}")
    if context is None:
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

    if context.role != "admin":
        append_audit_event(
            "auth_failure",
            {
                "reason": "insufficient_role",
                "role": context.role,
                "subject": context.subject,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return context
