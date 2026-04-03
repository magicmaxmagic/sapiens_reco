"""
Evaluation Metrics Service for Recommendation System.

This module provides standard information retrieval metrics for evaluating
profile-mission matching performance:

- Precision@k: Fraction of recommended items in top-k that are relevant
- Recall@k: Fraction of relevant items that appear in top-k recommendations
- MAP@k (Mean Average Precision): Average precision across all relevant items
- NDCG (Normalized Discounted Cumulative Gain): Measures ranking quality
- MRR (Mean Reciprocal Rank): Average of reciprocal ranks of relevant items
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from app.models.mission import Mission
    from app.models.profile import Profile


@dataclass
class RankingResult:
    """Result of ranking profiles for a mission."""

    mission_id: int
    profile_ids: list[int]
    scores: list[float]
    relevance_labels: list[int]  # 1 for relevant, 0 for not relevant


@dataclass
class MetricsResult:
    """Container for all computed metrics."""

    precision_at_k: dict[int, float]
    recall_at_k: dict[int, float]
    map_at_k: dict[int, float]
    ndcg: float
    mrr: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "map_at_k": self.map_at_k,
            "ndcg": round(self.ndcg, 4),
            "mrr": round(self.mrr, 4),
        }


class MetricsService:
    """Service for computing recommendation evaluation metrics."""

    def __init__(self, k_values: list[int] | None = None) -> None:
        """
        Initialize metrics service.

        Args:
            k_values: List of k values for @k metrics. Default: [1, 3, 5, 10]
        """
        self.k_values = k_values or [1, 3, 5, 10]

    @staticmethod
    def precision_at_k(relevance: list[int], k: int) -> float:
        """
        Compute Precision@k.

        Precision@k = (# of relevant items in top k) / k

        Args:
            relevance: Binary relevance labels for ranked items
            k: Number of top items to consider

        Returns:
            Precision@k score in [0, 1]
        """
        if k <= 0:
            return 0.0

        # Take top k items
        top_k = relevance[:k]
        relevant_count = sum(top_k)

        return relevant_count / k

    @staticmethod
    def recall_at_k(relevance: list[int], total_relevant: int, k: int) -> float:
        """
        Compute Recall@k.

        Recall@k = (# of relevant items in top k) / (total # of relevant items)

        Args:
            relevance: Binary relevance labels for ranked items
            total_relevant: Total number of relevant items in the dataset
            k: Number of top items to consider

        Returns:
            Recall@k score in [0, 1]
        """
        if total_relevant == 0 or k <= 0:
            return 0.0

        # Take top k items
        top_k = relevance[:k]
        relevant_in_top_k = sum(top_k)

        return relevant_in_top_k / total_relevant

    @staticmethod
    def average_precision(relevance: list[int]) -> float:
        """
        Compute Average Precision for a single query.

        AP = (1/R) * sum(Precision@k * rel(k) for k in ranked list)

        where R is the total number of relevant items.

        Args:
            relevance: Binary relevance labels for ranked items

        Returns:
            Average Precision in [0, 1]
        """
        # Find positions of relevant items
        relevant_positions = [i for i, rel in enumerate(relevance) if rel == 1]

        if not relevant_positions:
            return 0.0

        total_relevant = len(relevant_positions)
        precision_sum = 0.0

        for pos in relevant_positions:
            k = pos + 1  # 1-indexed position
            precision_at_k = sum(relevance[:k]) / k
            precision_sum += precision_at_k

        return precision_sum / total_relevant

    @staticmethod
    def mean_average_precision(all_relevance: list[list[int]]) -> float:
        """
        Compute Mean Average Precision across multiple queries.

        MAP = mean(AP for each query)

        Args:
            all_relevance: List of relevance lists, one per query

        Returns:
            MAP score in [0, 1]
        """
        if not all_relevance:
            return 0.0

        ap_scores = [
            MetricsService.average_precision(relevance)
            for relevance in all_relevance
        ]

        return np.mean(ap_scores)

    @staticmethod
    def dcg_at_k(relevance: list[int], k: int) -> float:
        """
        Compute Discounted Cumulative Gain at k.

        DCG@k = sum(rel_i / log2(i+1) for i in 1..k)

        Args:
            relevance: Relevance labels (can be binary or graded)
            k: Number of items to consider

        Returns:
            DCG@k score
        """
        dcg = 0.0
        for i, rel in enumerate(relevance[:k]):
            # Position is 1-indexed for DCG formula
            position = i + 1
            dcg += rel / np.log2(position + 1)

        return dcg

    @staticmethod
    def ndcg_at_k(relevance: list[int], k: int) -> float:
        """
        Compute Normalized Discounted Cumulative Gain at k.

        NDCG@k = DCG@k / IDCG@k

        where IDCG@k is the DCG of the ideal ranking (all relevant items first).

        Args:
            relevance: Relevance labels for ranked items
            k: Number of items to consider

        Returns:
            NDCG@k score in [0, 1]
        """
        dcg = MetricsService.dcg_at_k(relevance, k)

        # Ideal ranking: all relevant items first
        ideal_relevance = sorted(relevance, reverse=True)
        idcg = MetricsService.dcg_at_k(ideal_relevance, k)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    @staticmethod
    def reciprocal_rank(relevance: list[int]) -> float:
        """
        Compute Reciprocal Rank for a single query.

        RR = 1 / rank of first relevant item

        If no relevant item exists, returns 0.

        Args:
            relevance: Binary relevance labels for ranked items

        Returns:
            Reciprocal Rank in [0, 1]
        """
        for i, rel in enumerate(relevance):
            if rel == 1:
                return 1.0 / (i + 1)  # 1-indexed rank

        return 0.0

    @staticmethod
    def mean_reciprocal_rank(all_relevance: list[list[int]]) -> float:
        """
        Compute Mean Reciprocal Rank across multiple queries.

        MRR = mean(RR for each query)

        Args:
            all_relevance: List of relevance lists, one per query

        Returns:
            MRR score in [0, 1]
        """
        if not all_relevance:
            return 0.0

        rr_scores = [
            MetricsService.reciprocal_rank(relevance)
            for relevance in all_relevance
        ]

        return np.mean(rr_scores)

    def compute_all_metrics(
        self,
        all_relevance: list[list[int]],
        k_values: list[int] | None = None,
    ) -> MetricsResult:
        """
        Compute all evaluation metrics.

        Args:
            all_relevance: List of relevance lists, one per query/mission
            k_values: Override default k values

        Returns:
            MetricsResult with all computed metrics
        """
        k_vals = k_values or self.k_values

        # Compute metrics at each k
        precision_at_k = {}
        recall_at_k = {}
        map_at_k = {}

        for k in k_vals:
            # Precision@k - average across all queries
            precisions = [
                self.precision_at_k(rel, k) for rel in all_relevance
            ]
            precision_at_k[k] = round(float(np.mean(precisions)), 4)

            # Recall@k - need total relevant for each query
            recalls = []
            for rel in all_relevance:
                total_relevant = sum(rel)
                recalls.append(self.recall_at_k(rel, total_relevant, k))
            recall_at_k[k] = round(float(np.mean(recalls)), 4)

            # MAP@k
            map_at_k[k] = round(
                self.mean_average_precision([r[:k] for r in all_relevance]),
                4,
            )

        # NDCG - average across queries at max k
        max_k = max(k_vals)
        ndcg_scores = [
            self.ndcg_at_k(rel, max_k) for rel in all_relevance
        ]
        ndcg = float(np.mean(ndcg_scores))

        # MRR
        mrr = self.mean_reciprocal_rank(all_relevance)

        return MetricsResult(
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            map_at_k=map_at_k,
            ndcg=ndcg,
            mrr=mrr,
        )

    def evaluate_rankings(
        self,
        rankings: list[RankingResult],
    ) -> MetricsResult:
        """
        Evaluate multiple ranking results.

        Args:
            rankings: List of RankingResult objects

        Returns:
            MetricsResult with computed metrics
        """
        all_relevance = [r.relevance_labels for r in rankings]
        return self.compute_all_metrics(all_relevance)


def create_ground_truth(
    profiles: list[Profile],
    missions: list[Mission],
    relevance_threshold: float = 60.0,
    score_function: callable | None = None,
) -> dict[int, set[int]]:
    """
    Create ground truth relevance mapping from profiles to missions.

    A profile is considered relevant to a mission if the matching score
    exceeds the threshold.

    Args:
        profiles: List of profiles
        missions: List of missions
        relevance_threshold: Minimum score to consider a match relevant
        score_function: Optional custom scoring function

    Returns:
        Dict mapping mission_id to set of relevant profile_ids
    """
    from app.services.matching_service import score_profile_for_mission

    ground_truth: dict[int, set[int]] = {}

    for mission in missions:
        relevant_profiles = set()
        for profile in profiles:
            # Use provided score function or default matching
            if score_function:
                score = score_function(profile, mission)
            else:
                score = score_profile_for_mission(mission, profile)

            if score["final_score"] >= relevance_threshold:
                relevant_profiles.add(profile.id)

        ground_truth[mission.id] = relevant_profiles

    return ground_truth


def evaluate_matching_system(
    profiles: list[Profile],
    missions: list[Mission],
    predicted_rankings: dict[int, list[int]],
    ground_truth: dict[int, set[int]] | None = None,
    relevance_threshold: float = 60.0,
    k_values: list[int] | None = None,
) -> dict:
    """
    Evaluate the matching system with standard IR metrics.

    Args:
        profiles: List of all profiles
        missions: List of all missions
        predicted_rankings: Dict mapping mission_id to list of ranked profile_ids
        ground_truth: Optional pre-computed ground truth
        relevance_threshold: Threshold for relevance if computing ground truth
        k_values: k values for @k metrics

    Returns:
        Dictionary with all evaluation metrics
    """
    metrics_service = MetricsService(k_values)

    # Compute ground truth if not provided
    if ground_truth is None:
        ground_truth = create_ground_truth(profiles, missions, relevance_threshold)

    # Build relevance lists for each mission
    all_relevance: list[list[int]] = []
    mission_metrics: dict[int, dict] = {}

    for mission in missions:
        mission_id = mission.id
        relevant_profiles = ground_truth.get(mission_id, set())

        # Get predicted ranking for this mission
        predicted = predicted_rankings.get(mission_id, [])

        # Build relevance list: 1 if profile is relevant, 0 otherwise
        relevance = [
            1 if profile_id in relevant_profiles else 0
            for profile_id in predicted
        ]

        all_relevance.append(relevance)

        # Compute per-mission metrics
        mission_metrics[mission_id] = {
            "num_relevant": len(relevant_profiles),
            "num_predicted": len(predicted),
            "num_correct": sum(relevance),
            "precision": (
                sum(relevance) / len(predicted) if predicted else 0.0
            ),
            "recall": (
                sum(relevance) / len(relevant_profiles)
                if relevant_profiles else 0.0
            ),
        }

    # Compute aggregate metrics
    aggregate_metrics = metrics_service.compute_all_metrics(all_relevance)

    return {
        "aggregate_metrics": aggregate_metrics.to_dict(),
        "mission_metrics": mission_metrics,
        "num_missions": len(missions),
        "num_profiles": len(profiles),
        "config": {
            "relevance_threshold": relevance_threshold,
            "k_values": k_values or [1, 3, 5, 10],
        },
    }


class MetricsTracker:
    """Track metrics over time for monitoring."""

    def __init__(self) -> None:
        self._history: list[dict] = []

    def record(self, metrics: dict, timestamp: str | None = None) -> None:
        """Record a metrics snapshot."""
        from datetime import datetime

        snapshot = {
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "metrics": metrics,
        }
        self._history.append(snapshot)

    def get_history(self, limit: int | None = None) -> list[dict]:
        """Get metrics history."""
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def get_trend(self, metric_name: str) -> list[float]:
        """Get trend for a specific metric."""
        trend = []
        for snapshot in self._history:
            # Navigate nested metrics
            value = snapshot.get("metrics", {})
            for key in metric_name.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    break
            if isinstance(value, (int, float)):
                trend.append(value)
        return trend

    def get_average(self, metric_name: str, window: int = 10) -> float:
        """Get rolling average for a metric."""
        trend = self.get_trend(metric_name)[-window:]
        return float(np.mean(trend)) if trend else 0.0


# Singleton metrics tracker
_metrics_tracker: MetricsTracker | None = None


def get_metrics_tracker() -> MetricsTracker:
    """Get or create the singleton metrics tracker."""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = MetricsTracker()
    return _metrics_tracker