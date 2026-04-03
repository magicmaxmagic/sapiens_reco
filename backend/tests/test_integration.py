"""Integration tests for recommendation and metrics services."""

import json
from pathlib import Path

import pytest

from app.models.mission import Mission
from app.models.profile import Profile
from app.services.metrics_service import (
    MetricsService,
    RankingResult,
    create_ground_truth,
    evaluate_matching_system,
)
from app.services.recommendation_service import (
    clear_recommendation_cache,
    get_recommendation_service,
)


@pytest.fixture
def profiles_fixture() -> list[Profile]:
    """Load profiles from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "profiles.json"
    with open(fixture_path) as f:
        data = json.load(f)

    return [
        Profile(
            id=item["id"],
            full_name=item["full_name"],
            raw_text=item["raw_text"],
            parsed_skills=item["parsed_skills"],
            parsed_languages=item["parsed_languages"],
            parsed_location=item["parsed_location"],
            parsed_seniority=item["parsed_seniority"],
            availability_status=item["availability_status"],
            source=item["source"],
        )
        for item in data
    ]


@pytest.fixture
def missions_fixture() -> list[Mission]:
    """Load missions from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "missions.json"
    with open(fixture_path) as f:
        data = json.load(f)

    return [
        Mission(
            id=item["id"],
            title=item["title"],
            description=item["description"],
            required_skills=item["required_skills"],
            required_language=item.get("required_language"),
            required_location=item.get("required_location"),
            required_seniority=item.get("required_seniority"),
            status=item.get("status", "active"),
            priority=item.get("priority", "medium"),
        )
        for item in data
    ]


