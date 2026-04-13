"""
Two-Tower Matching Service for Profile-Mission Matching.

This module implements a two-tower architecture:
- Profile Tower: Encodes skills, seniority, location into a vector
- Mission Tower: Encodes requirements into a vector
- Matching: Cosine similarity between vectors
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import TYPE_CHECKING

from app.models.mission import Mission
from app.models.profile import Profile

if TYPE_CHECKING:
    pass


# === ENCODING CONSTANTS ===

# All possible skills (will be built dynamically)
SKILL_VOCAB: dict[str, int] = {}
SKILL_VOCAB_BUILT = False

# Seniority encoding (ordinal)
SENIORITY_ORDER = {
    "junior": 0.25,
    "mid": 0.50,
    "senior": 0.75,
    "lead": 1.00,
}

# Location encoding (normalized)
LOCATION_VOCAB: dict[str, int] = {}
LOCATION_VOCAB_BUILT = False


def _normalize(value: str | None) -> str:
    """Normalize a string value."""
    return (value or "").strip().lower()


def _build_skill_vocabulary(profiles: list[Profile], missions: list[Mission]) -> None:
    """Build skill vocabulary from all profiles and missions."""
    global SKILL_VOCAB, SKILL_VOCAB_BUILT
    
    if SKILL_VOCAB_BUILT:
        return
    
    all_skills: set[str] = set()
    
    # Collect skills from profiles
    for profile in profiles:
        for skill in (profile.parsed_skills or []):
            all_skills.add(_normalize(skill))
    
    # Collect skills from missions
    for mission in missions:
        for skill in (mission.required_skills or []):
            all_skills.add(_normalize(skill))
    
    # Build vocabulary (sorted for consistency)
    sorted_skills = sorted(all_skills)
    SKILL_VOCAB = {skill: idx for idx, skill in enumerate(sorted_skills)}
    SKILL_VOCAB_BUILT = True


def _build_location_vocabulary(profiles: list[Profile], missions: list[Mission]) -> None:
    """Build location vocabulary from all profiles and missions."""
    global LOCATION_VOCAB, LOCATION_VOCAB_BUILT
    
    if LOCATION_VOCAB_BUILT:
        return
    
    all_locations: set[str] = set()
    
    # Collect locations from profiles
    for profile in profiles:
        if profile.parsed_location:
            all_locations.add(_normalize(profile.parsed_location))
    
    # Collect locations from missions
    for mission in missions:
        if mission.required_location:
            all_locations.add(_normalize(mission.required_location))
    
    # Build vocabulary (sorted for consistency)
    sorted_locations = sorted(all_locations)
    LOCATION_VOCAB = {loc: idx for idx, loc in enumerate(sorted_locations)}
    LOCATION_VOCAB_BUILT = True


# === TOWER ENCODERS ===

def encode_skills_one_hot(skills: list[str] | None, vocab: dict[str, int]) -> list[float]:
    """Encode skills as one-hot vector.
    
    Args:
        skills: List of skill strings
        vocab: Skill vocabulary (skill -> index)
    
    Returns:
        One-hot encoded vector (size = len(vocab))
    """
    if not skills or not vocab:
        return [0.0] * max(1, len(vocab))
    
    vector = [0.0] * len(vocab)
    for skill in skills:
        normalized = _normalize(skill)
        if normalized in vocab:
            vector[vocab[normalized]] = 1.0
    
    return vector


def encode_seniority(seniority: str | None) -> float:
    """Encode seniority as normalized float (0-1).
    
    Args:
        seniority: Seniority level string
    
    Returns:
        Normalized seniority value (0.0-1.0)
    """
    if not seniority:
        return 0.5  # Default to mid level
    
    normalized = _normalize(seniority)
    return SENIORITY_ORDER.get(normalized, 0.5)


def encode_location_one_hot(location: str | None, vocab: dict[str, int]) -> list[float]:
    """Encode location as one-hot vector.
    
    Args:
        location: Location string
        vocab: Location vocabulary (location -> index)
    
    Returns:
        One-hot encoded vector (size = len(vocab))
    """
    if not location or not vocab:
        return [0.0] * max(1, len(vocab))
    
    vector = [0.0] * len(vocab)
    normalized = _normalize(location)
    
    if normalized in vocab:
        vector[vocab[normalized]] = 1.0
    
    return vector


def encode_profile_tower(
    profile: Profile,
    skill_vocab: dict[str, int],
    location_vocab: dict[str, int]
) -> list[float]:
    """Encode a profile into a vector using the Profile Tower.
    
    The vector consists of:
    - Skills one-hot encoding (size = len(skill_vocab))
    - Seniority encoding (size = 1)
    - Location one-hot encoding (size = len(location_vocab))
    
    Args:
        profile: Profile to encode
        skill_vocab: Skill vocabulary
        location_vocab: Location vocabulary
    
    Returns:
        Profile vector
    """
    skills_vector = encode_skills_one_hot(profile.parsed_skills, skill_vocab)
    seniority = encode_seniority(profile.parsed_seniority)
    location_vector = encode_location_one_hot(profile.parsed_location, location_vocab)
    
    # Combine into single vector
    return skills_vector + [seniority] + location_vector


def encode_mission_tower(
    mission: Mission,
    skill_vocab: dict[str, int],
    location_vocab: dict[str, int]
) -> list[float]:
    """Encode a mission into a vector using the Mission Tower.
    
    The vector consists of:
    - Required skills one-hot encoding (size = len(skill_vocab))
    - Required seniority encoding (size = 1)
    - Required location one-hot encoding (size = len(location_vocab))
    
    Args:
        mission: Mission to encode
        skill_vocab: Skill vocabulary
        location_vocab: Location vocabulary
    
    Returns:
        Mission vector
    """
    skills_vector = encode_skills_one_hot(mission.required_skills, skill_vocab)
    seniority = encode_seniority(mission.required_seniority)
    location_vector = encode_location_one_hot(mission.required_location, location_vocab)
    
    # Combine into single vector
    return skills_vector + [seniority] + location_vector


# === SIMILARITY FUNCTIONS ===

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Cosine similarity (0.0-1.0)
    """
    if len(vec1) != len(vec2):
        return 0.0
    
    if not vec1 or not vec2:
        return 0.0
    
    # Dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Magnitudes
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


