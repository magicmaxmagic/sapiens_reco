from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/env")
def check_env():
    settings = get_settings()
    return {
        "admin_username": settings.admin_username,
        "admin_password_len": len(settings.admin_password) if settings.admin_password else 0,
        "admin_password_first_3": settings.admin_password[:3] if settings.admin_password else None,
    }
