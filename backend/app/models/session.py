"""Session model for refresh tokens."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Session(Base, TimestampMixin):
    """User session for refresh tokens."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA256 of access token
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # SHA256 of refresh token
    refresh_token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_revoked: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationship
    user: Mapped[User] = relationship("User", backref="sessions")

    def __repr__(self) -> str:
        return f"<Session {self.id} for user {self.user_id}>"