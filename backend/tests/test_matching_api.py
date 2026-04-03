"""Tests for matching API endpoints."""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


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


def create_profile_via_upload(client: TestClient, admin_headers: dict, profile_data: dict) -> dict:
    """Helper to create a profile via upload."""
    # Create a text file with profile info
    content = f"{profile_data.get('full_name', 'Test Developer')}\n"
    content += f"Skills: {', '.join(profile_data.get('parsed_skills', []))}\n"
    content += f"Location: {profile_data.get('parsed_location', 'Paris')}\n"
    content += f"Languages: {', '.join(profile_data.get('parsed_languages', ['en']))}\n"
    content += f"Experience: {profile_data.get('parsed_seniority', 'mid')} level\n"

    file = ("test_profile.txt", io.BytesIO(content.encode()), "text/plain")
    response = client.post(
        "/api/profiles/upload",
        files={"file": file},
        headers=admin_headers,
    )
    return response


def create_mission(client: TestClient, admin_headers: dict, mission_data: dict) -> dict:
    """Helper to create a mission."""
    # Ensure description is long enough (min 10 chars)
    if "description" not in mission_data or len(mission_data.get("description", "")) < 10:
        mission_data["description"] = mission_data.get("description", "Test mission description")
    return client.post(
        "/api/missions",
        json=mission_data,
        headers=admin_headers,
    )


class TestMatchingEndpoint:
    """Tests for the POST /missions/{mission_id}/match endpoint."""

    def test_run_matching_success(self, client: TestClient, admin_headers: dict):
        """Test successful matching run."""
        # Create a profile via upload
        profile_response = create_profile_via_upload(
            client, admin_headers,
            {"full_name": "Test Dev", "parsed_skills": ["python"], "parsed_location": "paris"}
        )
        assert profile_response.status_code in [200, 201]

        # Create a mission
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Python Developer",
                "description": "Need Python developer with experience",
                "required_skills": ["python"],
                "required_language": "en",
                "required_location": "paris",
                "required_seniority": "mid",
            }
        )
        assert mission_response.status_code in [200, 201]
        mission_id = mission_response.json()["id"]

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
            create_profile_via_upload(
                client, admin_headers,
                {"full_name": f"Dev {i}", "parsed_skills": ["python"]}
            )

        # Create mission
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Python Dev",
                "description": "Test mission for matching profiles",
                "required_skills": ["python"],
            }
        )
        mission_id = mission_response.json()["id"]

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
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Test Mission",
                "description": "Test mission description here",
                "required_skills": ["python"],
            }
        )
        mission_id = mission_response.json()["id"]

        # Run matching (may have profiles from other tests)
        response = client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        # Should return valid response (empty or with existing profiles)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestListMatchesEndpoint:
    """Tests for the GET /missions/{mission_id}/matches endpoint."""

    def test_list_matches_success(self, client: TestClient, admin_headers: dict):
        """Test listing matches after running matching."""
        # Create profile
        create_profile_via_upload(
            client, admin_headers,
            {"full_name": "Match Test Dev", "parsed_skills": ["python"]}
        )

        # Create mission
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Match Test Mission",
                "description": "Test mission for matching",
                "required_skills": ["python"],
            }
        )
        mission_id = mission_response.json()["id"]

        # Run matching first
        client.post(f"/api/missions/{mission_id}/match", headers=admin_headers)

        # List matches
        response = client.get(f"/api/missions/{mission_id}/matches")

        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

    def test_list_matches_ordered_by_score(self, client: TestClient, admin_headers: dict):
        """Test that matches are ordered by score descending."""
        # Create profiles with different skills
        create_profile_via_upload(
            client, admin_headers,
            {"full_name": "Score Test Dev 1", "parsed_skills": ["python"]}
        )
        create_profile_via_upload(
            client, admin_headers,
            {"full_name": "Score Test Dev 2", "parsed_skills": ["java"]}
        )

        # Create mission requiring Python
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Score Test Mission",
                "description": "Need Python developer experience",
                "required_skills": ["python"],
            }
        )
        mission_id = mission_response.json()["id"]

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
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "No Matches Mission",
                "description": "Test mission for matching",
                "required_skills": ["python"],
            }
        )
        mission_id = mission_response.json()["id"]

        # List matches without running matching
        response = client.get(f"/api/missions/{mission_id}/matches")

        # Should return empty list (mission exists but no matches)
        assert response.status_code == 200
        assert response.json() == []


class TestMatchingWithFixtures:
    """Tests using fixture data."""

    def test_matching_with_fixture_data(
        self, client: TestClient, admin_headers: dict,
        profiles_fixture: list[dict], missions_fixture: list[dict]
    ):
        """Test matching using fixture data."""
        # Create one profile via upload
        profile_data = profiles_fixture[0]
        profile_content = f"{profile_data['full_name']}\n"
        profile_content += f"Skills: {', '.join(profile_data.get('parsed_skills', []))}\n"
        profile_content += f"Location: {profile_data.get('parsed_location', 'Paris')}\n"

        file = ("fixture_profile.txt", io.BytesIO(profile_content.encode()), "text/plain")
        create_profile = client.post(
            "/api/profiles/upload",
            files={"file": file},
            headers=admin_headers,
        )
        assert create_profile.status_code in [200, 201]

        # Create one mission
        mission_data = missions_fixture[0]
        create_mission_resp = create_mission(
            client, admin_headers,
            {
                "title": mission_data["title"],
                "description": mission_data["description"],
                "required_skills": mission_data.get("required_skills", []),
                "required_language": mission_data.get("required_language"),
                "required_location": mission_data.get("required_location"),
                "required_seniority": mission_data.get("required_seniority"),
            }
        )
        assert create_mission_resp.status_code in [200, 201]
        mission_id = create_mission_resp.json()["id"]

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
        profile_content = "Score Test Profile\nSkills: python, fastapi\nLocation: paris\n"
        file = ("score_profile.txt", io.BytesIO(profile_content.encode()), "text/plain")
        client.post(
            "/api/profiles/upload",
            files={"file": file},
            headers=admin_headers,
        )

        # Create mission
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Score Test Mission",
                "description": "Need Python FastAPI developer",
                "required_skills": ["python", "fastapi"],
                "required_language": "en",
                "required_location": "paris",
                "required_seniority": "mid",
            }
        )
        mission_id = mission_response.json()["id"]

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