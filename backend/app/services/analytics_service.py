"""Analytics service for dashboard statistics."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
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
    """Service for dashboard analytics."""

    def __init__(self, db: Session):
        self.db = db

    def get_profile_stats(self) -> ProfileStats:
        """Get profile statistics."""
        total = self.db.query(func.count(Profile.id)).scalar() or 0
        active = self.db.query(func.count(Profile.id)).filter(
            Profile.is_active == True  # noqa: E712
        ).scalar() or 0

        # Group by seniority
        seniority_counts = (
            self.db.query(
                Profile.parsed_seniority, func.count(Profile.id)
            )
            .group_by(Profile.parsed_seniority)
            .all()
        )
        by_seniority = {s or "unknown": c for s, c in seniority_counts}

        # Group by availability
        availability_counts = (
            self.db.query(Profile.availability_status, func.count(Profile.id))
            .group_by(Profile.availability_status)
            .all()
        )
        by_availability = {s: c for s, c in availability_counts}

        # Recent profiles (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = (
            self.db.query(func.count(Profile.id))
            .filter(Profile.created_at >= week_ago)
            .scalar() or 0
        )

        return ProfileStats(
            total=total,
            active=active,
            by_seniority=by_seniority,
            by_availability=by_availability,
            recent_count=recent_count,
        )

    def get_mission_stats(self) -> MissionStats:
        """Get mission statistics."""
        total = self.db.query(func.count(Mission.id)).scalar() or 0
        active = self.db.query(func.count(Mission.id)).filter(
            Mission.is_active == True  # noqa: E712
        ).scalar() or 0

        # Group by status
        status_counts = (
            self.db.query(Mission.status, func.count(Mission.id))
            .group_by(Mission.status)
            .all()
        )
        by_status = {s or "draft": c for s, c in status_counts}

        # Recent missions (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = (
            self.db.query(func.count(Mission.id))
            .filter(Mission.created_at >= week_ago)
            .scalar() or 0
        )

        return MissionStats(
            total=total,
            active=active,
            by_status=by_status,
            recent_count=recent_count,
        )

    def get_match_stats(self) -> MatchStats:
        """Get match statistics."""
        total = self.db.query(func.count(MatchResult.id)).scalar() or 0

        # Average score
        avg_score = self.db.query(func.avg(MatchResult.final_score)).scalar() or 0.0

        # Score distribution (buckets)
        score_distribution = {}
        for low, high in [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]:
            count = (
                self.db.query(func.count(MatchResult.id))
                .filter(
                    MatchResult.final_score >= low,
                    MatchResult.final_score < high
                )
                .scalar() or 0
            )
            score_distribution[f"{low}-{high}"] = count

        # Top matched profiles
        top_profiles = (
            self.db.query(
                MatchResult.profile_id,
                func.avg(MatchResult.final_score).label("avg_score"),
                func.count(MatchResult.id).label("match_count"),
            )
            .group_by(MatchResult.profile_id)
            .order_by(func.avg(MatchResult.final_score).desc())
            .limit(10)
            .all()
        )

        top_matched_profiles = [
            {
                "profile_id": str(p.profile_id),
                "avg_score": round(p.avg_score or 0, 2),
                "matches": p.match_count,
            }
            for p in top_profiles
        ]

        return MatchStats(
            total=total,
            average_score=round(avg_score, 2),
            score_distribution=score_distribution,
            top_matched_profiles=top_matched_profiles,
        )

    def get_time_series(self, days: int = 30) -> TimeSeriesResponse:
        """Get time series data for charts."""
        start_date = datetime.utcnow() - timedelta(days=days)

        # Profile counts by date
        profile_counts = (
            self.db.query(
                func.date(Profile.created_at).label("date"),
                func.count(Profile.id).label("count"),
            )
            .filter(Profile.created_at >= start_date)
            .group_by(func.date(Profile.created_at))
            .all()
        )

        # Mission counts by date
        mission_counts = (
            self.db.query(
                func.date(Mission.created_at).label("date"),
                func.count(Mission.id).label("count"),
            )
            .filter(Mission.created_at >= start_date)
            .group_by(func.date(Mission.created_at))
            .all()
        )

        # Convert to dict for easier lookup
        profile_dict = {str(p.date): p.count for p in profile_counts}
        mission_dict = {str(m.date): m.count for m in mission_counts}

        # Fill in missing dates
        profiles = []
        missions = []
        current_date = start_date
        while current_date <= datetime.utcnow():
            date_str = str(current_date.date())
            profiles.append(
                TimeSeriesDataPoint(date=date_str, count=profile_dict.get(date_str, 0))
            )
            missions.append(
                TimeSeriesDataPoint(date=date_str, count=mission_dict.get(date_str, 0))
            )
            current_date += timedelta(days=1)

        return TimeSeriesResponse(profiles=profiles, missions=missions)

    def get_recent_activity(self, limit: int = 10) -> list[dict[str, Any]]:
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
                "user_id": str(log.user_id) if log.user_id else None,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in recent
        ]

    def get_dashboard_stats(self) -> DashboardStats:
        """Get all dashboard statistics."""
        return DashboardStats(
            profiles=self.get_profile_stats(),
            missions=self.get_mission_stats(),
            matches=self.get_match_stats(),
            recent_activity=self.get_recent_activity(),
            time_series=self.get_time_series(),
        )