"""Tests for matching API endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.mission import Mission
from app.models.profile import Profile


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    """Get admin auth headers."""
    import os
    login = client.post(
        "/api/auth/login",
        json={
            "username": os.environ.get("ADMIN_USERNAME", "admin"),
            "password": os.environ.get("ADMIN_PASSWORD", "TestAdmin#2026Secure"),
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def profiles_fixture() -> list[dict]:
    """Load profiles from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "profiles.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def missions_fixture() -> list[dict]:
    """Load missions from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "missions.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestMatchingEndpoint:
    """Tests for the POST /missions/{mission_id}/match endpoint."""

    def test_run_matching_success(self, client: TestClient, admin_headers: dict):
        """Test successful matching run."""
        # First create a profile
        profile_data = {
            "full_name": "Test Developer",
            "raw_text": "Python developer with 5 years experience",
            "parsed_skills": ["python", "fastapi"],
            "parsed_languages": ["en", "fr"],
            "parsed_location": "paris",
            "parsed_seniority": "mid",
            "availability_status": "available",
        }
        create_profile = client.post(
            "/api/profiles",
            json=profile_data,
            headers=admin_headers,
        )
        assert create_profile.status_code in [200, 201]

        # Create a mission
        mission_data = {
            "title": "Python Developer",
            "description": "Need Python developer",
            "required_skills": ["python"],
            "required_language": "en",
            "required_location": "paris",
            "required_seniority": "mid",
        }
        create_mission = client.post(
            "/api/missions",
            json=mission_data,
            headers=admin_headers,
        )
        assert create_mission.status_code in [200, 201]
        mission_id = create_mission.json()["id"]

        # Run matching
        response = client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

        # Check result structure
        for result in results:
            assert "mission_id" in result
            assert "profile_id" in result
            assert "final_score" in result
            assert "structured_score" in result
            assert "semantic_score" in result
            assert "business_score" in result
            assert "explanation_tags" in result

    def test_run_matching_with_top_n(self, client: TestClient, admin_headers: dict):
        """Test matching with top_n parameter."""
        # Create multiple profiles
        for i in range(5):
            profile_data = {
                "full_name": f"Developer {i}",
                "parsed_skills": ["python"],
                "parsed_languages": ["en"],
                "availability_status": "available",
            }
            client.post("/api/profiles", json=profile_data, headers=admin_headers)

        # Create mission
        mission_data = {
            "title": "Python Dev",
            "description": "Test",
            "required_skills": ["python"],
        }
        create_mission = client.post(
            "/api/missions",
            json=mission_data,
            headers=admin_headers,
        )
        mission_id = create_mission.json()["id"]

        # Run matching with top_n=3
        response = client.post(
            f"/api/missions/{mission_id}/match?top_n=3",
            headers=admin_headers,
        )

        assert response.status_code == 200
        results = response.json()
        assert len(results) <= 3

    def test_run_matching_mission_not_found(self, client: TestClient, admin_headers: dict):
        """Test matching with non-existent mission."""
        response = client.post(
            "/api/missions/999999/match",
            headers=admin_headers,
        )

        assert response.status_code == 404

    def test_run_matching_unauthorized(self, client: TestClient):
        """Test matching without authentication."""
        response = client.post("/api/missions/1/match")

        assert response.status_code == 401

    def test_run_matching_empty_profiles(self, client: TestClient, admin_headers: dict):
        """Test matching when no profiles exist."""
        # Create mission
        mission_data = {
            "title": "Test Mission",
            "description": "Test",
            "required_skills": ["python"],
        }
        create_mission = client.post(
            "/api/missions",
            json=mission_data,
            headers=admin_headers,
        )
        mission_id = create_mission.json()["id"]

        # Delete all profiles first (if any)
        # This test assumes no profiles or we clean them

        # Run matching
        response = client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        # Should return empty list
        assert response.status_code == 200
        assert response.json() == []


class TestListMatchesEndpoint:
    """Tests for the GET /missions/{mission_id}/matches endpoint."""

    def test_list_matches_success(self, client: TestClient, admin_headers: dict):
        """Test listing matches after running matching."""
        # Create profile
        profile_data = {
            "full_name": "Match Test Dev",
            "parsed_skills": ["python"],
            "availability_status": "available",
        }
        client.post("/api/profiles", json=profile_data, headers=admin_headers)

        # Create mission
        mission_data = {
            "title": "Match Test Mission",
            "description": "Test",
            "required_skills": ["python"],
        }
        create_mission = client.post(
            "/api/missions",
            json=mission_data,
            headers=admin_headers,
        )
        mission_id = create_mission.json()["id"]

        # Run matching first
        client.post(f"/api/missions/{mission_id}/match", headers=admin_headers)

        # List matches
        response = client.get(f"/api/missions/{mission_id}/matches")

        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

    def test_list_matches_ordered_by_score(self, client: TestClient, admin_headers: dict):
        """Test that matches are ordered by score descending."""
        # Create multiple profiles with different scores
        for i in range(3):
            profile_data = {
                "full_name": f"Score Test Dev {i}",
                "parsed_skills": ["python"] if i == 0 else ["java"],
                "availability_status": "available",
            }
            client.post("/api/profiles", json=profile_data, headers=admin_headers)

        # Create mission requiring Python
        mission_data = {
            "title": "Score Test Mission",
            "description": "Need Python",
            "required_skills": ["python"],
        }
        create_mission = client.post(
            "/api/missions",
            json=mission_data,
            headers=admin_headers,
        )
        mission_id = create_mission.json()["id"]

        # Run matching
        client.post(f"/api/missions/{mission_id}/match", headers=admin_headers)

        # List matches
        response = client.get(f"/api/missions/{mission_id}/matches")
        assert response.status_code == 200

        results = response.json()
        if len(results) > 1:
            scores = [r["final_score"] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_list_matches_mission_not_found(self, client: TestClient):
        """Test listing matches for non-existent mission."""
        response = client.get("/api/missions/999999/matches")

        assert response.status_code == 404

    def test_list_matches_no_matches(self, client: TestClient, admin_headers: dict):
        """Test listing matches when matching hasn't been run."""
        # Create mission
        mission_data = {
            "title": "No Matches Mission",
            "description": "Test",
            "required_skills": ["python"],
        }
        create_mission = client.post(
            "/api/missions",
            json=mission_data,
            headers=admin_headers,
        )
        mission_id = create_mission.json()["id"]

        # List matches without running matching
        response = client.get(f"/api/missions/{mission_id}/matches")

        # Should return empty list (mission exists but no matches)
        assert response.status_code == 200
        assert response.json() == []


