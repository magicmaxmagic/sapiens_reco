"""Analytics schemas for dashboard statistics."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProfileStats(BaseModel):
    """Profile statistics."""
    total: int
    by_seniority: dict[str, int]
    by_skill: dict[str, int]
    created_last_7_days: int
    created_last_30_days: int


class MissionStats(BaseModel):
    """Mission statistics."""
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    open_positions: int
    created_last_7_days: int


class MatchStats(BaseModel):
    """Matching statistics."""
    total_matches: int
    average_score: float
    score_distribution: dict[str, int]  # e.g., {"0-20": 5, "20-40": 10, ...}
    top_matched_profiles: list[dict]


class DashboardStats(BaseModel):
    """Combined dashboard statistics."""
    profiles: ProfileStats
    missions: MissionStats
    matches: MatchStats
    recent_activity: list[dict]
    trends: dict  # {"profiles": [{"date": "...", "count": 5}, ...], ...}


class TimeSeriesDataPoint(BaseModel):
    """Single data point for time series."""
    date: datetime
    value: int | float


class TimeSeriesResponse(BaseModel):
    """Time series data response."""
    metric: str
    data: list[TimeSeriesDataPoint]
    granularity: str  # day, week, month