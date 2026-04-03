"""Tests for the two-tower recommendation service."""

import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics.pairwise import cosine_similarity

from app.models.mission import Mission
from app.models.profile import Profile
from app.services.recommendation_service import (
    SKILL_EMBEDDINGS,
    MissionEmbedding,
    MissionEncoder,
    ProfileEmbedding,
    ProfileEncoder,
    RecommendationService,
    clear_recommendation_cache,
    get_recommendation_service,
)


@pytest.fixture
def sample_profile() -> Profile:
    """Create a sample profile for testing."""
    return Profile(
        id=1,
        full_name="Test Developer",
        raw_text="Python developer with 5 years experience in FastAPI and React. Located in Paris.",
        parsed_skills=["python", "fastapi", "react"],
        parsed_languages=["en", "fr"],
        parsed_location="paris",
        parsed_seniority="mid",
        availability_status="available",
        source="upload",
    )


@pytest.fixture
def sample_mission() -> Mission:
    """Create a sample mission for testing."""
    return Mission(
        id=1,
        title="Senior Python Developer",
        description="Looking for an experienced Python developer to build APIs.",
        required_skills=["python", "fastapi", "postgresql"],
        required_language="en",
        required_location="paris",
        required_seniority="senior",
        status="active",
        priority="high",
    )


@pytest.fixture
def profiles_fixture() -> list[Profile]:
    """Load profiles from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "profiles.json"
    with open(fixture_path) as f:
        data = json.load(f)

    profiles = []
    for item in data:
        profiles.append(Profile(
            id=item["id"],
            full_name=item["full_name"],
            raw_text=item["raw_text"],
            parsed_skills=item["parsed_skills"],
            parsed_languages=item["parsed_languages"],
            parsed_location=item["parsed_location"],
            parsed_seniority=item["parsed_seniority"],
            availability_status=item["availability_status"],
            source=item["source"],
        ))
    return profiles


@pytest.fixture
def missions_fixture() -> list[Mission]:
    """Load missions from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "missions.json"
    with open(fixture_path) as f:
        data = json.load(f)

    missions = []
    for item in data:
        missions.append(Mission(
            id=item["id"],
            title=item["title"],
            description=item["description"],
            required_skills=item["required_skills"],
            required_language=item.get("required_language"),
            required_location=item.get("required_location"),
            required_seniority=item.get("required_seniority"),
            status=item.get("status", "active"),
            priority=item.get("priority", "medium"),
        ))
    return missions


class TestProfileEncoder:
    """Tests for ProfileEncoder."""

    def test_encode_skills_known_skills(self):
        """Test encoding of known skills."""
        encoder = ProfileEncoder()
        skills = ["python", "react", "docker"]
        vector = encoder.encode_skills(skills)

        assert vector.shape == (encoder._embedding_dim,)
        # Should have non-zero values for known skills
        assert np.any(vector != 0)

    def test_encode_skills_empty(self):
        """Test encoding with empty skills."""
        encoder = ProfileEncoder()
        vector = encoder.encode_skills([])

        assert vector.shape == (encoder._embedding_dim,)
        assert np.all(vector == 0)

    def test_encode_skills_unknown_skill(self):
        """Test encoding with unknown skill (should use fallback)."""
        encoder = ProfileEncoder()
        skills = ["obscure_skill_xyz"]
        vector = encoder.encode_skills(skills)

        assert vector.shape == (encoder._embedding_dim,)
        # Should still produce a valid embedding

    def test_encode_location_known(self):
        """Test encoding of known location."""
        encoder = ProfileEncoder()
        vector = encoder.encode_location("paris")

        assert vector.shape == (encoder._embedding_dim,)
        assert np.any(vector == 1.0)

    def test_encode_location_none(self):
        """Test encoding with None location."""
        encoder = ProfileEncoder()
        vector = encoder.encode_location(None)

        assert vector.shape == (encoder._embedding_dim,)
        assert np.all(vector == 0)

    def test_encode_seniority_known(self):
        """Test encoding of known seniority levels."""
        encoder = ProfileEncoder()

        junior_vec = encoder.encode_seniority("junior")
        mid_vec = encoder.encode_seniority("mid")
        senior_vec = encoder.encode_seniority("senior")
        lead_vec = encoder.encode_seniority("lead")

        # Seniority should increase with level
        assert junior_vec[0] < mid_vec[0]
        assert mid_vec[0] < senior_vec[0]
        assert senior_vec[0] < lead_vec[0]

    def test_encode_seniority_none(self):
        """Test encoding with None seniority."""
        encoder = ProfileEncoder()
        vector = encoder.encode_seniority(None)

        assert vector.shape == (encoder._embedding_dim,)
        assert np.all(vector == 0)

    def test_encode_languages(self):
        """Test encoding of languages."""
        encoder = ProfileEncoder()
        languages = ["en", "fr", "de"]
        vector = encoder.encode_languages(languages)

        assert vector.shape == (encoder._embedding_dim,)
        # Should have some non-zero values
        assert np.any(vector != 0)

    def test_encode_availability(self):
        """Test encoding of availability status."""
        encoder = ProfileEncoder()

        available = encoder.encode_availability("available")
        soon = encoder.encode_availability("soon")
        open_status = encoder.encode_availability("open")

        # Available should have highest score
        assert available[0] > soon[0]
        assert soon[0] > open_status[0]

    def test_encode_full_profile(self, sample_profile):
        """Test encoding of a complete profile."""
        encoder = ProfileEncoder()
        embedding = encoder.encode(sample_profile)

        assert isinstance(embedding, ProfileEmbedding)
        assert embedding.vector.shape == (encoder._embedding_dim,)
        assert embedding.metadata["profile_id"] == sample_profile.id
        assert embedding.metadata["full_name"] == sample_profile.full_name


