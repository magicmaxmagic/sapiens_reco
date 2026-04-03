"""Match result model for storing matching scores."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.mission import Mission
    from app.models.profile import Profile


class MatchResult(Base, TimestampMixin):
    """Match result between a profile and a mission."""

    __tablename__ = "match_results"
    __table_args__ = (
        UniqueConstraint("mission_id", "profile_id", name="uq_mission_profile"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    mission_id: Mapped[int] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    structured_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    business_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    explanation_tags: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Feedback fields - accepted, rejected, maybe
    feedback: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    feedback_at: Mapped[datetime | None] = mapped_column(nullable=True)

    mission: Mapped[Mission] = relationship(back_populates="matches")
    profile: Mapped[Profile] = relationship(back_populates="matches")