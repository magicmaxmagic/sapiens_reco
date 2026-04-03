from fastapi import APIRouter

from app.api.endpoints.audit import router as audit_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.matching import router as matching_router
from app.api.endpoints.missions import router as missions_router
from app.api.endpoints.notes import router as notes_router
from app.api.endpoints.profiles import router as profiles_router
from app.api.endpoints.search import router as search_router
from app.api.analytics import router as analytics_router
from app.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(audit_router)
api_router.include_router(profiles_router)
api_router.include_router(missions_router)
api_router.include_router(matching_router)
api_router.include_router(search_router)
api_router.include_router(notes_router)
api_router.include_router(analytics_router)
api_router.include_router(users_router)