class TestMissionEncoder:
    """Tests for MissionEncoder."""

    def test_encode_skills(self):
        """Test encoding of mission skills."""
        encoder = MissionEncoder()
        skills = ["python", "fastapi"]
        vector = encoder.encode_skills(skills)

        assert vector.shape == (encoder._embedding_dim,)
        assert np.any(vector != 0)

    def test_encode_location(self):
        """Test encoding of mission location."""
        encoder = MissionEncoder()
        vector = encoder.encode_location("paris")

        assert vector.shape == (encoder._embedding_dim,)
        assert np.any(vector == 1.0)

    def test_encode_seniority(self):
        """Test encoding of seniority requirement."""
        encoder = MissionEncoder()
        vector = encoder.encode_seniority("senior")

        assert vector.shape == (encoder._embedding_dim,)
        assert vector[0] > 0

    def test_encode_full_mission(self, sample_mission):
        """Test encoding of a complete mission."""
        encoder = MissionEncoder()
        embedding = encoder.encode(sample_mission)

        assert isinstance(embedding, MissionEmbedding)
        assert embedding.vector.shape == (encoder._embedding_dim,)
        assert embedding.metadata["mission_id"] == sample_mission.id


class TestRecommendationService:
    """Tests for RecommendationService."""

    def test_compute_structured_similarity(self, sample_profile, sample_mission):
        """Test structured similarity computation."""
        service = RecommendationService()
        profile_emb = service.profile_encoder.encode(sample_profile)
        mission_emb = service.mission_encoder.encode(sample_mission)

        similarity = service.compute_structured_similarity(profile_emb, mission_emb)

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_compute_semantic_similarity(self, sample_profile, sample_mission):
        """Test semantic similarity computation."""
        service = RecommendationService()
        profile_emb = service.profile_encoder.encode(sample_profile)
        mission_emb = service.mission_encoder.encode(sample_mission)

        similarity = service.compute_semantic_similarity(profile_emb, mission_emb)

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_score_profile_for_mission(self, sample_profile, sample_mission):
        """Test full profile scoring."""
        service = RecommendationService()
        result = service.score_profile_for_mission(sample_profile, sample_mission)

        assert "structured_score" in result
        assert "semantic_score" in result
        assert "text_score" in result
        assert "final_score" in result
        assert "explanation_tags" in result

        assert isinstance(result["structured_score"], float)
        assert isinstance(result["semantic_score"], float)
        assert isinstance(result["final_score"], float)
        assert isinstance(result["explanation_tags"], list)

        # Scores should be in percentage (0-100)
        assert 0 <= result["structured_score"] <= 100
        assert 0 <= result["semantic_score"] <= 100
        assert 0 <= result["final_score"] <= 100

    def test_score_with_skill_match(self, sample_profile, sample_mission):
        """Test that skill matches are detected."""
        service = RecommendationService()
        result = service.score_profile_for_mission(sample_profile, sample_mission)

        # Profile has python and fastapi, mission requires python and fastapi
        tags = result["explanation_tags"]
        assert any("skill" in tag.lower() for tag in tags)

    def test_score_with_location_match(self, sample_profile, sample_mission):
        """Test that location matches are detected."""
        service = RecommendationService()
        result = service.score_profile_for_mission(sample_profile, sample_mission)

        tags = result["explanation_tags"]
        assert "location_match" in tags

    def test_score_with_language_match(self, sample_profile, sample_mission):
        """Test that language matches are detected."""
        service = RecommendationService()
        result = service.score_profile_for_mission(sample_profile, sample_mission)

        tags = result["explanation_tags"]
        assert "language_match" in tags

    def test_rank_profiles_for_mission(self, profiles_fixture, missions_fixture):
        """Test ranking multiple profiles for a mission."""
        service = RecommendationService()
        mission = missions_fixture[0]  # Junior Python Developer

        rankings = service.rank_profiles_for_mission(
            profiles_fixture, mission, top_n=5
        )

        assert len(rankings) <= 5
        assert len(rankings) > 0

        # Rankings should be sorted by final_score descending
        scores = [r[1]["final_score"] for r in rankings]
        assert scores == sorted(scores, reverse=True)

    def test_batch_scoring(self, profiles_fixture, missions_fixture):
        """Test batch scoring of all profiles against all missions."""
        service = RecommendationService()
        results = service.batch_score(profiles_fixture, missions_fixture)

        assert len(results) == len(missions_fixture)

        for mission_id, scores in results.items():
            assert mission_id in [m.id for m in missions_fixture]
            assert all("final_score" in s for s in scores)
            # Scores should be sorted
            sorted_scores = sorted(scores, key=lambda x: x["final_score"], reverse=True)
            assert scores == sorted_scores

    def test_caching(self, sample_profile, sample_mission):
        """Test that caching works correctly."""
        service = RecommendationService()

        # First call should cache
        result1 = service.score_profile_for_mission(sample_profile, sample_mission)
        assert sample_profile.id in service._profile_cache
        assert sample_mission.id in service._mission_cache

        # Second call should use cache
        result2 = service.score_profile_for_mission(sample_profile, sample_mission)
        assert result1["final_score"] == result2["final_score"]

    def test_clear_cache(self, sample_profile, sample_mission):
        """Test cache clearing."""
        # Use the singleton to ensure cache is shared
        service = get_recommendation_service()
        service.score_profile_for_mission(sample_profile, sample_mission)

        clear_recommendation_cache()

        # Check the singleton's cache (not a new instance)
        service = get_recommendation_service()
        assert len(service._profile_cache) == 0
        assert len(service._mission_cache) == 0

    def test_singleton(self):
        """Test singleton pattern."""
        service1 = get_recommendation_service()
        service2 = get_recommendation_service()

        assert service1 is service2

    def test_empty_profile_handling(self, sample_mission):
        """Test handling of profile with minimal data."""
        service = RecommendationService()
        profile = Profile(
            id=999,
            full_name="Empty Profile",
            raw_text=None,
            parsed_skills=[],
            parsed_languages=[],
            parsed_location=None,
            parsed_seniority=None,
            availability_status="unknown",
            source="upload",
        )

        result = service.score_profile_for_mission(profile, sample_mission)

        assert "final_score" in result
        # Empty profile should still get a valid score
        assert result["final_score"] >= 0

    def test_empty_mission_handling(self, sample_profile):
        """Test handling of mission with minimal requirements."""
        service = RecommendationService()
        mission = Mission(
            id=999,
            title="Generic Position",
            description="A generic position",
            required_skills=[],
            required_language=None,
            required_location=None,
            required_seniority=None,
            status="active",
            priority="medium",
        )

        result = service.score_profile_for_mission(sample_profile, mission)

        assert "final_score" in result
        assert result["final_score"] >= 0


class TestSkillEmbeddings:
    """Tests for skill embedding quality."""

    def test_related_skills_have_similar_embeddings(self):
        """Test that related skills have similar embeddings."""
        # Backend skills should be similar
        python = np.array(SKILL_EMBEDDINGS["python"])
        fastapi = np.array(SKILL_EMBEDDINGS["fastapi"])

        similarity = cosine_similarity(
            python.reshape(1, -1), fastapi.reshape(1, -1)
        )[0][0]

        assert similarity > 0.8  # High similarity for related skills

    def test_different_categories_have_different_embeddings(self):
        """Test that skills from different categories differ."""
        python = np.array(SKILL_EMBEDDINGS["python"])
        react = np.array(SKILL_EMBEDDINGS["react"])
        docker = np.array(SKILL_EMBEDDINGS["docker"])

        # Backend vs Frontend
        similarity_python_react = cosine_similarity(
            python.reshape(1, -1), react.reshape(1, -1)
        )[0][0]

        # Backend vs DevOps
        similarity_python_docker = cosine_similarity(
            python.reshape(1, -1), docker.reshape(1, -1)
        )[0][0]

        # Same category should be more similar
        assert similarity_python_docker < similarity_python_react or similarity_python_react < 0.5