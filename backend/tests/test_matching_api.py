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
        profile_response = create_profile_via_upload(
            client, admin_headers,
            {"full_name": "Test Dev", "parsed_skills": ["python"], "parsed_location": "paris"}
        )
        assert profile_response.status_code in [200, 201]

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

        response = client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

        for result in results:
            assert "profile_id" in result
            assert "profile_name" in result
            assert "score" in result
            assert "skills_match" in result
            assert "seniority_match" in result
            assert "location_match" in result

    def test_run_matching_empty_profiles(self, client: TestClient, admin_headers: dict):
        """Test matching returns empty list when no skills match."""
        # Create a profile with different skills
        create_profile_via_upload(
            client, admin_headers,
            {"full_name": "Java Dev", "parsed_skills": ["java", "spring"]}
        )

        # Create a mission requiring skills that don't match
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Rust Developer",
                "description": "Need Rust developer",
                "required_skills": ["rust", "cargo"],
            }
        )
        mission_id = mission_response.json()["id"]

        response = client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        assert response.status_code == 200
        results = response.json()
        # All profiles should have score 0.0 since no skills match
        for result in results:
            assert result["skills_match"] == 0.0


class TestListMatchesEndpoint:
    """Tests for the GET /missions/{mission_id}/shortlist endpoint."""

    def test_list_matches_success(self, client: TestClient, admin_headers: dict):
        """Test listing matches after running matching."""
        create_profile_via_upload(
            client, admin_headers,
            {"full_name": "Dev 1", "parsed_skills": ["python"]}
        )

        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "Test Mission",
                "description": "Test mission description",
                "required_skills": ["python"],
            }
        )
        mission_id = mission_response.json()["id"]

        client.post(
            f"/api/missions/{mission_id}/match",
            headers=admin_headers,
        )

        response = client.get(
            f"/api/missions/{mission_id}/shortlist",
            headers=admin_headers,
        )

        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

    def test_list_matches_without_running(self, client: TestClient, admin_headers: dict):
        """Test listing matches without running matching first."""
        mission_response = create_mission(
            client, admin_headers,
            {
                "title": "No Match Mission",
                "description": "Mission with no matching run",
                "required_skills": ["python"],
            }
        )
        mission_id = mission_response.json()["id"]

        response = client.get(
            f"/api/missions/{mission_id}/shortlist",
            headers=admin_headers,
        )

        assert response.status_code == 404