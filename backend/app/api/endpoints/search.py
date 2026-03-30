from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.profile import ProfileRead
from app.services.input_security_service import sanitize_label
from app.services.search_service import search_profiles

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/profiles")
def search_profiles_endpoint(
    q: str | None = None,
    language: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    availability: str | None = None,
    skill: str | None = None,
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

    total, items = search_profiles(
        db=db,
        q=safe_q,
        language=safe_language,
        location=safe_location,
        seniority=safe_seniority,
        availability=safe_availability,
        skill=safe_skill,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "items": [ProfileRead.model_validate(item).model_dump() for item in items],
    }
