from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthContext, require_admin_user
from app.core.database import get_db
from app.models.mission import Mission
from app.models.profile import Profile
from app.schemas.match import ShortlistItem
from app.services.matching_service import score_profile_for_mission

router = APIRouter(prefix="/missions", tags=["matching"])

# In-memory storage for shortlists (MVP only)
_shortlists: dict[int, list[ShortlistItem]] = {}


@router.post("/{mission_id}/match", response_model=list[ShortlistItem])
def run_matching(
    mission_id: int,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> list[ShortlistItem]:
    """Run matching for a mission and return sorted shortlist."""
    mission = db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    profiles = (
        db.query(Profile)
        .filter(Profile.is_active.is_(True))
        .all()
    )
    if not profiles:
        return []

    results: list[ShortlistItem] = []
    for profile in profiles:
        score = score_profile_for_mission(mission, profile)
        results.append(
            ShortlistItem(
                profile_id=profile.id,
                profile_name=profile.full_name,
                score=score["final_score"],
                skills_match=score["skills_match"],
                seniority_match=score["seniority_match"],
                location_match=score["location_match"],
            )
        )

    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)

    # Store for GET endpoint
    _shortlists[mission_id] = results

    return results


@router.get("/{mission_id}/shortlist", response_model=list[ShortlistItem])
def get_shortlist(
    mission_id: int,
    db: Session = Depends(get_db),
) -> list[ShortlistItem]:
    """Get the last shortlist generated for a mission."""
    mission = db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    shortlist = _shortlists.get(mission_id, [])
    if not shortlist:
        raise HTTPException(
            status_code=404,
            detail="No shortlist found for this mission. Run POST /missions/{id}/match first.",
        )

    return shortlist
