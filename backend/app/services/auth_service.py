"""Authentication service for user management."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    brute_force_protection,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.audit_log import AuditAction
from app.models.session import Session as UserSession
from app.models.user import User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    UserResponse,
)
from app.schemas.user import UserCreate

settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, data: UserCreate) -> User:
        """Create a new user."""
        # Validate password strength
        is_valid, violations = self._validate_password(data.password)
        if not is_valid:
            raise ValueError(f"Password does not meet requirements: {violations}")

        # Create user
        user = User(
            id=uuid4(),
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=data.role or UserRole.VIEWER,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._log_action(
            user.id, AuditAction.USER_CREATED, "user", user.id, details={"email": data.email}
        )
        return user

    def login(
        self, data: LoginRequest, ip_address: str | None = None, user_agent: str | None = None
    ) -> LoginResponse:
        """Authenticate a user and return tokens."""
        # Check brute force protection
        if brute_force_protection.is_locked(data.email):
            self._log_action(None, AuditAction.LOGIN_FAILED, "user", None, ip_address=ip_address)
            raise ValueError("Account temporarily locked due to too many failed attempts")

        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            brute_force_protection.record_failure(data.email)
            self._log_action(None, AuditAction.LOGIN_FAILED, "user", None, ip_address=ip_address)
            raise ValueError("Invalid credentials")

        if not user.is_active:
            self._log_action(
                user.id, AuditAction.LOGIN_FAILED, "user", user.id,
                ip_address=ip_address
            )
            raise ValueError("Account is deactivated")

        if not verify_password(data.password, user.password_hash):
            brute_force_protection.record_failure(data.email)
            self._log_action(
                user.id, AuditAction.LOGIN_FAILED, "user", user.id,
                ip_address=ip_address
            )
            raise ValueError("Invalid credentials")

        # Reset failed attempts on successful login
        brute_force_protection.reset(data.email)

        # Create session
        access_token = generate_token()
        refresh_token = generate_token()

        session = UserSession(
            id=uuid4(),
            user_id=user.id,
            token_hash=hash_token(access_token),
            refresh_token_hash=hash_token(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        self.db.add(session)

        # Update user last login
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        self.db.commit()

        self._log_action(user.id, AuditAction.LOGIN, "session", session.id, ip_address=ip_address)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_minutes * 60,
            user=UserResponse.model_validate(user),
        )

    def refresh_token(
        self, refresh_token: str, ip_address: str | None = None, user_agent: str | None = None
    ) -> RefreshResponse:
        """Refresh access token."""
        token_hash = hash_token(refresh_token)

        session = (
            self.db.query(UserSession)
            .filter(
                UserSession.refresh_token_hash == token_hash,
                UserSession.is_revoked.is_(False),
                UserSession.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not session:
            raise ValueError("Invalid or expired refresh token")

        user = self.db.query(User).filter(User.id == session.user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")

        # Generate new tokens
        new_access_token = generate_token()
        new_refresh_token = generate_token()

        # Update session
        session.token_hash = hash_token(new_access_token)
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.last_used_at = datetime.utcnow()

        # Log audit
        self._log_action(
            session.user_id, AuditAction.TOKEN_REFRESH, "session", session.id, ip_address=ip_address
        )

        self.db.commit()

        return RefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_minutes * 60,
        )

    def logout(self, user_id: UUID, token: str) -> None:
        """Logout user by revoking session."""
        token_hash = hash_token(token)

        session = (
            self.db.query(UserSession)
            .filter(
                UserSession.token_hash == token_hash,
                UserSession.is_revoked.is_(False),
            )
            .first()
        )

        if session:
            session.is_revoked = True
            self.db.commit()

        self._log_action(user_id, AuditAction.LOGOUT, "session", session.id if session else None)

    def logout_all_sessions(self, user_id: UUID) -> None:
        """Revoke all sessions for a user."""
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).update({"is_revoked": True})
        self.db.commit()

        self._log_action(user_id, AuditAction.LOGOUT, "user", user_id)

    def request_password_reset(self, email: str) -> str:
        """Request password reset."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if user exists or not
            return "If the email exists, a reset link will be sent"

        # Generate reset token
        reset_token = generate_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        self.db.commit()

        self._log_action(user.id, AuditAction.PASSWORD_RESET, "user", user.id)

        # In production, send email with reset link
        return reset_token

    def confirm_password_reset(self, token: str, new_password: str) -> None:
        """Confirm password reset."""
        user = (
            self.db.query(User)
            .filter(
                User.reset_token == token,
                User.reset_token_expires > datetime.utcnow(),
            )
            .first()
        )

        if not user:
            raise ValueError("Invalid or expired reset token")

        # Validate password
        is_valid, violations = self._validate_password(new_password)
        if not is_valid:
            raise ValueError(f"Password does not meet requirements: {violations}")

        # Update password
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        self.db.commit()

        # Revoke all sessions
        self.db.query(UserSession).filter(
            UserSession.user_id == user.id
        ).update({"is_revoked": True})
        self.db.commit()

        self._log_action(user.id, AuditAction.PASSWORD_CHANGED, "user", user.id)

    def change_password(self, user_id: UUID, data: ChangePasswordRequest) -> None:
        """Change user password."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if not verify_password(data.current_password, user.password_hash):
            raise ValueError("Invalid current password")

        # Validate new password
        is_valid, violations = self._validate_password(data.new_password)
        if not is_valid:
            raise ValueError(f"Password does not meet requirements: {violations}")

        user.password_hash = hash_password(data.new_password)
        self.db.commit()

        self._log_action(user_id, AuditAction.PASSWORD_CHANGED, "user", user_id)

    def verify_email(self, user_id: UUID) -> None:
        """Verify user email."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user.is_verified = True
        self.db.commit()

        self._log_action(user_id, AuditAction.USER_UPDATED, "user", user_id)

    def _validate_password(self, password: str) -> tuple[bool, list[str]]:
        """Validate password meets requirements."""
        violations = []

        if len(password) < settings.password_min_length:
            violations.append(f"minimum_length<{settings.password_min_length}")

        if settings.password_require_uppercase and not any(c.isupper() for c in password):
            violations.append("missing_uppercase")

        if settings.password_require_lowercase and not any(c.islower() for c in password):
            violations.append("missing_lowercase")

        if settings.password_require_digit and not any(c.isdigit() for c in password):
            violations.append("missing_digit")

        if settings.password_require_special and not any(
            (not c.isalnum()) and (not c.isspace()) for c in password
        ):
            violations.append("missing_special_char")

        return len(violations) == 0, violations

    def _log_action(
        self,
        user_id: UUID | None,
        action: AuditAction,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log an audit action."""
        from app.services.audit_log_service import append_audit_event

        append_audit_event(
            action.value,
            {
                "user_id": str(user_id) if user_id else None,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "details": details,
                "ip_address": ip_address,
            },
        )