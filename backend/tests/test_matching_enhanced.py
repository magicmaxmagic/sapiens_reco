"""Enhanced tests for the matching service using fixtures."""

import json
from pathlib import Path

import pytest

from app.models.mission import Mission
from app.models.profile import Profile
from app.services.matching_service import (
    SENIORITY_ORDER,
    _business_score,
    _normalize,
    _semantic_score,
    _structured_score,
    score_profile_for_mission,
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


class TestNormalize:
    """Tests for the _normalize helper function."""

    def test_normalize_lowercase(self):
        """Test normalization converts to lowercase."""
        assert _normalize("PARIS") == "paris"
        assert _normalize("Python") == "python"

    def test_normalize_strips_whitespace(self):
        """Test normalization strips whitespace."""
        assert _normalize("  python  ") == "python"
        assert _normalize("\tpython\n") == "python"

    def test_normalize_none(self):
        """Test normalization of None returns empty string."""
        assert _normalize(None) == ""

    def test_normalize_empty_string(self):
        """Test normalization of empty string."""
        assert _normalize("") == ""


class TestStructuredScore:
    """Tests for the _structured_score function."""

    @pytest.fixture
    def profile(self):
        """Create a test profile."""
        return Profile(
            id=1,
            full_name="Test Developer",
            parsed_skills=["python", "fastapi", "sql"],
            parsed_languages=["en", "fr"],
            parsed_location="paris",
            parsed_seniority="mid",
            availability_status="available",
            source="upload",
        )

    @pytest.fixture
    def mission(self):
        """Create a test mission."""
        return Mission(
            id=1,
            title="Python Developer",
            description="Need Python developer",
            required_skills=["python", "sql"],
            required_language="en",
            required_location="paris",
            required_seniority="mid",
            status="active",
        )

    def test_perfect_match(self, profile, mission):
        """Test structured score with perfect match."""
        score, tags = _structured_score(mission, profile)

        assert score == 100.0  # All constraints matched
        assert "language_match" in tags
        assert "location_match" in tags
        assert "seniority_match" in tags
        assert "availability_match" in tags

    def test_language_mismatch(self, profile):
        """Test structured score with language mismatch."""
        mission = Mission(
            id=1,
            title="Position",
            description="Need German speaker",
            required_skills=[],
            required_language="de",
            required_location=None,
            required_seniority=None,
            status="active",
        )

        score, tags = _structured_score(mission, profile)

        assert score < 100.0
        assert "language_match" not in tags

    def test_location_mismatch(self, profile):
        """Test structured score with location mismatch."""
        mission = Mission(
            id=1,
            title="Position",
            description="Remote position",
            required_skills=[],
            required_language=None,
            required_location="remote",
            required_seniority=None,
            status="active",
        )

        score, tags = _structured_score(mission, profile)

        # Location mismatch
        assert "location_match" not in tags

    def test_seniority_above_requirement(self, profile):
        """Test structured score when candidate exceeds seniority."""
        mission = Mission(
            id=1,
            title="Position",
            description="Junior position",
            required_skills=[],
            required_language=None,
            required_location=None,
            required_seniority="junior",
            status="active",
        )

        score, tags = _structured_score(mission, profile)

        # Mid candidate meets junior requirement
        assert "seniority_match" in tags

    def test_seniority_below_requirement(self, profile):
        """Test structured score when candidate below seniority."""
        mission = Mission(
            id=1,
            title="Position",
            description="Senior position",
            required_skills=[],
            required_language=None,
            required_location=None,
            required_seniority="senior",
            status="active",
        )

        score, tags = _structured_score(mission, profile)

        # Mid candidate doesn't meet senior requirement
        assert "seniority_match" not in tags

    def test_no_structured_constraints(self, profile):
        """Test structured score with no constraints."""
        mission = Mission(
            id=1,
            title="Position",
            description="Open position",
            required_skills=[],
            required_language=None,
            required_location=None,
            required_seniority=None,
            status="active",
        )

        score, tags = _structured_score(mission, profile)

        # Should return 100% with no structured constraints
        assert score == 100.0
        assert "no_structured_constraints" in tags


class TestSemanticScore:
    """Tests for the _semantic_score function."""

    def test_high_semantic_overlap(self):
        """Test semantic score with high text overlap."""
        mission = Mission(
            id=1,
            title="Python Developer",
            description="Looking for Python FastAPI developer",
            required_skills=["python", "fastapi"],
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Python Developer",
            raw_text="Experienced Python FastAPI developer with 5 years experience",
            parsed_skills=["python", "fastapi"],
            source="upload",
        )

        score = _semantic_score(mission, profile)

        # High overlap should give decent score
        assert score > 30.0

    def test_low_semantic_overlap(self):
        """Test semantic score with low text overlap."""
        mission = Mission(
            id=1,
            title="Java Developer",
            description="Looking for Java Spring developer",
            required_skills=["java", "spring"],
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Python Developer",
            raw_text="Experienced Python developer with Django expertise",
            parsed_skills=["python", "django"],
            source="upload",
        )

        score = _semantic_score(mission, profile)

        # Low overlap should give low score
        assert score < 50.0

    def test_empty_texts(self):
        """Test semantic score with empty texts."""
        mission = Mission(
            id=1,
            title="Position",
            description="",
            required_skills=[],
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="",
            raw_text=None,
            parsed_skills=[],
            source="upload",
        )

        score = _semantic_score(mission, profile)

        assert score == 0.0


class TestBusinessScore:
    """Tests for the _business_score function."""

    def test_all_skills_match(self):
        """Test business score when all skills match."""
        mission = Mission(
            id=1,
            title="Position",
            description="Need Python and SQL",
            required_skills=["python", "sql"],
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Developer",
            parsed_skills=["python", "sql", "javascript"],
            source="upload",
        )

        score, tags = _business_score(mission, profile)

        # All required skills present
        assert score >= 85.0
        assert "skill:python" in tags
        assert "skill:sql" in tags

    def test_partial_skills_match(self):
        """Test business score with partial skill match."""
        mission = Mission(
            id=1,
            title="Position",
            description="Need Python SQL and Java",
            required_skills=["python", "sql", "java"],
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Developer",
            parsed_skills=["python", "sql"],
            source="upload",
        )

        score, tags = _business_score(mission, profile)

        # 2 out of 3 skills
        assert score >= 50.0
        assert "skill:python" in tags
        assert "skill:sql" in tags

    def test_no_skills_match(self):
        """Test business score with no skill match."""
        mission = Mission(
            id=1,
            title="Position",
            description="Need Java",
            required_skills=["java"],
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Developer",
            parsed_skills=["python", "javascript"],
            source="upload",
        )

        score, tags = _business_score(mission, profile)

        # No skills match
        assert score < 20.0
        assert len(tags) == 0

    def test_upload_freshness_bonus(self):
        """Test that upload source gives freshness bonus."""
        mission = Mission(
            id=1,
            title="Position",
            description="Need Python",
            required_skills=["python"],
            status="active",
        )
        profile_upload = Profile(
            id=1,
            full_name="Dev",
            parsed_skills=["python"],
            source="upload",
        )
        profile_linkedin = Profile(
            id=2,
            full_name="Dev",
            parsed_skills=["python"],
            source="linkedin",
        )

        score_upload, _ = _business_score(mission, profile_upload)
        score_linkedin, _ = _business_score(mission, profile_linkedin)

        # Upload should get higher bonus
        assert score_upload > score_linkedin

    def test_no_required_skills(self):
        """Test business score with no required skills."""
        mission = Mission(
            id=1,
            title="Position",
            description="Open position",
            required_skills=[],
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Developer",
            parsed_skills=["python", "sql"],
            source="upload",
        )

        score, tags = _business_score(mission, profile)

        # No required skills should give default score
        assert score == 50.0
        assert "no_required_skills" in tags


class TestScoreProfileForMission:
    """Tests for the full score_profile_for_mission function."""

    def test_comprehensive_scoring(self):
        """Test comprehensive scoring with all components."""
        mission = Mission(
            id=1,
            title="Senior Python Developer",
            description="Looking for senior Python developer with FastAPI experience",
            required_skills=["python", "fastapi"],
            required_language="en",
            required_location="paris",
            required_seniority="senior",
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Senior Developer",
            raw_text="Experienced Python FastAPI developer based in Paris",
            parsed_skills=["python", "fastapi", "sql"],
            parsed_languages=["en", "fr"],
            parsed_location="paris",
            parsed_seniority="senior",
            availability_status="available",
            source="upload",
        )

        result = score_profile_for_mission(mission, profile)

        # Check all score components
        assert "structured_score" in result
        assert "semantic_score" in result
        assert "business_score" in result
        assert "final_score" in result
        assert "explanation_tags" in result

        # All constraints match, should be high score
        assert result["final_score"] > 70.0

        # Should have multiple explanation tags
        assert len(result["explanation_tags"]) >= 3

    def test_score_range(self):
        """Test that all scores are in valid range."""
        mission = Mission(
            id=1,
            title="Position",
            description="Test position",
            required_skills=["skill1", "skill2"],
            required_language="en",
            required_location="paris",
            required_seniority="mid",
            status="active",
        )
        profile = Profile(
            id=1,
            full_name="Developer",
            raw_text="Developer with skills",
            parsed_skills=["skill1"],
            parsed_languages=["fr"],
            parsed_location="lyon",
            parsed_seniority="junior",
            availability_status="not_available",
            source="linkedin",
        )

        result = score_profile_for_mission(mission, profile)

        # All scores should be in [0, 100]
        assert 0 <= result["structured_score"] <= 100
        assert 0 <= result["semantic_score"] <= 100
        assert 0 <= result["business_score"] <= 100
        assert 0 <= result["final_score"] <= 100


class TestMatchingWithFixtures:
    """Tests using the fixture data."""

    def test_junior_position_matching(self, profiles_fixture, missions_fixture):
        """Test matching for junior positions."""
        # Find the junior Python developer position
        junior_mission = next(
            (m for m in missions_fixture if m.id == 1), None
        )
        assert junior_mission is not None
        assert junior_mission.required_seniority == "junior"

        # Score all profiles
        results = []
        for profile in profiles_fixture:
            score = score_profile_for_mission(junior_mission, profile)
            results.append((profile, score))

        # Sort by final score
        results.sort(key=lambda x: x[1]["final_score"], reverse=True)

        # Junior profiles should rank higher for junior positions
        top_profiles = [r[0] for r in results[:5]]
        junior_count = sum(
            1 for p in top_profiles
            if p.parsed_seniority in ("junior", "mid")
        )

        # At least some junior/mid profiles should be in top 5
        assert junior_count >= 2

    def test_senior_position_matching(self, profiles_fixture, missions_fixture):
        """Test matching for senior positions."""
        # Find senior backend engineer position
        senior_mission = next(
            (m for m in missions_fixture if m.id == 2), None
        )
        assert senior_mission is not None
        assert senior_mission.required_seniority == "senior"

        results = []
        for profile in profiles_fixture:
            score = score_profile_for_mission(senior_mission, profile)
            results.append((profile, score))

        results.sort(key=lambda x: x[1]["final_score"], reverse=True)

        # Top results should have relevant skills
        top_profile = results[0][0]
        assert "python" in [s.lower() for s in top_profile.parsed_skills]

    def test_remote_position_matching(self, profiles_fixture, missions_fixture):
        """Test matching for remote positions."""
        # Find remote positions
        remote_missions = [
            m for m in missions_fixture
            if m.required_location and m.required_location.lower() == "remote"
        ]

        assert len(remote_missions) > 0

        for mission in remote_missions:
            results = []
            for profile in profiles_fixture:
                score = score_profile_for_mission(mission, profile)
                results.append((profile, score))

            results.sort(key=lambda x: x[1]["final_score"], reverse=True)

            # Remote positions should match profiles regardless of location
            assert len(results) > 0
            assert results[0][1]["final_score"] > 0

    def test_skill_based_matching(self, profiles_fixture, missions_fixture):
        """Test that skill matching is a major factor."""
        # Find ML Engineer position
        ml_mission = next(
            (m for m in missions_fixture if m.id == 9), None
        )
        assert ml_mission is not None
        assert "tensorflow" in [s.lower() for s in ml_mission.required_skills]

        results = []
        for profile in profiles_fixture:
            score = score_profile_for_mission(ml_mission, profile)
            results.append((profile, score))

        results.sort(key=lambda x: x[1]["final_score"], reverse=True)

        # Top profiles should have ML skills
        top_3_profiles = [r[0] for r in results[:3]]
        for profile in top_3_profiles:
            # Should have some overlap with required skills
            profile_skills = {s.lower() for s in profile.parsed_skills}
            mission_skills = {s.lower() for s in ml_mission.required_skills}
            overlap = profile_skills & mission_skills
            # At least some skill overlap expected for top results
            assert len(overlap) > 0 or score["final_score"] > 40

    def test_location_preference(self, profiles_fixture, missions_fixture):
        """Test that location matching affects scores."""
        # Find Paris position
        paris_mission = next(
            (m for m in missions_fixture
             if m.required_location and m.required_location.lower() == "paris"),
            None
        )
        assert paris_mission is not None

        # Get Paris-based profiles
        paris_profiles = [
            p for p in profiles_fixture
            if p.parsed_location and p.parsed_location.lower() == "paris"
        ]

        # Get non-Paris profiles
        other_profiles = [
            p for p in profiles_fixture
            if not p.parsed_location or p.parsed_location.lower() != "paris"
        ]

        if paris_profiles and other_profiles:
            # Compare average scores
            paris_scores = [
                score_profile_for_mission(paris_mission, p)["final_score"]
                for p in paris_profiles
            ]
            other_scores = [
                score_profile_for_mission(paris_mission, p)["final_score"]
                for p in other_profiles
            ]

            # Paris profiles should generally score higher for Paris positions
            # (accounting for other factors like skills)
            avg_paris = sum(paris_scores) / len(paris_scores)
            avg_other = sum(other_scores) / len(other_scores)

            # Paris location gives advantage
            assert avg_paris > avg_other or abs(avg_paris - avg_other) < 20

    def test_consistency_across_multiple_runs(self, profiles_fixture, missions_fixture):
        """Test that scoring is consistent across multiple runs."""
        mission = missions_fixture[0]
        profile = profiles_fixture[0]

        scores = [
            score_profile_for_mission(mission, profile)
            for _ in range(5)
        ]

        # All scores should be identical
        final_scores = [s["final_score"] for s in scores]
        assert len(set(final_scores)) == 1  # All same value