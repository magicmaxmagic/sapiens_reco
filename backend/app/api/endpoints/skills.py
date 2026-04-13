
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthContext, require_admin_user
from app.core.database import get_db
from app.models.skill_taxonomy import SkillTaxonomy
from app.schemas.skill_taxonomy import (
    SkillTaxonomyCreate,
    SkillTaxonomyRead,
    SkillTaxonomyUpdate,
)
from app.services.input_security_service import sanitize_label, sanitize_string_list

router = APIRouter(prefix="/skills", tags=["skills"])


def _sanitize_skill_data(data: dict) -> dict:
    """Sanitize skill taxonomy data."""
    cleaned = dict(data)
    if "name" in cleaned and isinstance(cleaned["name"], str):
        cleaned["name"] = sanitize_label(cleaned["name"], max_length=255)
    if "category" in cleaned and isinstance(cleaned["category"], str):
        cleaned["category"] = sanitize_label(cleaned["category"], max_length=100)
    if "synonyms" in cleaned and isinstance(cleaned["synonyms"], list):
        cleaned["synonyms"] = sanitize_string_list(cleaned["synonyms"], max_items=50)
    return cleaned


@router.get("", response_model=list[SkillTaxonomyRead])
def list_skills(
    category: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[SkillTaxonomy]:
    """List all skills with optional filtering."""
    query = db.query(SkillTaxonomy)

    if category:
        query = query.filter(SkillTaxonomy.category == category)
    if q:
        q = q.lower()
        query = query.filter(
            (SkillTaxonomy.name.ilike(f"%{q}%"))
            | (SkillTaxonomy.category.ilike(f"%{q}%"))
        )

    return query.offset(offset).limit(limit).all()


@router.get("/{skill_id}", response_model=SkillTaxonomyRead)
def get_skill(skill_id: int, db: Session = Depends(get_db)) -> SkillTaxonomy:
    """Get a specific skill by ID."""
    skill = db.get(SkillTaxonomy, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("", response_model=SkillTaxonomyRead, status_code=201)
def create_skill(
    payload: SkillTaxonomyCreate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> SkillTaxonomy:
    """Create a new skill taxonomy entry."""
    existing = db.query(SkillTaxonomy).filter(SkillTaxonomy.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Skill with this name already exists")

    data = _sanitize_skill_data(payload.model_dump())
    skill = SkillTaxonomy(**data)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/{skill_id}", response_model=SkillTaxonomyRead)
def update_skill(
    skill_id: int,
    payload: SkillTaxonomyUpdate,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> SkillTaxonomy:
    """Update an existing skill taxonomy entry."""
    skill = db.get(SkillTaxonomy, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    data = _sanitize_skill_data(payload.model_dump(exclude_unset=True))

    # Check for duplicate name
    if "name" in data:
        existing = (
            db.query(SkillTaxonomy)
            .filter(SkillTaxonomy.name == data["name"])
            .filter(SkillTaxonomy.id != skill_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Skill with this name already exists")

    for field, value in data.items():
        setattr(skill, field, value)

    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=204)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> None:
    """Delete a skill taxonomy entry."""
    skill = db.get(SkillTaxonomy, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    db.delete(skill)
    db.commit()
