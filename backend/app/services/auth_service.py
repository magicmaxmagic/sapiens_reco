"""Authentication service for user management."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    brute_force_protection,
    generate_token,
    hash_password,
    hash_token,
    validate_password_strength,
    verify_password,
)
from app.models.audit_log import AuditAction, AuditLog
from app.models.session import Session as UserSession
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PasswordChange,
    PasswordResetConfirm,
    RefreshResponse,
    RegisterRequest,
)
from app.schemas.user import UserCreate, UserUpdate

settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def register(self, data: UserCreate) -> User:
        """Create a new user."""
        # Check if email already exists
        existing = self.db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ValueError("Email already registered")

        # Validate password strength
        is_valid, violations = validate_password_strength(data.password)
        if not is_valid:
            raise ValueError(f"Password too weak: {', '.join(violations)}")

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

        # Log audit
        self._log_action(user.id, AuditAction.USER_CREATED, "user", user.id)

        return user

    def login(self, data: LoginRequest, ip_address: str | None = None, user_agent: str | None = None) -> LoginResponse:
        """Authenticate a user and return tokens."""
        # Check brute force protection
        is_locked, locked_until = brute_force_protection.is_locked(data.email)
        if is_locked and locked_until:
            raise ValueError(f"Account locked until {locked_until.isoformat()}")

        # Find user
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            brute_force_protection.record_failure(data.email)
            raise ValueError("Invalid credentials")

        # Verify password
        if not verify_password(data.password, user.password_hash):
            brute_force_protection.record_failure(data.email)
            self._log_action(user.id, AuditAction.LOGIN_FAILED, "user", user.id, ip_address=ip_address)
            raise ValueError("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is deactivated")

        # Reset brute force protection on successful login
        brute_force_protection.reset(data.email)

        # Create session
        access_token = generate_token(32)
        refresh_token = generate_token(32)
        expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_access_token_minutes * 60)

        session = UserSession(
            id=uuid4(),
            user_id=user.id,
            token_hash=hash_token(access_token),
            refresh_token_hash=hash_token(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self.db.add(session)

        # Update user last login
        user.last_login = datetime.utcnow()
        self.db.commit()

        # Log audit
        self._log_action(user.id, AuditAction.LOGIN, "user", user.id, ip_address=ip_address)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_minutes * 60,
            user_id=user.id,
            role=user.role.value,
        )

    def refresh(self, refresh_token: str, ip_address: str | None = None) -> RefreshResponse:
        """Refresh access token using refresh token."""
        token_hash = hash_token(refresh_token)
        session = self.db.query(UserSession).filter(
            UserSession.refresh_token_hash == token_hash,
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.utcnow(),
        ).first()

        if not session:
            raise ValueError("Invalid or expired refresh token")

        # Generate new tokens
        new_access_token = generate_token(32)
        new_refresh_token = generate_token(32)
        expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_access_token_minutes * 60)

        # Revoke old session and create new one
        session.is_revoked = True
        new_session = UserSession(
            id=uuid4(),
            user_id=session.user_id,
            token_hash=hash_token(new_access_token),
            refresh_token_hash=hash_token(new_refresh_token),
            ip_address=ip_address,
            user_agent=session.user_agent,
            expires_at=expires_at,
        )
        self.db.add(new_session)
        self.db.commit()

        # Log audit
        self._log_action(session.user_id, AuditAction.TOKEN_REFRESH, "session", new_session.id, ip_address=ip_address)

        return RefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_minutes * 60,
        )

    def logout(self, access_token: str) -> bool:
        """Logout user by revoking their session."""
        token_hash = hash_token(access_token)
        session = self.db.query(UserSession).filter(UserSession.token_hash == token_hash).first()

        if session:
            session.is_revoked = True
            self.db.commit()
            self._log_action(session.user_id, AuditAction.LOGOUT, "session", session.id)
            return True

        return False

    def logout_all(self, user_id: UUID) -> int:
        """Logout all sessions for a user."""
        result = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False,
        ).update({"is_revoked": True})
        self.db.commit()
        self._log_action(user_id, AuditAction.LOGOUT, "user", user_id)
        return result

    def change_password(self, user_id: UUID, data: PasswordChange) -> bool:
        """Change user password."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Validate new password strength
        is_valid, violations = validate_password_strength(data.new_password)
        if not is_valid:
            raise ValueError(f"Password too weak: {', '.join(violations)}")

        # Update password
        user.password_hash = hash_password(data.new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()

        # Revoke all sessions
        self.db.query(UserSession).filter(UserSession.user_id == user_id).update({"is_revoked": True})
        self.db.commit()

        self._log_action(user_id, AuditAction.PASSWORD_CHANGED, "user", user_id)

        return True

    def request_password_reset(self, email: str) -> str:
        """Request password reset token."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if email exists
            return "If the email exists, a reset link will be sent"

        # Generate reset token
        reset_token = generate_token(32)
        user.reset_token = hash_token(reset_token)
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        self.db.commit()

        self._log_action(user.id, AuditAction.PASSWORD_RESET, "user", user.id)

        # In a real app, send email here
        return reset_token

    def confirm_password_reset(self, data: PasswordResetConfirm) -> bool:
        """Confirm password reset."""
        token_hash = hash_token(data.token)
        user = self.db.query(User).filter(
            User.reset_token == token_hash,
            User.reset_token_expires > datetime.utcnow(),
        ).first()

        if not user:
            raise ValueError("Invalid or expired reset token")

        # Validate password strength
        is_valid, violations = validate_password_strength(data.new_password)
        if not is_valid:
            raise ValueError(f"Password too weak: {', '.join(violations)}")

        # Update password and clear reset token
        user.password_hash = hash_password(data.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.updated_at = datetime.utcnow()
        self.db.commit()

        # Revoke all sessions
        self.db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_revoked": True})
        self.db.commit()

        self._log_action(user.id, AuditAction.PASSWORD_CHANGED, "user", user.id)

        return True

    def verify_token(self, access_token: str) -> User | None:
        """Verify access token and return user."""
        token_hash = hash_token(access_token)
        session = self.db.query(UserSession).filter(
            UserSession.token_hash == token_hash,
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.utcnow(),
        ).first()

        if not session:
            return None

        # Update session last used
        session.last_used_at = datetime.utcnow()
        self.db.commit()

        return self.db.query(User).filter(User.id == session.user_id).first()

    def _log_action(
        self,
        user_id: UUID | None,
        action: AuditAction,
        resource_type: str | None,
        resource_id: UUID | None,
        ip_address: str | None = None,
    ) -> None:
        """Log an audit action."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()