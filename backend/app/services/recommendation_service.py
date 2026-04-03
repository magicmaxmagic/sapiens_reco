"""
Two-Tower Recommendation Service for Profile-Mission Matching.

This module implements a two-tower architecture for matching profiles to missions:
- Tower 1 (Profile Encoder): Encodes skills, experience, location into embeddings
- Tower 2 (Mission Encoder): Encodes requirements into embeddings

The towers support both:
- Structured matching (TF-IDF based)
- Semantic matching (embedding-based)

Cosine similarity is used to compute matching scores between profile and mission embeddings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if TYPE_CHECKING:
    from app.models.mission import Mission
    from app.models.profile import Profile


# Weight configuration for different embedding components
PROFILE_WEIGHTS = {
    "skills": 0.4,
    "location": 0.15,
    "seniority": 0.15,
    "languages": 0.1,
    "availability": 0.1,
    "raw_text": 0.1,
}

MISSION_WEIGHTS = {
    "skills": 0.5,
    "location": 0.15,
    "seniority": 0.15,
    "language": 0.1,
    "description": 0.1,
}

SENIORITY_ORDER = {
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
}

# Predefined skill embeddings for common skills (simplified semantic matching)
SKILL_EMBEDDINGS: dict[str, list[float]] = {
    # Backend
    "python": [1.0, 0.8, 0.3, 0.1, 0.0, 0.0],
    "django": [0.9, 0.7, 0.2, 0.1, 0.0, 0.0],
    "fastapi": [0.95, 0.85, 0.25, 0.1, 0.0, 0.0],
    "flask": [0.85, 0.65, 0.2, 0.1, 0.0, 0.0],
    # Data
    "sql": [0.3, 0.4, 0.9, 0.2, 0.0, 0.0],
    "postgresql": [0.3, 0.45, 0.95, 0.2, 0.0, 0.0],
    "pandas": [0.2, 0.3, 0.85, 0.3, 0.0, 0.0],
    "numpy": [0.2, 0.3, 0.9, 0.3, 0.0, 0.0],
    # ML/AI
    "tensorflow": [0.1, 0.2, 0.8, 0.5, 0.0, 0.0],
    "scikit-learn": [0.15, 0.25, 0.85, 0.45, 0.0, 0.0],
    # Frontend
    "react": [0.0, 0.0, 0.1, 0.2, 0.9, 0.0],
    "typescript": [0.1, 0.1, 0.15, 0.2, 0.85, 0.0],
    "next.js": [0.0, 0.05, 0.1, 0.2, 0.92, 0.0],
    # DevOps
    "docker": [0.0, 0.0, 0.0, 0.3, 0.0, 0.9],
    "kubernetes": [0.0, 0.0, 0.0, 0.35, 0.0, 0.95],
    "aws": [0.0, 0.0, 0.0, 0.4, 0.0, 0.88],
    "terraform": [0.0, 0.0, 0.0, 0.35, 0.0, 0.92],
}


@dataclass
class ProfileEmbedding:
    """Embedding vector for a profile with metadata."""

    vector: np.ndarray
    skills_vector: np.ndarray
    location_vector: np.ndarray
    seniority_vector: np.ndarray
    languages_vector: np.ndarray
    availability_vector: np.ndarray
    raw_text_embedding: np.ndarray
    metadata: dict


@dataclass
class MissionEmbedding:
    """Embedding vector for a mission with metadata."""

    vector: np.ndarray
    skills_vector: np.ndarray
    location_vector: np.ndarray
    seniority_vector: np.ndarray
    language_vector: np.ndarray
    description_embedding: np.ndarray
    metadata: dict


class ProfileEncoder:
    """Tower 1: Encodes profiles into embedding vectors."""

    def __init__(self) -> None:
        self._tfidf = TfidfVectorizer(stop_words="english")
        self._embedding_dim = 6  # Dimension of our skill embeddings

    def encode_skills(self, skills: list[str]) -> np.ndarray:
        """Encode skills into a normalized embedding vector."""
        if not skills:
            return np.zeros(self._embedding_dim)

        # Collect embeddings for known skills
        skill_vectors = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in SKILL_EMBEDDINGS:
                skill_vectors.append(np.array(SKILL_EMBEDDINGS[skill_lower]))

        if not skill_vectors:
            # Fallback: create a random but deterministic embedding based on skill names
            combined = " ".join(sorted(skills))
            hash_val = hash(combined)
            np.random.seed(abs(hash_val) % (2**32))
            return np.random.randn(self._embedding_dim)

        # Average the skill vectors
        avg_vector = np.mean(skill_vectors, axis=0)
        # Normalize
        norm = np.linalg.norm(avg_vector)
        return avg_vector / norm if norm > 0 else avg_vector

    def encode_location(self, location: str | None) -> np.ndarray:
        """Encode location into a one-hot style vector."""
        if not location:
            return np.zeros(self._embedding_dim)

        # Simple location encoding - uses position in embedding
        location_lower = location.lower()
        location_idx = abs(hash(location_lower)) % self._embedding_dim
        vec = np.zeros(self._embedding_dim)
        vec[location_idx] = 1.0
        return vec

    def encode_seniority(self, seniority: str | None) -> np.ndarray:
        """Encode seniority into a normalized scalar embedding."""
        if not seniority:
            return np.zeros(self._embedding_dim)

        seniority_lower = seniority.lower()
        level = SENIORITY_ORDER.get(seniority_lower, 0)
        # Normalize to [0, 1] range
        normalized_level = level / max(SENIORITY_ORDER.values())
        vec = np.zeros(self._embedding_dim)
        vec[0] = normalized_level
        return vec

    def encode_languages(self, languages: list[str]) -> np.ndarray:
        """Encode languages into a compact representation."""
        if not languages:
            return np.zeros(self._embedding_dim)

        # Create a compact language representation
        vec = np.zeros(self._embedding_dim)
        for i, lang in enumerate(sorted(set(lang.lower() for lang in languages))):
            if i < self._embedding_dim:
                vec[i] = 1.0
        return vec

    def encode_availability(self, availability: str) -> np.ndarray:
        """Encode availability status."""
        availability_scores = {
            "available": 1.0,
            "soon": 0.7,
            "open": 0.5,
            "not_available": 0.0,
            "unknown": 0.3,
        }
        score = availability_scores.get(availability.lower(), 0.3)
        vec = np.zeros(self._embedding_dim)
        vec[0] = score
        return vec

    def encode_raw_text(self, raw_text: str | None) -> np.ndarray:
        """Encode raw text using TF-IDF (fitted on corpus)."""
        if not raw_text:
            return np.zeros(100)  # Default dimension for text

        # Simple hash-based encoding for raw text
        words = raw_text.lower().split()
        vec = np.zeros(100)
        for word in words:
            idx = abs(hash(word)) % 100
            vec[idx] += 1
        # Normalize
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def encode(self, profile: Profile) -> ProfileEmbedding:
        """Encode a complete profile into an embedding."""
        skills_vector = self.encode_skills(profile.parsed_skills)
        location_vector = self.encode_location(profile.parsed_location)
        seniority_vector = self.encode_seniority(profile.parsed_seniority)
        languages_vector = self.encode_languages(profile.parsed_languages)
        availability_vector = self.encode_availability(profile.availability_status)
        raw_text_embedding = self.encode_raw_text(profile.raw_text)

        # Weighted combination for final embedding
        combined = np.zeros(self._embedding_dim)
        combined += PROFILE_WEIGHTS["skills"] * skills_vector[: self._embedding_dim]
        combined += PROFILE_WEIGHTS["location"] * location_vector
        combined += PROFILE_WEIGHTS["seniority"] * seniority_vector
        combined += PROFILE_WEIGHTS["languages"] * languages_vector
        combined += PROFILE_WEIGHTS["availability"] * availability_vector

        # Normalize the combined vector
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm

        metadata = {
            "profile_id": profile.id,
            "full_name": profile.full_name,
            "skills_count": len(profile.parsed_skills),
            "seniority": profile.parsed_seniority,
            "location": profile.parsed_location,
        }

        return ProfileEmbedding(
            vector=combined,
            skills_vector=skills_vector,
            location_vector=location_vector,
            seniority_vector=seniority_vector,
            languages_vector=languages_vector,
            availability_vector=availability_vector,
            raw_text_embedding=raw_text_embedding,
            metadata=metadata,
        )


class MissionEncoder:
    """Tower 2: Encodes missions into embedding vectors."""

    def __init__(self) -> None:
        self._embedding_dim = 6

    def encode_skills(self, skills: list[str]) -> np.ndarray:
        """Encode required skills into a normalized embedding vector."""
        if not skills:
            return np.zeros(self._embedding_dim)

        skill_vectors = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in SKILL_EMBEDDINGS:
                skill_vectors.append(np.array(SKILL_EMBEDDINGS[skill_lower]))

        if not skill_vectors:
            # Fallback: create a random but deterministic embedding
            combined = " ".join(sorted(skills))
            hash_val = hash(combined)
            np.random.seed(abs(hash_val) % (2**32))
            return np.random.randn(self._embedding_dim)

        avg_vector = np.mean(skill_vectors, axis=0)
        norm = np.linalg.norm(avg_vector)
        return avg_vector / norm if norm > 0 else avg_vector

    def encode_location(self, location: str | None) -> np.ndarray:
        """Encode location requirement into a vector."""
        if not location:
            return np.zeros(self._embedding_dim)

        location_lower = location.lower()
        location_idx = abs(hash(location_lower)) % self._embedding_dim
        vec = np.zeros(self._embedding_dim)
        vec[location_idx] = 1.0
        return vec

    def encode_seniority(self, seniority: str | None) -> np.ndarray:
        """Encode seniority requirement into a normalized vector."""
        if not seniority:
            return np.zeros(self._embedding_dim)

        seniority_lower = seniority.lower()
        level = SENIORITY_ORDER.get(seniority_lower, 0)
        normalized_level = level / max(SENIORITY_ORDER.values())
        vec = np.zeros(self._embedding_dim)
        vec[0] = normalized_level
        return vec

    def encode_language(self, language: str | None) -> np.ndarray:
        """Encode language requirement."""
        if not language:
            return np.zeros(self._embedding_dim)

        vec = np.zeros(self._embedding_dim)
        lang_lower = language.lower()
        lang_idx = abs(hash(lang_lower)) % self._embedding_dim
        vec[lang_idx] = 1.0
        return vec

    def encode_description(self, title: str, description: str) -> np.ndarray:
        """Encode mission description using hash-based encoding."""
        combined_text = f"{title} {description}"
        words = combined_text.lower().split()
        vec = np.zeros(100)
        for word in words:
            idx = abs(hash(word)) % 100
            vec[idx] += 1
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def encode(self, mission: Mission) -> MissionEmbedding:
        """Encode a complete mission into an embedding."""
        skills_vector = self.encode_skills(mission.required_skills)
        location_vector = self.encode_location(mission.required_location)
        seniority_vector = self.encode_seniority(mission.required_seniority)
        language_vector = self.encode_language(mission.required_language)
        description_embedding = self.encode_description(mission.title, mission.description)

        # Weighted combination for final embedding
        combined = np.zeros(self._embedding_dim)
        combined += MISSION_WEIGHTS["skills"] * skills_vector[: self._embedding_dim]
        combined += MISSION_WEIGHTS["location"] * location_vector
        combined += MISSION_WEIGHTS["seniority"] * seniority_vector
        combined += MISSION_WEIGHTS["language"] * language_vector

        # Normalize
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm

        metadata = {
            "mission_id": mission.id,
            "title": mission.title,
            "skills_count": len(mission.required_skills),
            "seniority": mission.required_seniority,
            "location": mission.required_location,
        }

        return MissionEmbedding(
            vector=combined,
            skills_vector=skills_vector,
            location_vector=location_vector,
            seniority_vector=seniority_vector,
            language_vector=language_vector,
            description_embedding=description_embedding,
            metadata=metadata,
        )


class RecommendationService:
    """Two-tower recommendation service for profile-mission matching."""

    def __init__(self) -> None:
        self.profile_encoder = ProfileEncoder()
        self.mission_encoder = MissionEncoder()
        self._profile_cache: dict[int, ProfileEmbedding] = {}
        self._mission_cache: dict[int, MissionEmbedding] = {}

    def compute_structured_similarity(
        self, profile_emb: ProfileEmbedding, mission_emb: MissionEmbedding
    ) -> float:
        """Compute structured similarity based on explicit features."""
        # Skills overlap (most important)
        skills_sim = cosine_similarity(
            profile_emb.skills_vector.reshape(1, -1),
            mission_emb.skills_vector.reshape(1, -1),
        )[0][0]

        # Location match
        location_sim = cosine_similarity(
            profile_emb.location_vector.reshape(1, -1),
            mission_emb.location_vector.reshape(1, -1),
        )[0][0]

        # Seniority compatibility
        seniority_sim = cosine_similarity(
            profile_emb.seniority_vector.reshape(1, -1),
            mission_emb.seniority_vector.reshape(1, -1),
        )[0][0]

        # Combined structured score
        return float(
            0.5 * skills_sim
            + 0.25 * location_sim
            + 0.15 * seniority_sim
            + 0.1 * profile_emb.availability_vector[0]
        )

    def compute_semantic_similarity(
        self, profile_emb: ProfileEmbedding, mission_emb: MissionEmbedding
    ) -> float:
        """Compute semantic similarity based on learned embeddings."""
        return float(
            cosine_similarity(
                profile_emb.vector.reshape(1, -1),
                mission_emb.vector.reshape(1, -1),
            )[0][0]
        )

    def compute_text_similarity(
        self, profile_emb: ProfileEmbedding, mission_emb: MissionEmbedding
    ) -> float:
        """Compute text-based similarity using TF-IDF."""
        return float(
            cosine_similarity(
                profile_emb.raw_text_embedding.reshape(1, -1),
                mission_emb.description_embedding.reshape(1, -1),
            )[0][0]
        )

    def score_profile_for_mission(
        self,
        profile: Profile,
        mission: Mission,
        use_cache: bool = True,
    ) -> dict[str, object]:
        """
        Score a profile against a mission using the two-tower architecture.

        Returns a dictionary with:
        - structured_score: Score based on explicit features
        - semantic_score: Score from embedding similarity
        - text_score: Score from TF-IDF text matching
        - final_score: Weighted combination
        - explanation_tags: List of matching tags
        """
        # Get or create embeddings
        if use_cache and profile.id in self._profile_cache:
            profile_emb = self._profile_cache[profile.id]
        else:
            profile_emb = self.profile_encoder.encode(profile)
            if use_cache:
                self._profile_cache[profile.id] = profile_emb

        if use_cache and mission.id in self._mission_cache:
            mission_emb = self._mission_cache[mission.id]
        else:
            mission_emb = self.mission_encoder.encode(mission)
            if use_cache:
                self._mission_cache[mission.id] = mission_emb

        # Compute various similarity scores
        structured_sim = self.compute_structured_similarity(profile_emb, mission_emb)
        semantic_sim = self.compute_semantic_similarity(profile_emb, mission_emb)
        text_sim = self.compute_text_similarity(profile_emb, mission_emb)

        # Combine scores with weights
        final_score = (
            0.35 * structured_sim
            + 0.40 * semantic_sim
            + 0.25 * text_sim
        )

        # Generate explanation tags
        tags = self._generate_tags(profile, mission, structured_sim, semantic_sim)

        # Clear cache if it gets too large
        if len(self._profile_cache) > 1000:
            self._profile_cache.clear()
        if len(self._mission_cache) > 100:
            self._mission_cache.clear()

        return {
            "structured_score": round(structured_sim * 100, 2),
            "semantic_score": round(semantic_sim * 100, 2),
            "text_score": round(text_sim * 100, 2),
            "final_score": round(final_score * 100, 2),
            "explanation_tags": tags,
            "embedding_info": {
                "profile_embedding_dim": len(profile_emb.vector),
                "mission_embedding_dim": len(mission_emb.vector),
            },
        }

    def _generate_tags(
        self,
        profile: Profile,
        mission: Mission,
        structured_sim: float,
        semantic_sim: float,
    ) -> list[str]:
        """Generate explanation tags for the match."""
        tags = []

        # Skill matches
        profile_skills = {s.lower() for s in profile.parsed_skills}
        mission_skills = {s.lower() for s in mission.required_skills}
        matching_skills = profile_skills & mission_skills
        if matching_skills:
            tags.append(f"skill_match:{len(matching_skills)}")
            for skill in sorted(matching_skills)[:3]:  # Limit to top 3
                tags.append(f"skill:{skill}")

        # Location match
        if profile.parsed_location and mission.required_location:
            profile_loc = profile.parsed_location.lower()
            mission_loc = mission.required_location.lower()
            if profile_loc == mission_loc or mission_loc == "remote":
                tags.append("location_match")
            elif profile_loc in mission_loc or mission_loc in profile_loc:
                tags.append("location_partial")

        # Seniority match
        if profile.parsed_seniority and mission.required_seniority:
            profile_level = SENIORITY_ORDER.get(profile.parsed_seniority.lower(), 0)
            mission_level = SENIORITY_ORDER.get(mission.required_seniority.lower(), 0)
            if profile_level >= mission_level > 0:
                tags.append("seniority_match")
            elif profile_level > 0 and mission_level > 0:
                tags.append("seniority_close")

        # Language match
        if mission.required_language:
            profile_langs = [lang.lower() for lang in profile.parsed_languages]
            if mission.required_language.lower() in profile_langs:
                tags.append("language_match")

        # Availability
        if profile.availability_status.lower() in {"available", "soon", "open"}:
            tags.append("availability_match")

        # Quality indicators
        if structured_sim > 0.7:
            tags.append("high_structured_match")
        if semantic_sim > 0.8:
            tags.append("high_semantic_match")

        return sorted(set(tags))

    def rank_profiles_for_mission(
        self,
        profiles: list[Profile],
        mission: Mission,
        top_n: int = 10,
    ) -> list[tuple[Profile, dict[str, object]]]:
        """
        Rank profiles for a mission and return top N matches.

        Returns list of (profile, score_dict) tuples sorted by final_score descending.
        """
        results = []
        for profile in profiles:
            score = self.score_profile_for_mission(profile, mission)
            results.append((profile, score))

        # Sort by final_score descending
        results.sort(key=lambda x: x[1]["final_score"], reverse=True)
        return results[:top_n]

    def batch_score(
        self,
        profiles: list[Profile],
        missions: list[Mission],
    ) -> dict[int, list[dict[str, object]]]:
        """
        Batch score all profiles against all missions.

        Returns dict mapping mission_id to list of profile scores.
        """
        results: dict[int, list[dict[str, object]]] = {}

        for mission in missions:
            mission_results = []
            for profile in profiles:
                score = self.score_profile_for_mission(profile, mission)
                score["profile_id"] = profile.id
                score["profile_name"] = profile.full_name
                mission_results.append(score)

            # Sort by final_score
            mission_results.sort(key=lambda x: x["final_score"], reverse=True)
            results[mission.id] = mission_results

        return results


# Singleton instance for reuse
_recommendation_service: RecommendationService | None = None


def get_recommendation_service() -> RecommendationService:
    """Get or create the singleton recommendation service."""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service


def clear_recommendation_cache() -> None:
    """Clear the embedding cache."""
    global _recommendation_service
    if _recommendation_service is not None:
        _recommendation_service._profile_cache.clear()
        _recommendation_service._mission_cache.clear()