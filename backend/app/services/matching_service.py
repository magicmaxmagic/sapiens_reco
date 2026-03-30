from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


def _structured_score(mission: Mission, profile: Profile) -> tuple[float, list[str]]:
    score = 0.0
    tags: list[str] = []

    checks = 0
    if mission.required_language:
        checks += 1
        profile_languages = [_normalize(lang) for lang in profile.parsed_languages]
        if _normalize(mission.required_language) in profile_languages:
            score += 1
            tags.append("language_match")

    if mission.required_location:
        checks += 1
        location = _normalize(profile.parsed_location)
        required_location = _normalize(mission.required_location)
        if required_location in location or location in required_location:
            score += 1
            tags.append("location_match")

    if mission.required_seniority:
        checks += 1
        required = SENIORITY_ORDER.get(_normalize(mission.required_seniority), 0)
        candidate = SENIORITY_ORDER.get(_normalize(profile.parsed_seniority), 0)
        if candidate >= required > 0:
            score += 1
            tags.append("seniority_match")

    checks += 1
    if _normalize(profile.availability_status) in {"available", "soon", "open"}:
        score += 1
        tags.append("availability_match")

    if checks == 0:
        return 100.0, ["no_structured_constraints"]

    return (score / checks) * 100, tags


def _semantic_score(mission: Mission, profile: Profile) -> float:
    mission_text = " ".join(
        [mission.title, mission.description, " ".join(mission.required_skills)]
    ).strip()
    profile_text = " ".join(
        [
            profile.raw_text or "",
            " ".join(profile.parsed_skills),
            profile.full_name,
        ]
    ).strip()

    if not mission_text or not profile_text:
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([mission_text, profile_text])
    similarity = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return max(0.0, min(100.0, similarity * 100.0))


def _business_score(mission: Mission, profile: Profile) -> tuple[float, list[str]]:
    required_skills = {_normalize(skill) for skill in mission.required_skills}
    candidate_skills = {_normalize(skill) for skill in profile.parsed_skills}

    if not required_skills:
        return 50.0, ["no_required_skills"]

    overlap = required_skills & candidate_skills
    overlap_ratio = len(overlap) / len(required_skills)

    tags = [f"skill:{skill}" for skill in sorted(overlap)]
    freshness_bonus = 15.0 if _normalize(profile.source) == "upload" else 5.0

    score = (overlap_ratio * 85.0) + freshness_bonus
    return max(0.0, min(100.0, score)), tags


def score_profile_for_mission(mission: Mission, profile: Profile) -> dict[str, object]:
    structured, structured_tags = _structured_score(mission, profile)
    semantic = _semantic_score(mission, profile)
    business, business_tags = _business_score(mission, profile)

    final_score = (0.4 * structured) + (0.4 * semantic) + (0.2 * business)
    tags = sorted(set([*structured_tags, *business_tags]))

    return {
        "structured_score": round(structured, 2),
        "semantic_score": round(semantic, 2),
        "business_score": round(business, 2),
        "final_score": round(final_score, 2),
        "explanation_tags": tags,
    }