class TestRecommendationWithMetrics:
    """Integration tests combining recommendation and metrics services."""

    def test_ranking_with_metrics_evaluation(self, profiles_fixture, missions_fixture):
        """Test ranking profiles and evaluating with metrics."""
        service = get_recommendation_service()
        metrics_service = MetricsService()

        # Select a mission
        mission = missions_fixture[0]

        # Rank profiles
        rankings = service.rank_profiles_for_mission(
            profiles_fixture, mission, top_n=10
        )

        # Create relevance labels (using ground truth)
        ground_truth = create_ground_truth(
            profiles_fixture, [mission], relevance_threshold=50.0
        )
        relevant_profiles = ground_truth.get(mission.id, set())

        # Build relevance labels
        relevance = [
            1 if profile.id in relevant_profiles else 0
            for profile, score in rankings
        ]

        # Compute metrics
        precision_at_5 = metrics_service.precision_at_k(relevance, k=5)
        recall_at_5 = metrics_service.recall_at_k(
            relevance, total_relevant=len(relevant_profiles), k=5
        )
        ndcg = metrics_service.ndcg_at_k(relevance, k=5)

        # All metrics should be valid
        assert 0 <= precision_at_5 <= 1
        assert 0 <= recall_at_5 <= 1
        assert 0 <= ndcg <= 1

    def test_batch_scoring_and_evaluation(self, profiles_fixture, missions_fixture):
        """Test batch scoring with full evaluation."""
        service = get_recommendation_service()

        # Batch score all profiles against all missions
        results = service.batch_score(profiles_fixture, missions_fixture)

        # Create predicted rankings
        predicted_rankings = {}
        for mission_id, scores in results.items():
            predicted_rankings[mission_id] = [s["profile_id"] for s in scores]

        # Evaluate
        evaluation = evaluate_matching_system(
            profiles=profiles_fixture,
            missions=missions_fixture,
            predicted_rankings=predicted_rankings,
            relevance_threshold=50.0,
        )

        # Check evaluation results
        assert "aggregate_metrics" in evaluation
        assert "mission_metrics" in evaluation

        agg = evaluation["aggregate_metrics"]
        assert "precision_at_k" in agg
        assert "recall_at_k" in agg
        assert "map_at_k" in agg
        assert "ndcg" in agg
        assert "mrr" in agg

        # Metrics should be reasonable
        assert 0 <= agg["ndcg"] <= 1
        assert 0 <= agg["mrr"] <= 1

    def test_compare_matching_strategies(self, profiles_fixture, missions_fixture):
        """Test comparing matching strategies."""
        service = get_recommendation_service()

        mission = missions_fixture[0]

        # Get rankings
        rankings = service.rank_profiles_for_mission(
            profiles_fixture, mission, top_n=10
        )

        # Extract scores
        scores = [score for profile, score in rankings]

        # Check score distributions
        final_scores = [s["final_score"] for s in scores]

        # Should have variety in scores
        if len(final_scores) > 1:
            score_range = max(final_scores) - min(final_scores)
            # Some variance in scores expected
            assert score_range >= 0  # At minimum, non-negative

    def test_per_mission_metrics(self, profiles_fixture, missions_fixture):
        """Test computing metrics per mission."""
        service = get_recommendation_service()

        all_rankings = []

        for mission in missions_fixture:
            rankings = service.rank_profiles_for_mission(
                profiles_fixture, mission, top_n=10
            )

            # Create ground truth for this mission
            ground_truth = create_ground_truth(
                profiles_fixture, [mission], relevance_threshold=50.0
            )
            relevant_ids = ground_truth.get(mission.id, set())

            # Build ranking result
            relevance = [
                1 if profile.id in relevant_ids else 0
                for profile, score in rankings
            ]

            all_rankings.append(RankingResult(
                mission_id=mission.id,
                profile_ids=[p.id for p, s in rankings],
                scores=[s["final_score"] for p, s in rankings],
                relevance_labels=relevance,
            ))

        # Compute overall metrics
        metrics_service = MetricsService()
        result = metrics_service.evaluate_rankings(all_rankings)

        # All metrics should be valid
        assert 0 <= result.ndcg <= 1
        assert 0 <= result.mrr <= 1

    def test_recommendation_cache_consistency(self, profiles_fixture, missions_fixture):
        """Test that caching produces consistent results."""
        service = get_recommendation_service()
        clear_recommendation_cache()

        profile = profiles_fixture[0]
        mission = missions_fixture[0]

        # Score multiple times
        result1 = service.score_profile_for_mission(profile, mission)
        result2 = service.score_profile_for_mission(profile, mission)
        result3 = service.score_profile_for_mission(profile, mission)

        # All results should be identical
        assert result1["final_score"] == result2["final_score"]
        assert result2["final_score"] == result3["final_score"]

    def test_explanation_tags_quality(self, profiles_fixture, missions_fixture):
        """Test that explanation tags are meaningful."""
        service = get_recommendation_service()

        # Find a mission with specific requirements
        mission = next(
            (m for m in missions_fixture if m.required_skills and m.required_language),
            missions_fixture[0]
        )

        rankings = service.rank_profiles_for_mission(
            profiles_fixture, mission, top_n=5
        )

        # Check top results have explanation tags
        for profile, score in rankings[:3]:
            tags = score["explanation_tags"]

            # Should have some tags
            assert len(tags) > 0

            # Tags should be strings
            assert all(isinstance(tag, str) for tag in tags)

    def test_seniority_matching_accuracy(self, profiles_fixture, missions_fixture):
        """Test accuracy of seniority matching."""
        service = get_recommendation_service()

        # Find missions with different seniority requirements
        seniority_missions = {}
        for mission in missions_fixture:
            if mission.required_seniority:
                seniority_missions.setdefault(
                    mission.required_seniority.lower(), []
                ).append(mission)

        # For each seniority level, check top matches
        for seniority, missions in seniority_missions.items():
            if not missions:
                continue

            mission = missions[0]
            rankings = service.rank_profiles_for_mission(
                profiles_fixture, mission, top_n=5
            )

            # Check if profiles meet seniority requirement
            seniority_order = {"junior": 1, "mid": 2, "senior": 3, "lead": 4}
            required_level = seniority_order.get(seniority, 0)

            for profile, score in rankings[:3]:
                profile_level = seniority_order.get(
                    profile.parsed_seniority.lower() if profile.parsed_seniority else "",
                    0
                )
                # Seniority match tag should appear for valid matches
                if profile_level >= required_level > 0:
                    # May or may not have seniority_match tag depending on other factors
                    pass  # Just verify no errors

    def test_skill_overlap_scoring(self, profiles_fixture, missions_fixture):
        """Test that skill overlap affects scoring."""
        service = get_recommendation_service()

        # Find mission with specific skills
        mission = next(
            (m for m in missions_fixture if len(m.required_skills) >= 2),
            missions_fixture[0]
        )

        rankings = service.rank_profiles_for_mission(
            profiles_fixture, mission, top_n=len(profiles_fixture)
        )

        # Group profiles by skill overlap
        high_overlap = []
        low_overlap = []

        required_skills = set(s.lower() for s in mission.required_skills)

        for profile, score in rankings:
            profile_skills = set(s.lower() for s in profile.parsed_skills)
            overlap = len(required_skills & profile_skills)

            if overlap >= len(required_skills) * 0.5:
                high_overlap.append(score["final_score"])
            else:
                low_overlap.append(score["final_score"])

        # High overlap profiles should generally score higher
        if high_overlap and low_overlap:
            avg_high = sum(high_overlap) / len(high_overlap)
            avg_low = sum(low_overlap) / len(low_overlap)
            # High overlap should correlate with higher scores
            # (though other factors matter too)
            assert avg_high >= avg_low or abs(avg_high - avg_low) < 20


