import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import AuthContext, require_admin_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.input_security_service import (
    sanitize_label,
    sanitize_string_list,
    strip_prompt_injection_content,
)
from app.services.parsing_service import parse_profile_document
from app.services.search_service import search_profiles

router = APIRouter(prefix="/profiles", tags=["profiles"])
settings = get_settings()
security_logger = logging.getLogger("optimus.security")

ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/octet-stream",
}


def _sanitize_profile_updates(updates: dict[str, object]) -> dict[str, object]:
    cleaned = dict(updates)

    if "full_name" in cleaned and isinstance(cleaned["full_name"], str):
        cleaned["full_name"] = sanitize_label(cleaned["full_name"], max_length=255)

    if "parsed_skills" in cleaned and isinstance(cleaned["parsed_skills"], list):
        cleaned["parsed_skills"] = sanitize_string_list(cleaned["parsed_skills"], max_items=40)

    if "parsed_languages" in cleaned and isinstance(cleaned["parsed_languages"], list):
        cleaned["parsed_languages"] = sanitize_string_list(
            cleaned["parsed_languages"],
            max_items=10,
        )

    if "parsed_location" in cleaned and isinstance(cleaned["parsed_location"], str):
        cleaned["parsed_location"] = sanitize_label(cleaned["parsed_location"], max_length=255)

    if "parsed_seniority" in cleaned and isinstance(cleaned["parsed_seniority"], str):
        cleaned["parsed_seniority"] = sanitize_label(cleaned["parsed_seniority"], max_length=100)

    if "availability_status" in cleaned and isinstance(cleaned["availability_status"], str):
        cleaned["availability_status"] = sanitize_label(
            cleaned["availability_status"],
            max_length=100,
        )

    if "raw_text" in cleaned and isinstance(cleaned["raw_text"], str):
        safe_text, flags = strip_prompt_injection_content(cleaned["raw_text"])
        cleaned["raw_text"] = safe_text
        if flags:
            security_logger.warning("prompt_signals_in_profile_update flags=%s", ",".join(flags))
            if settings.block_prompt_injection:
                raise HTTPException(
                    status_code=422,
                    detail="Prompt-injection patterns detected in raw_text",
                )

    return cleaned


@router.post("/upload", response_model=ProfileRead)
async def upload_profile(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> Profile:
    safe_filename = Path(file.filename or "unknown.txt").name
    extension = Path(safe_filename).suffix.lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{extension}'. Allowed: pdf, docx, txt",
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported content type")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds max allowed size")

    try:
        parsed = parse_profile_document(safe_filename, content)
    except Exception as exc:  # pragma: no cover - defensive parsing barrier
        raise HTTPException(status_code=400, detail="Failed to parse document") from exc

    flags = parsed.get("security_flags", [])
    if flags:
        security_logger.warning(
            "prompt_signals_in_uploaded_profile filename=%s flags=%s",
            safe_filename,
            ",".join(flags),
        )
        if settings.block_prompt_injection:
            raise HTTPException(
                status_code=422,
                detail="Prompt-injection patterns detected in uploaded content",
            )

    profile = Profile(
        full_name=str(parsed["full_name"]),
        raw_text=str(parsed["raw_text"]),
        parsed_skills=list(parsed["parsed_skills"]),
        parsed_languages=list(parsed["parsed_languages"]),
        parsed_location=parsed["parsed_location"],
        parsed_seniority=parsed["parsed_seniority"],
        availability_status="unknown",
        source="upload",
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("", response_model=list[ProfileRead])
def list_profiles(
    q: str | None = None,
    language: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    availability: str | None = None,
    skill: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[Profile]:
    safe_q = sanitize_label(q, max_length=128) if q else None
    safe_language = sanitize_label(language, max_length=32) if language else None
    safe_location = sanitize_label(location, max_length=128) if location else None
    safe_seniority = sanitize_label(seniority, max_length=64) if seniority else None
    safe_availability = sanitize_label(availability, max_length=64) if availability else None
    safe_skill = sanitize_label(skill, max_length=64) if skill else None

    _, items = search_profiles(
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
    return items


@router.get("/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: int, db: Session = Depends(get_db)) -> Profile:
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/{profile_id}", response_model=ProfileRead)
def update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> Profile:
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    updates = _sanitize_profile_updates(payload.model_dump(exclude_unset=True))
    for field, value in updates.items():
        setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/{profile_id}/manual-correction", response_model=ProfileRead)
def manual_profile_correction(
    profile_id: int,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> Profile:
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    updates = _sanitize_profile_updates(payload.model_dump(exclude_unset=True))
    for field, value in updates.items():
        setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