class TestMatchingWithFixtures:
    """Tests using fixture data."""

    @pytest.fixture
    def setup_fixture_data(
        self, client: TestClient, admin_headers: dict,
        profiles_fixture: list[dict], missions_fixture: list[dict]
    ):
        """Setup profiles and missions from fixtures."""
        created_profiles = []
        created_missions = []

        # Create profiles
        for profile_data in profiles_fixture[:5]:  # Limit to 5 for test speed
            response = client.post(
                "/api/profiles",
                json={
                    "full_name": profile_data["full_name"],
                    "raw_text": profile_data.get("raw_text"),
                    "parsed_skills": profile_data.get("parsed_skills", []),
                    "parsed_languages": profile_data.get("parsed_languages", []),
                    "parsed_location": profile_data.get("parsed_location"),
                    "parsed_seniority": profile_data.get("parsed_seniority"),
                    "availability_status": profile_data.get("availability_status", "unknown"),
                    "source": profile_data.get("source", "upload"),
                },
                headers=admin_headers,
            )
            if response.status_code in [200, 201]:
                created_profiles.append(response.json())

        # Create missions
        for mission_data in missions_fixture[:3]:  # Limit to 3 for test speed
            response = client.post(
                "/api/missions",
                json={
                    "title": mission_data["title"],
                    "description": mission_data["description"],
                    "required_skills": mission_data.get("required_skills", []),
                    "required_language": mission_data.get("required_language"),
                    "required_location": mission_data.get("required_location"),
                    "required_seniority": mission_data.get("required_seniority"),
                },
                headers=admin_headers,
            )
            if response.status_code in [200, 201]:
                created_missions.append(response.json())

        return created_profiles, created_missions

    def test_matching_with_fixture_data(
        self, client: TestClient, admin_headers: dict,
        profiles_fixture: list[dict], missions_fixture: list[dict]
    ):
        """Test matching using fixture data."""
        # Create one profile
        profile_data = profiles_fixture[0]
        create_profile = client.post(
            "/api/profiles",
            json={
                "full_name": profile_data["full_name"],
                "raw_text": profile_data.get("raw_text"),
                "parsed_skills": profile_data.get("parsed_skills", []),
                "parsed_languages": profile_data.get("parsed_languages", []),
                "parsed_location": profile_data.get("parsed_location"),
                "parsed_seniority": profile_data.get("parsed_seniority"),
                "availability_status": profile_data.get("availability_status", "unknown"),
            },
            headers=admin_headers,
        )
        assert create_profile.status_code in [200, 201]

        # Create one mission
        mission_data = missions_fixture[0]
        create_mission = client.post(
            "/api/missions",
            json={
                "title": mission_data["title"],
                "description": mission_data["description"],
                "required_skills": mission_data.get("required_skills", []),
                "required_language": mission_data.get("required_language"),
                "required_location": mission_data.get("required_location"),
                "required_seniority": mission_data.get("required_seniority"),
            },
            headers=admin_headers,
        )
        assert create_mission.status_code in [200, 201]
        mission_id = create_mission.json()["id"]

        # Run matching
        response = client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1

        # Verify match result structure
        match = results[0]
        assert "final_score" in match
        assert match["final_score"] >= 0
        assert match["final_score"] <= 100
        assert isinstance(match["explanation_tags"], list)


