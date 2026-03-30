from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import (
    AuthContext,
    create_access_token,
    require_admin_user,
    validate_admin_credentials,
)
from app.schemas.auth import AuthMeResponse, LoginRequest, TokenResponse
from app.services.audit_log_service import append_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not validate_admin_credentials(payload.username, payload.password):
        append_audit_event(
            "auth_failure",
            {
                "reason": "invalid_credentials",
                "username": payload.username,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token, expires_in = create_access_token(subject=payload.username, role="admin")
    append_audit_event(
        "auth_success",
        {
            "subject": payload.username,
            "role": "admin",
        },
    )

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
    )


@router.get("/me", response_model=AuthMeResponse)
def me(current_admin: AuthContext = Depends(require_admin_user)) -> AuthMeResponse:
    return AuthMeResponse(sub=current_admin.subject, role=current_admin.role)