# === MATCHING FUNCTIONS ===

def score_profile_for_mission(mission: Mission, profile: Profile) -> dict[str, float]:
    """Calculate matching score for a profile against a mission using 2-tower.
    
    Uses cosine similarity between profile vector and mission vector.
    
    Args:
        mission: Mission to match against
        profile: Profile to score
    
    Returns:
        Dict with score and component scores
    """
    # Build vocabularies if needed
    _build_skill_vocabulary([profile], [mission])
    _build_location_vocabulary([profile], [mission])
    
    # Encode vectors
    profile_vector = encode_profile_tower(profile, SKILL_VOCAB, LOCATION_VOCAB)
    mission_vector = encode_mission_tower(mission, SKILL_VOCAB, LOCATION_VOCAB)
    
    # Calculate cosine similarity
    score = cosine_similarity(profile_vector, mission_vector)
    
    # Calculate component scores for explainability
    skills_match = 0.0
    if mission.required_skills and profile.parsed_skills:
        required_normalized = {_normalize(s) for s in mission.required_skills}
        profile_normalized = {_normalize(s) for s in profile.parsed_skills}
        overlap = required_normalized & profile_normalized
        skills_match = len(overlap) / len(required_normalized) if required_normalized else 0.0
    
    seniority_match = 0.0
    if mission.required_seniority and profile.parsed_seniority:
        profile_level = SENIORITY_ORDER.get(_normalize(profile.parsed_seniority), 0)
        required_level = SENIORITY_ORDER.get(_normalize(mission.required_seniority), 0)
        seniority_match = 1.0 if profile_level >= required_level else 0.0
    elif not mission.required_seniority:
        seniority_match = 1.0
    
    location_match = 0.0
    if mission.required_location and profile.parsed_location:
        location_match = 1.0 if _normalize(mission.required_location) == _normalize(profile.parsed_location) else 0.0
    elif not mission.required_location:
        location_match = 1.0
    
    return {
        "score": round(score, 3),
        "skills_match": round(skills_match, 3),
        "seniority_match": round(seniority_match, 3),
        "location_match": round(location_match, 3),
    }


def rank_profiles_for_mission(
    mission: Mission,
    profiles: list[Profile],
    top_k: int = 10
) -> list[dict]:
    """Rank profiles for a mission using 2-tower matching.
    
    Args:
        mission: Mission to match against
        profiles: List of profiles to rank
        top_k: Number of top candidates to return
    
    Returns:
        List of ranked candidates with scores
    """
    # Build vocabularies from all profiles and missions
    _build_skill_vocabulary(profiles, [mission])
    _build_location_vocabulary(profiles, [mission])
    
    # Encode mission vector once
    mission_vector = encode_mission_tower(mission, SKILL_VOCAB, LOCATION_VOCAB)
    
    # Score all profiles
    results = []
    for profile in profiles:
        profile_vector = encode_profile_tower(profile, SKILL_VOCAB, LOCATION_VOCAB)
        score = cosine_similarity(profile_vector, mission_vector)
        
        # Calculate component scores for explainability
        skills_match = 0.0
        if mission.required_skills and profile.parsed_skills:
            required_normalized = {_normalize(s) for s in mission.required_skills}
            profile_normalized = {_normalize(s) for s in profile.parsed_skills}
            overlap = required_normalized & profile_normalized
            skills_match = len(overlap) / len(required_normalized) if required_normalized else 0.0
        
        seniority_match = 0.0
        if mission.required_seniority and profile.parsed_seniority:
            profile_level = SENIORITY_ORDER.get(_normalize(profile.parsed_seniority), 0)
            required_level = SENIORITY_ORDER.get(_normalize(mission.required_seniority), 0)
            seniority_match = 1.0 if profile_level >= required_level else 0.0
        elif not mission.required_seniority:
            seniority_match = 1.0
        
        location_match = 0.0
        if mission.required_location and profile.parsed_location:
            location_match = 1.0 if _normalize(mission.required_location) == _normalize(profile.parsed_location) else 0.0
        elif not mission.required_location:
            location_match = 1.0
        
        results.append({
            "profile_id": profile.id,
            "profile_name": profile.full_name or f"Profile {profile.id}",
            "score": round(score, 3),
            "skills_match": round(skills_match, 3),
            "seniority_match": round(seniority_match, 3),
            "location_match": round(location_match, 3),
        })
    
    # Sort by score (descending) and return top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


# === LEGACY COMPATIBILITY ===

calculate_skills_match = lambda required, profile: score_profile_for_mission(
    Mission(id=0, required_skills=required), 
    Profile(id=0, parsed_skills=profile)
)["skills_match"]

calculate_seniority_match = lambda required, profile: score_profile_for_mission(
    Mission(id=0, required_seniority=required), 
    Profile(id=0, parsed_seniority=profile)
)["seniority_match"]

calculate_location_match = lambda required, profile: score_profile_for_mission(
    Mission(id=0, required_location=required), 
    Profile(id=0, parsed_location=profile)
)["location_match"]