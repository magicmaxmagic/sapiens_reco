from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.mission import Mission
    from app.models.profile import Profile


class MatchResult(Base, TimestampMixin):
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
    explanation_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    mission: Mapped[Mission] = relationship(back_populates="matches")
    profile: Mapped[Profile] = relationship(back_populates="matches")