class TestScoreBreakdown:
    """Tests for score breakdown components."""

    def test_score_components_sum_correctly(self, client: TestClient, admin_headers: dict):
        """Test that score components contribute to final score."""
        # Create profile with known attributes
        profile_data = {
            "full_name": "Score Test Profile",
            "parsed_skills": ["python", "fastapi"],
            "parsed_languages": ["en"],
            "parsed_location": "paris",
            "parsed_seniority": "senior",
            "availability_status": "available",
        }
        client.post("/api/profiles", json=profile_data, headers=admin_headers)

        # Create mission
        mission_data = {
            "title": "Score Test Mission",
            "description": "Need Python FastAPI",
            "required_skills": ["python", "fastapi"],
            "required_language": "en",
            "required_location": "paris",
            "required_seniority": "mid",
        }
        create_mission = client.post(
            "/api/missions",
            json=mission_data,
            headers=admin_headers,
        )
        mission_id = create_mission.json()["id"]

        # Run matching
        response = client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        assert response.status_code == 200
        results = response.json()

        if len(results) > 0:
            result = results[0]
            # All scores should be non-negative and <= 100
            assert 0 <= result["structured_score"] <= 100
            assert 0 <= result["semantic_score"] <= 100
            assert 0 <= result["business_score"] <= 100
            assert 0 <= result["final_score"] <= 100

            # Final score is weighted combination
            # structured * 0.4 + semantic * 0.4 + business * 0.2
            expected = (
                result["structured_score"] * 0.4 +
                result["semantic_score"] * 0.4 +
                result["business_score"] * 0.2
            )
            # Allow small rounding differences
            assert abs(result["final_score"] - expected) < 1.0