"""Analytics schemas for dashboard statistics."""


from pydantic import BaseModel


class ProfileStats(BaseModel):
    """Profile statistics."""

    total: int
    active: int
    by_seniority: dict[str, int]
    by_availability: dict[str, int]
    recent_count: int


class MissionStats(BaseModel):
    """Mission statistics."""

    total: int
    active: int
    by_status: dict[str, int]
    recent_count: int


class MatchStats(BaseModel):
    """Match statistics."""

    total: int
    average_score: float
    score_distribution: dict[str, int]
    top_matched_profiles: list[dict[str, float | int]]


class TimeSeriesDataPoint(BaseModel):
    """Time series data point."""

    date: str
    count: int


class TimeSeriesResponse(BaseModel):
    """Time series response."""

    profiles: list[TimeSeriesDataPoint]
    missions: list[TimeSeriesDataPoint]


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    profiles: ProfileStats
    missions: MissionStats
    matches: MatchStats
    recent_activity: list[dict[str, str | int]]
    time_series: TimeSeriesResponse