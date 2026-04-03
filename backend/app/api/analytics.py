"""Analytics API endpoints."""

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_auth
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import DashboardStats, TimeSeriesResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_auth),
) -> DashboardStats:
    """Get all dashboard statistics."""
    service = AnalyticsService(db)
    return service.get_dashboard_stats()


@router.get("/profiles", response_model=dict)
async def get_profile_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_auth),
) -> dict:
    """Get profile analytics."""
    service = AnalyticsService(db)
    return service.get_profile_stats().model_dump()


@router.get("/missions", response_model=dict)
async def get_mission_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_auth),
) -> dict:
    """Get mission analytics."""
    service = AnalyticsService(db)
    return service.get_mission_stats().model_dump()


@router.get("/matches", response_model=dict)
async def get_match_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_auth),
) -> dict:
    """Get matching analytics."""
    service = AnalyticsService(db)
    return service.get_match_stats().model_dump()


@router.get("/activity", response_model=list[dict])
async def get_recent_activity(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_auth),
) -> list[dict]:
    """Get recent activity feed."""
    service = AnalyticsService(db)
    return service.get_recent_activity(limit=limit)


@router.get("/trends", response_model=TimeSeriesResponse)
async def get_trends(
    metric: Literal["profiles", "missions", "matches"] = Query(default="profiles"),
    days: int = Query(default=30, le=90),
    granularity: Literal["day", "week", "month"] = Query(default="day"),
    db: Session = Depends(get_db),
    _: User = Depends(require_auth),
) -> TimeSeriesResponse:
    """Get time series trends."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    service = AnalyticsService(db)
    return service.get_time_series(metric, start_date, end_date, granularity)