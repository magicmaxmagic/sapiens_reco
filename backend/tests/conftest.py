import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("AUTH_REQUIRED", "true")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("AUDIT_LOG_PATH", "./test_audit.jsonl")
os.environ.setdefault("AUDIT_EXPORT_MAX_LINES", "500")

from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _cleanup_test_audit_log() -> None:
    audit_file = Path("./test_audit.jsonl")
    if audit_file.exists():
        audit_file.unlink()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={
            "username": os.environ["ADMIN_USERNAME"],
            "password": os.environ["ADMIN_PASSWORD"],
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
