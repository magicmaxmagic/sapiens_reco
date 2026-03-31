from __future__ import annotations

from typing import Literal

from sqlalchemy import String, case, cast, func, literal, or_
from sqlalchemy.orm import Session

from app.models.profile import Profile

SkillMode = Literal["any", "all"]
SortBy = Literal["relevance", "date", "seniority"]


def _build_seniority_rank_expr():
    seniority = func.lower(func.coalesce(Profile.parsed_seniority, ""))
    return case(
        (seniority.like("%expert%"), 4),
        (seniority.like("%senior%"), 3),
        (seniority.like("%confirm%"), 2),
        (seniority.like("%intermediate%"), 2),
        (seniority.like("%junior%"), 1),
        else_=0,
    )


def _build_relevance_expr(q: str | None, skills: list[str]):
    skills_text = cast(Profile.parsed_skills, String)
    languages_text = cast(Profile.parsed_languages, String)

    score = literal(0)
    if q:
        pattern = f"%{q}%"
        score = score + case((Profile.full_name.ilike(pattern), 5), else_=0)
        score = score + case((skills_text.ilike(pattern), 4), else_=0)
        score = score + case((languages_text.ilike(pattern), 3), else_=0)
        score = score + case((Profile.parsed_location.ilike(pattern), 2), else_=0)
        score = score + case((Profile.parsed_seniority.ilike(pattern), 2), else_=0)
        score = score + case((Profile.raw_text.ilike(pattern), 1), else_=0)

    for skill in skills:
        skill_pattern = f"%{skill}%"
        score = score + case((skills_text.ilike(skill_pattern), 3), else_=0)

    return score


def search_profiles(
    db: Session,
    q: str | None = None,
    language: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    availability: str | None = None,
    skill: str | None = None,
    skills: list[str] | None = None,
    skill_mode: SkillMode = "any",
    sort_by: SortBy = "date",
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[Profile]]:
    query = db.query(Profile)

    skill_values = [value for value in (skills or []) if value]
    if skill and skill not in skill_values:
        skill_values.append(skill)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Profile.full_name.ilike(pattern),
                Profile.raw_text.ilike(pattern),
            )
        )

    if language:
        query = query.filter(cast(Profile.parsed_languages, String).ilike(f"%{language}%"))

    if location:
        query = query.filter(Profile.parsed_location.ilike(f"%{location}%"))

    if seniority:
        query = query.filter(Profile.parsed_seniority.ilike(f"%{seniority}%"))

    if availability:
        query = query.filter(Profile.availability_status.ilike(f"%{availability}%"))

    if skill_values:
        skills_expr = cast(Profile.parsed_skills, String)
        skill_filters = [skills_expr.ilike(f"%{value}%") for value in skill_values]
        if skill_mode == "all":
            for filter_clause in skill_filters:
                query = query.filter(filter_clause)
        else:
            query = query.filter(or_(*skill_filters))

    total = query.count()

    if sort_by == "seniority":
        seniority_rank = _build_seniority_rank_expr()
        query = query.order_by(seniority_rank.desc(), Profile.created_at.desc())
    elif sort_by == "relevance":
        relevance_score = _build_relevance_expr(q=q, skills=skill_values)
        query = query.order_by(relevance_score.desc(), Profile.created_at.desc())
    else:
        query = query.order_by(Profile.created_at.desc())

    items = query.offset(max(offset, 0)).limit(min(max(limit, 1), 200)).all()
    return total, items
