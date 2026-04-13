"""Minimal debug endpoint for troubleshooting."""

from fastapi import APIRouter

router = APIRouter(tags=["debug"])


@router.get("/debug/ping")
def ping() -> dict:
    """Basic ping without any imports."""
    return {"status": "ok", "message": "pong"}


@router.get("/debug/info")
def info() -> dict:
    """Basic info with minimal imports."""
    import os
    import sys

    return {
        "status": "ok",
        "python_version": sys.version,
        "env_app_env": os.environ.get("APP_ENV", "NOT_SET"),
        "env_auth_required": os.environ.get("AUTH_REQUIRED", "NOT_SET"),
        "env_admin_password": "***SET***" if os.environ.get("ADMIN_PASSWORD") else "***NOT_SET***",
        "env_jwt_secret": "***SET***" if os.environ.get("JWT_SECRET_KEY") else "***NOT_SET***",
        "env_database_url": "***SET***" if os.environ.get("DATABASE_URL") else "***NOT_SET***",
    }