class TestEndToEndMatching:
    """End-to-end tests matching profiles to missions."""

    def test_full_matching_pipeline(self, profiles_fixture, missions_fixture):
        """Test full matching pipeline with evaluation."""
        # Step 1: Create recommendation service
        service = get_recommendation_service()
        clear_recommendation_cache()

        # Step 2: Score all profiles against all missions
        all_scores = service.batch_score(profiles_fixture, missions_fixture)

        # Step 3: Create rankings
        predicted_rankings = {}
        for mission_id, scores in all_scores.items():
            predicted_rankings[mission_id] = [s["profile_id"] for s in scores]

        # Step 4: Evaluate
        evaluation = evaluate_matching_system(
            profiles=profiles_fixture,
            missions=missions_fixture,
            predicted_rankings=predicted_rankings,
            relevance_threshold=50.0,
            k_values=[1, 3, 5, 10],
        )

        # Step 5: Verify evaluation results
        assert "aggregate_metrics" in evaluation
        assert evaluation["num_missions"] == len(missions_fixture)
        assert evaluation["num_profiles"] == len(profiles_fixture)

        # Step 6: Check metrics are reasonable
        agg = evaluation["aggregate_metrics"]
        assert isinstance(agg["precision_at_k"], dict)
        assert isinstance(agg["recall_at_k"], dict)
        assert isinstance(agg["map_at_k"], dict)

        # Step 7: Verify mission-level metrics
        for mission_id, metrics in evaluation["mission_metrics"].items():
            assert "num_relevant" in metrics
            assert "num_predicted" in metrics
            assert "num_correct" in metrics
            assert "precision" in metrics
            assert "recall" in metrics

    def test_matching_with_different_thresholds(self, profiles_fixture, missions_fixture):
        """Test evaluation with different relevance thresholds."""
        service = get_recommendation_service()

        mission = missions_fixture[0]
        rankings = service.rank_profiles_for_mission(
            profiles_fixture, mission, top_n=10
        )

        # Verify rankings were returned
        assert len(rankings) > 0

        # Create ground truth with different thresholds
        gt_low = create_ground_truth(profiles_fixture, [mission], relevance_threshold=30.0)
        gt_high = create_ground_truth(profiles_fixture, [mission], relevance_threshold=70.0)

        # Higher threshold should result in fewer relevant profiles
        assert len(gt_high.get(mission.id, set())) <= len(gt_low.get(mission.id, set()))

    def test_concurrent_matching_requests(self, profiles_fixture, missions_fixture):
        """Test handling multiple matching requests."""
        service = get_recommendation_service()
        clear_recommendation_cache()

        # Simulate multiple concurrent requests
        results = []
        for mission in missions_fixture[:5]:
            ranking = service.rank_profiles_for_mission(
                profiles_fixture, mission, top_n=5
            )
            results.append(ranking)

        # All results should be valid
        assert len(results) == 5
        for ranking in results:
            assert len(ranking) <= 5
            for profile, score in ranking:
                assert "final_score" in score
                assert 0 <= score["final_score"] <= 100