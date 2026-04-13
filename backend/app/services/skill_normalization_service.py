"""Skill normalization service with fuzzy matching."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rapidfuzz import fuzz

from app.models.skill_taxonomy import SkillTaxonomy

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Threshold for fuzzy matching (0-100)
FUZZY_THRESHOLD = 80


def normalize_skill_name(skill_name: str) -> str:
    """Normalize a skill name by trimming and lowercasing."""
    return skill_name.strip().lower()


def find_matching_skill(
    db: Session,
    skill_name: str,
    threshold: int = FUZZY_THRESHOLD,
) -> tuple[SkillTaxonomy | None, float]:
    """
    Find a matching skill in the taxonomy using fuzzy matching.
    
    Returns:
        Tuple of (matched_skill, similarity_score) or (None, 0) if no match.
    """
    normalized_name = normalize_skill_name(skill_name)
    
    # Get all skills from taxonomy
    all_skills = db.query(SkillTaxonomy).all()
    
    best_match: SkillTaxonomy | None = None
    best_score = 0
    
    for skill in all_skills:
        # Check direct name match
        skill_normalized = normalize_skill_name(skill.name)
        
        # Calculate fuzzy score using multiple methods
        # 1. Simple ratio
        score = fuzz.ratio(normalized_name, skill_normalized)
        
        # 2. Partial ratio (for partial matches)
        partial_score = fuzz.partial_ratio(normalized_name, skill_normalized)
        score = max(score, partial_score)
        
        # 3. Token sort ratio (for reordered words)
        token_score = fuzz.token_sort_ratio(normalized_name, skill_normalized)
        score = max(score, token_score)
        
        # Check synonyms
        for synonym in skill.synonyms:
            synonym_normalized = normalize_skill_name(synonym)
            syn_score = fuzz.ratio(normalized_name, synonym_normalized)
            syn_partial = fuzz.partial_ratio(normalized_name, synonym_normalized)
            syn_token = fuzz.token_sort_ratio(normalized_name, synonym_normalized)
            syn_score = max(syn_score, syn_partial, syn_token)
            score = max(score, syn_score)
        
        if score >= threshold and score > best_score:
            best_score = score
            best_match = skill
    
    return best_match, best_score


def normalize_skills(
    db: Session,
    skills: list[str],
    threshold: int = FUZZY_THRESHOLD,
    create_missing: bool = False,
) -> list[dict]:
    """
    Normalize a list of skills against the taxonomy.
    
    Args:
        db: Database session
        skills: List of raw skill names
        threshold: Fuzzy matching threshold (0-100)
        create_missing: If True, create new taxonomy entries for unmatched skills
    
    Returns:
        List of normalized skill dicts with 'original', 'normalized', 'taxonomy_id', 'score'
    """
    results = []
    
    for skill_name in skills:
        if not skill_name or not skill_name.strip():
            continue
        
        match, score = find_matching_skill(db, skill_name, threshold)
        
        if match:
            results.append({
                "original": skill_name,
                "normalized": match.name,
                "category": match.category,
                "taxonomy_id": match.id,
                "score": score,
            })
        elif create_missing:
            # Create new taxonomy entry
            new_skill = SkillTaxonomy(
                name=normalize_skill_name(skill_name).title(),
                synonyms=[],
            )
            db.add(new_skill)
            db.commit()
            db.refresh(new_skill)
            results.append({
                "original": skill_name,
                "normalized": new_skill.name,
                "category": new_skill.category,
                "taxonomy_id": new_skill.id,
                "score": 100,
            })
        else:
            results.append({
                "original": skill_name,
                "normalized": None,
                "category": None,
                "taxonomy_id": None,
                "score": score,
            })
    
    return results


def get_skill_similarity(skill1: str, skill2: str) -> float:
    """
    Calculate similarity score between two skills.
    
    Returns:
        Similarity score between 0 and 100
    """
    s1 = normalize_skill_name(skill1)
    s2 = normalize_skill_name(skill2)
    
    return max(
        fuzz.ratio(s1, s2),
        fuzz.partial_ratio(s1, s2),
        fuzz.token_sort_ratio(s1, s2),
    )
