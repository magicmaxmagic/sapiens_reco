import os


def test_login_success_returns_access_token(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": os.environ["ADMIN_USERNAME"],
            "password": os.environ["ADMIN_PASSWORD"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["expires_in"] > 0


def test_login_rejects_bad_password(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": os.environ["ADMIN_USERNAME"],
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_protected_write_requires_jwt(client):
    response = client.post(
        "/api/missions",
        json={
            "title": "Unauthorized Mission",
            "description": "This request should fail without auth",
            "required_skills": ["python"],
            "required_language": "fr",
            "required_location": "paris",
            "required_seniority": "mid",
            "desired_start_date": None,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Bearer token"
