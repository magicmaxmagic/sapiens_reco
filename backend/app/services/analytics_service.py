"""Analytics service for dashboard statistics."""

from datetime import datetime, timedelta
from collections import Counter
from typing import Any
from uuid import UUID

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction
from app.models.match_result import MatchResult
from app.models.mission import Mission
from app.models.profile import Profile
from app.schemas.analytics import (
    DashboardStats,
    MatchStats,
    MissionStats,
    ProfileStats,
    TimeSeriesDataPoint,
    TimeSeriesResponse,
)


class AnalyticsService:
    """Service for analytics and statistics."""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self) -> DashboardStats:
        """Get all dashboard statistics."""
        return DashboardStats(
            profiles=self.get_profile_stats(),
            missions=self.get_mission_stats(),
            matches=self.get_match_stats(),
            recent_activity=self.get_recent_activity(),
            trends=self.get_trends(),
        )

    def get_profile_stats(self) -> ProfileStats:
        """Get profile statistics."""
        # Total profiles
        total = self.db.query(func.count(Profile.id)).scalar() or 0

        # By seniority
        seniority_counts = (
            self.db.query(Profile.parsed_seniority, func.count(Profile.id))
            .filter(Profile.parsed_seniority.isnot(None))
            .group_by(Profile.parsed_seniority)
            .all()
        )
        by_seniority = {s or "unknown": c for s, c in seniority_counts}

        # By skill (top 10)
        # This would need a more complex query if skills are stored as JSON
        by_skill: dict[str, int] = {}

        # Created in last 7/30 days
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        created_last_7_days = (
            self.db.query(func.count(Profile.id))
            .filter(Profile.created_at >= week_ago)
            .scalar() or 0
        )
        created_last_30_days = (
            self.db.query(func.count(Profile.id))
            .filter(Profile.created_at >= month_ago)
            .scalar() or 0
        )

        return ProfileStats(
            total=total,
            by_seniority=by_seniority,
            by_skill=by_skill,
            created_last_7_days=created_last_7_days,
            created_last_30_days=created_last_30_days,
        )

    def get_mission_stats(self) -> MissionStats:
        """Get mission statistics."""
        # Total missions
        total = self.db.query(func.count(Mission.id)).scalar() or 0

        # By status (if status field exists)
        by_status: dict[str, int] = {"open": total}  # Simplified

        # By priority (if priority field exists)
        by_priority: dict[str, int] = {}

        # Open positions
        open_positions = total  # Simplified

        # Created in last 7 days
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        created_last_7_days = (
            self.db.query(func.count(Mission.id))
            .filter(Mission.created_at >= week_ago)
            .scalar() or 0
        )

        return MissionStats(
            total=total,
            by_status=by_status,
            by_priority=by_priority,
            open_positions=open_positions,
            created_last_7_days=created_last_7_days,
        )

    def get_match_stats(self) -> MatchStats:
        """Get matching statistics."""
        # Total matches
        total_matches = self.db.query(func.count(MatchResult.id)).scalar() or 0

        # Average score
        avg_score = (
            self.db.query(func.avg(MatchResult.score))
            .filter(MatchResult.score.isnot(None))
            .scalar() or 0.0
        )

        # Score distribution (0-20, 20-40, 40-60, 60-80, 80-100)
        score_ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        score_distribution = {}
        for low, high in score_ranges:
            count = (
                self.db.query(func.count(MatchResult.id))
                .filter(and_(MatchResult.score >= low, MatchResult.score < high))
                .scalar() or 0
            )
            score_distribution[f"{low}-{high}"] = count

        # Top matched profiles
        top_profiles = (
            self.db.query(
                MatchResult.profile_id,
                func.avg(MatchResult.score).label("avg_score"),
                func.count(MatchResult.id).label("match_count"),
            )
            .group_by(MatchResult.profile_id)
            .order_by(func.avg(MatchResult.score).desc())
            .limit(5)
            .all()
        )

        top_matched_profiles = [
            {"profile_id": str(p.profile_id), "avg_score": round(p.avg_score or 0, 2), "matches": p.match_count}
            for p in top_profiles
        ]

        return MatchStats(
            total_matches=total_matches,
            average_score=round(avg_score, 2),
            score_distribution=score_distribution,
            top_matched_profiles=top_matched_profiles,
        )

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        """Get recent activity feed."""
        recent = (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(log.id),
                "action": log.action.value,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "user_id": str(log.user_id) if log.user_id else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in recent
        ]

    def get_trends(self, days: int = 30) -> dict:
        """Get time series trends."""
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)

        # Profiles created over time
        profile_trend = self._get_time_series(Profile.created_at, start_date, now)

        # Missions created over time
        mission_trend = self._get_time_series(Mission.created_at, start_date, now)

        # Matches created over time
        match_trend = self._get_time_series(MatchResult.created_at, start_date, now)

        return {
            "profiles": profile_trend,
            "missions": mission_trend,
            "matches": match_trend,
        }

    def _get_time_series(
        self,
        date_field: Any,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Get time series data for a model."""
        # Group by date
        results = (
            self.db.query(
                func.date(date_field).label("date"),
                func.count().label("count"),
            )
            .filter(date_field >= start_date, date_field <= end_date)
            .group_by(func.date(date_field))
            .order_by(func.date(date_field))
            .all()
        )

        return [
            {"date": str(r.date), "count": r.count}
            for r in results
        ]

    def get_time_series(
        self,
        metric: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "day",
    ) -> TimeSeriesResponse:
        """Get time series data for a specific metric."""
        model_map = {
            "profiles": Profile,
            "missions": Mission,
            "matches": MatchResult,
        }

        if metric not in model_map:
            raise ValueError(f"Unknown metric: {metric}")

        model = model_map[metric]
        date_field = model.created_at

        # Determine grouping based on granularity
        if granularity == "week":
            date_trunc = func.date_trunc("week", date_field)
        elif granularity == "month":
            date_trunc = func.date_trunc("month", date_field)
        else:
            date_trunc = func.date(date_field)

        results = (
            self.db.query(
                date_trunc.label("date"),
                func.count().label("value"),
            )
            .filter(date_field >= start_date, date_field <= end_date)
            .group_by(date_trunc)
            .order_by(date_trunc)
            .all()
        )

        return TimeSeriesResponse(
            metric=metric,
            data=[TimeSeriesDataPoint(date=r.date, value=r.value) for r in results],
            granularity=granularity,
        )