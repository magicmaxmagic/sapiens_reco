from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.profile import ProfileRead
from app.services.input_security_service import sanitize_label
from app.services.search_service import search_profiles

router = APIRouter(prefix="/search", tags=["search"])

MAX_SKILLS_FILTER = 12


def _parse_skill_values(raw: str | None) -> list[str]:
    if not raw:
        return []
    values: list[str] = []
    for token in raw.split(","):
        cleaned = sanitize_label(token, max_length=64)
        if cleaned and cleaned not in values:
            values.append(cleaned)
        if len(values) >= MAX_SKILLS_FILTER:
            break
    return values


def _safe_skill_mode(value: str | None) -> str:
    if (value or "").lower() == "all":
        return "all"
    return "any"


def _safe_sort_by(value: str | None) -> str:
    normalized = (value or "date").strip().lower()
    aliases = {
        "pertinence": "relevance",
        "relevance": "relevance",
        "date": "date",
        "seniority": "seniority",
        "seniorite": "seniority",
    }
    return aliases.get(normalized, "date")


@router.get("/profiles")
def search_profiles_endpoint(
    q: str | None = None,
    language: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    availability: str | None = None,
    skill: str | None = None,
    skills: str | None = None,
    skill_mode: str = "any",
    sort_by: str = "date",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    safe_q = sanitize_label(q, max_length=128) if q else None
    safe_language = sanitize_label(language, max_length=32) if language else None
    safe_location = sanitize_label(location, max_length=128) if location else None
    safe_seniority = sanitize_label(seniority, max_length=64) if seniority else None
    safe_availability = sanitize_label(availability, max_length=64) if availability else None
    safe_skill = sanitize_label(skill, max_length=64) if skill else None
    safe_skills = _parse_skill_values(skills)
    if safe_skill and safe_skill not in safe_skills:
        safe_skills.append(safe_skill)

    safe_skill_mode = _safe_skill_mode(skill_mode)
    safe_sort = _safe_sort_by(sort_by)

    total, items = search_profiles(
        db=db,
        q=safe_q,
        language=safe_language,
        location=safe_location,
        seniority=safe_seniority,
        availability=safe_availability,
        skill=safe_skill,
        skills=safe_skills,
        skill_mode=safe_skill_mode,
        sort_by=safe_sort,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "items": [ProfileRead.model_validate(item).model_dump() for item in items],
    }
