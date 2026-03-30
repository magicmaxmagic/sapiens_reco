from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthContext, require_admin_user
from app.core.database import get_db
from app.models.match_result import MatchResult
from app.models.mission import Mission
from app.models.profile import Profile
from app.schemas.match import MatchResultRead
from app.services.matching_service import score_profile_for_mission

router = APIRouter(prefix="/missions", tags=["matching"])


@router.post("/{mission_id}/match", response_model=list[MatchResultRead])
def run_matching(
    mission_id: int,
    top_n: int = 10,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_admin_user),
) -> list[MatchResult]:
    mission = db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    profiles = db.query(Profile).all()
    if not profiles:
        return []

    db.query(MatchResult).filter(MatchResult.mission_id == mission_id).delete()

    for profile in profiles:
        score = score_profile_for_mission(mission, profile)
        row = MatchResult(
            mission_id=mission_id,
            profile_id=profile.id,
            structured_score=float(score["structured_score"]),
            semantic_score=float(score["semantic_score"]),
            business_score=float(score["business_score"]),
            final_score=float(score["final_score"]),
            explanation_tags=list(score["explanation_tags"]),
        )
        db.add(row)

    db.commit()

    return (
        db.query(MatchResult)
        .filter(MatchResult.mission_id == mission_id)
        .order_by(MatchResult.final_score.desc())
        .limit(min(max(top_n, 1), 50))
        .all()
    )


@router.get("/{mission_id}/matches", response_model=list[MatchResultRead])
def list_matches(mission_id: int, db: Session = Depends(get_db)) -> list[MatchResult]:
    mission = db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    return (
        db.query(MatchResult)
        .filter(MatchResult.mission_id == mission_id)
        .order_by(MatchResult.final_score.desc())
        .all()
    )
