from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.experience import Experience
    from app.models.match_result import MatchResult


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    parsed_languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    parsed_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    availability_status: Mapped[str] = mapped_column(String(100), default="unknown", nullable=False)
    source: Mapped[str] = mapped_column(String(255), default="upload", nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    updated_by: Mapped[UUID | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    experiences: Mapped[list[Experience]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    matches: Mapped[list[MatchResult]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
