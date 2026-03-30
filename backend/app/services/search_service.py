from __future__ import annotations

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.profile import Profile


def search_profiles(
    db: Session,
    q: str | None = None,
    language: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    availability: str | None = None,
    skill: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[Profile]]:
    query = db.query(Profile)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Profile.full_name.ilike(pattern),
                Profile.raw_text.ilike(pattern),
            )
        )

    if language:
        query = query.filter(cast(Profile.parsed_languages, String).ilike(f"%{language}%"))

    if location:
        query = query.filter(Profile.parsed_location.ilike(f"%{location}%"))

    if seniority:
        query = query.filter(Profile.parsed_seniority.ilike(f"%{seniority}%"))

    if availability:
        query = query.filter(Profile.availability_status.ilike(f"%{availability}%"))

    if skill:
        query = query.filter(cast(Profile.parsed_skills, String).ilike(f"%{skill}%"))

    total = query.count()
    items = (
        query.order_by(Profile.created_at.desc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 200))
        .all()
    )
    return total, items
