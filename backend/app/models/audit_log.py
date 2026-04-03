"""Audit log model for tracking user actions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditAction(str, Enum):
    """Audit action types."""

    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGED = "password_changed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    PROFILE_DELETED = "profile_deleted"
    PROFILE_UPLOADED = "profile_uploaded"
    MISSION_CREATED = "mission_created"
    MISSION_UPDATED = "mission_updated"
    MISSION_DELETED = "mission_deleted"
    MISSION_MATCHED = "mission_matched"
    DATA_EXPORTED = "data_exported"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SECURITY_EVENT = "security_event"


class AuditLog(Base, TimestampMixin):
    """Audit log for tracking user actions."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction), nullable=False, index=True
    )
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationship
    user: Mapped[User | None] = relationship("User", backref="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} by {self.user_id}>"