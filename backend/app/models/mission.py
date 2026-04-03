from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.match_result import MatchResult


class Mission(Base, TimestampMixin):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    required_language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    required_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    required_seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    desired_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    matches: Mapped[list[MatchResult]] = relationship(
        back_populates="mission", cascade="all, delete-orphan"
    )
