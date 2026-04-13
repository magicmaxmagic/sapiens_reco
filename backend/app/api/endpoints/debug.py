"""Debug endpoint for troubleshooting."""

from fastapi import APIRouter

router = APIRouter(tags=["debug"])


@router.get("/debug/env")
def debug_env() -> dict:
    """Show environment variables (non-sensitive)."""
    import os
    from app.core.config import get_settings

    settings = get_settings()

    return {
        "app_env": settings.app_env,
        "auth_required": settings.auth_required,
        "admin_username": settings.admin_username,
        "admin_password_set": "***SET***" if settings.admin_password else "***NOT SET***",
        "jwt_secret_set": "***SET***" if settings.jwt_secret_key else "***NOT SET***",
        "database_url_set": "***SET***" if settings.database_url else "***NOT SET***",
        "auto_create_tables": settings.auto_create_tables,
        "allowed_origins": settings.allowed_origins,
    }


@router.get("/debug/health")
def debug_health() -> dict:
    """Basic health check without database."""
    return {"status": "ok", "message": "Backend is running"}