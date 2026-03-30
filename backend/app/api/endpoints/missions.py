import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthContext, require_admin_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.mission import Mission
from app.schemas.mission import MissionCreate, MissionRead, MissionUpdate
from app.services.input_security_service import (
    normalize_untrusted_text,
    sanitize_label,
    sanitize_string_list,
    strip_prompt_injection_content,
)

router = APIRouter(prefix="/missions", tags=["missions"])
settings = get_settings()
security_logger = logging.getLogger("optimus.security")


def _sanitize_mission_payload(payload: dict[str, object]) -> dict[str, object]:
    cleaned = dict(payload)

    if "title" in cleaned and isinstance(cleaned["title"], str):
        cleaned["title"] = sanitize_label(cleaned["title"], max_length=255)

    if "description" in cleaned and isinstance(cleaned["description"], str):
        normalized = normalize_untrusted_text(cleaned["description"], max_length=20_000)
        safe_description, flags = strip_prompt_injection_content(normalized)
        cleaned["description"] = safe_description
        if flags:
            security_logger.warning(
                "prompt_signals_in_mission_description flags=%s",
                ",".join(flags),
            )
            if settings.block_prompt_injection:
                raise HTTPException(
                    status_code=422,
                    detail="Prompt-injection patterns detected in mission description",
                )

    if "required_skills" in cleaned and isinstance(cleaned["required_skills"], list):
        cleaned["required_skills"] = sanitize_string_list(cleaned["required_skills"], max_items=40)

    for field_name, max_len in {
        "required_language": 64,
        "required_location": 255,
        "required_seniority": 64,
    }.items():
        if field_name in cleaned and isinstance(cleaned[field_name], str):
            cleaned[field_name] = sanitize_label(cleaned[field_name], max_length=max_len)

    return cleaned


@router.post("", response_model=MissionRead)
def create_mission(
    payload: MissionCreate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> Mission:
    mission = Mission(**_sanitize_mission_payload(payload.model_dump()))
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


@router.get("", response_model=list[MissionRead])
def list_missions(db: Session = Depends(get_db)) -> list[Mission]:
    return db.query(Mission).order_by(Mission.created_at.desc()).all()


@router.get("/{mission_id}", response_model=MissionRead)
def get_mission(mission_id: int, db: Session = Depends(get_db)) -> Mission:
    mission = db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.patch("/{mission_id}", response_model=MissionRead)
def update_mission(
    mission_id: int,
    payload: MissionUpdate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> Mission:
    mission = db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    updates = _sanitize_mission_payload(payload.model_dump(exclude_unset=True))
    for field, value in updates.items():
        setattr(mission, field, value)

    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission
