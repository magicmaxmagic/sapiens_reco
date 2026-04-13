from __future__ import annotations

from app.models.mission import Mission
from app.models.profile import Profile

SENIORITY_ORDER = {
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
}


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def calculate_skills_match(required_skills: list[str], profile_skills: list[str]) -> float:
    """Calculate skills match score.
    
    skills_match = intersection(required_skills, profile_skills) / len(required_skills)
    """
    if not required_skills:
        return 0.0
    
    required_normalized = {_normalize(s) for s in required_skills}
    profile_normalized = {_normalize(s) for s in profile_skills}
    
    overlap = required_normalized & profile_normalized
    return len(overlap) / len(required_normalized)


def calculate_seniority_match(
    required_seniority: str | None, profile_seniority: str | None
) -> float:
    """Calculate seniority match score.
    
    seniority_match = 1.0 if compatible, 0.0 otherwise
    A profile is compatible if its level >= required level.
    """
    if not required_seniority:
        return 1.0
    
    required = SENIORITY_ORDER.get(_normalize(required_seniority), 0)
    if required == 0:
        return 1.0
    
    profile_level = SENIORITY_ORDER.get(_normalize(profile_seniority), 0)
    return 1.0 if profile_level >= required else 0.0


def calculate_location_match(
    required_location: str | None, profile_location: str | None
) -> float:
    """Calculate location match score.
    
    location_match = 1.0 if same location, 0.5 if fuzzy, 0.0 otherwise
    """
    if not required_location:
        return 1.0
    
    required = _normalize(required_location)
    profile = _normalize(profile_location or "")
    
    if not profile:
        return 0.0
    
    # Exact match
    if required == profile:
        return 1.0
    
    # Fuzzy match (one contains the other)
    if required in profile or profile in required:
        return 0.5
    
    return 0.0


def score_profile_for_mission(mission: Mission, profile: Profile) -> dict[str, float]:
    """Calculate simple matching score for a profile against a mission.
    
    Score formula:
    - 60% skills_match
    - 30% seniority_match
    - 10% location_match
    """
    skills_match = calculate_skills_match(mission.required_skills, profile.parsed_skills)
    seniority_match = calculate_seniority_match(
        mission.required_seniority, profile.parsed_seniority
    )
    location_match = calculate_location_match(
        mission.required_location, profile.parsed_location
    )
    
    final_score = (
        0.6 * skills_match
        + 0.3 * seniority_match
        + 0.1 * location_match
    )
    
    return {
        "skills_match": round(skills_match, 4),
        "seniority_match": round(seniority_match, 4),
        "location_match": round(location_match, 4),
        "final_score": round(final_score, 4),
    }
