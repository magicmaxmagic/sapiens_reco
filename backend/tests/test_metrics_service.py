"""Tests for the metrics evaluation service."""

import pytest

from app.services.metrics_service import (
    MetricsResult,
    MetricsService,
    MetricsTracker,
    RankingResult,
    create_ground_truth,
    evaluate_matching_system,
    get_metrics_tracker,
)


class TestPrecisionAtK:
    """Tests for Precision@k metric."""

    def test_perfect_precision(self):
        """Test precision when all items are relevant."""
        relevance = [1, 1, 1, 1, 1]
        precision = MetricsService.precision_at_k(relevance, k=5)

        assert precision == 1.0

    def test_zero_precision(self):
        """Test precision when no items are relevant."""
        relevance = [0, 0, 0, 0, 0]
        precision = MetricsService.precision_at_k(relevance, k=5)

        assert precision == 0.0

    def test_half_precision(self):
        """Test precision when half of items are relevant."""
        relevance = [1, 0, 1, 0, 1]
        precision = MetricsService.precision_at_k(relevance, k=5)

        assert precision == 0.6

    def test_precision_at_k_less_than_list(self):
        """Test precision when k is smaller than list size."""
        relevance = [1, 1, 0, 0, 0]
        precision_k3 = MetricsService.precision_at_k(relevance, k=3)
        precision_k5 = MetricsService.precision_at_k(relevance, k=5)

        assert precision_k3 == pytest.approx(2 / 3)
        assert precision_k5 == 0.4

    def test_precision_empty_list(self):
        """Test precision with empty list."""
        precision = MetricsService.precision_at_k([], k=5)

        assert precision == 0.0

    def test_precision_zero_k(self):
        """Test precision with k=0."""
        precision = MetricsService.precision_at_k([1, 1, 1], k=0)

        assert precision == 0.0


class TestRecallAtK:
    """Tests for Recall@k metric."""

    def test_perfect_recall(self):
        """Test recall when all relevant items are in top k."""
        relevance = [1, 1, 1, 0, 0]
        recall = MetricsService.recall_at_k(relevance, total_relevant=3, k=5)

        assert recall == 1.0

    def test_partial_recall(self):
        """Test recall when only some relevant items are in top k."""
        relevance = [1, 1, 0, 0, 0]  # Only 2 of 5 relevant in top 5
        recall = MetricsService.recall_at_k(relevance, total_relevant=5, k=5)

        assert recall == pytest.approx(2 / 5)

    def test_zero_recall(self):
        """Test recall when no relevant items in top k."""
        relevance = [0, 0, 0, 1, 1]  # Relevant items at positions 4 and 5
        recall = MetricsService.recall_at_k(relevance, total_relevant=2, k=3)

        assert recall == 0.0

    def test_recall_k_smaller_than_relevant(self):
        """Test recall when k is smaller than number of relevant items."""
        relevance = [1, 1, 1, 0, 0]
        recall = MetricsService.recall_at_k(relevance, total_relevant=10, k=3)

        assert recall == pytest.approx(3 / 10)

    def test_recall_zero_total_relevant(self):
        """Test recall when there are no relevant items."""
        recall = MetricsService.recall_at_k([0, 0, 0], total_relevant=0, k=3)

        assert recall == 0.0


class TestAveragePrecision:
    """Tests for Average Precision metric."""

    def test_perfect_ap(self):
        """Test AP when all relevant items are at top."""
        relevance = [1, 1, 1, 0, 0]
        ap = MetricsService.average_precision(relevance)

        assert ap == 1.0

    def test_ap_with_interleaved_relevant(self):
        """Test AP with relevant items interleaved."""
        relevance = [1, 0, 1, 0, 1]  # 3 relevant at positions 1, 3, 5
        ap = MetricsService.average_precision(relevance)

        # P@1 = 1/1, P@3 = 2/3, P@5 = 3/5
        # AP = (1 + 2/3 + 3/5) / 3
        expected = (1.0 + 2/3 + 3/5) / 3
        assert ap == pytest.approx(expected)

    def test_ap_no_relevant_items(self):
        """Test AP when no items are relevant."""
        relevance = [0, 0, 0, 0, 0]
        ap = MetricsService.average_precision(relevance)

        assert ap == 0.0

    def test_ap_single_relevant_at_start(self):
        """Test AP with single relevant item at start."""
        relevance = [1, 0, 0, 0, 0]
        ap = MetricsService.average_precision(relevance)

        assert ap == 1.0

    def test_ap_single_relevant_at_end(self):
        """Test AP with single relevant item at end."""
        relevance = [0, 0, 0, 0, 1]
        ap = MetricsService.average_precision(relevance)

        # Only 1 relevant at position 5
        # AP = P@5 / 1 = 1/5 = 0.2
        assert ap == pytest.approx(0.2)


class TestMeanAveragePrecision:
    """Tests for Mean Average Precision metric."""

    def test_map_perfect(self):
        """Test MAP with perfect rankings."""
        all_relevance = [
            [1, 1, 1, 0, 0],
            [1, 1, 1, 0, 0],
            [1, 1, 1, 0, 0],
        ]
        map_score = MetricsService.mean_average_precision(all_relevance)

        assert map_score == 1.0

    def test_map_mixed_quality(self):
        """Test MAP with mixed quality rankings."""
        all_relevance = [
            [1, 1, 1, 0, 0],  # AP = 1.0
            [1, 0, 1, 0, 1],  # AP ≈ 0.56
            [0, 0, 0, 0, 0],  # AP = 0.0
        ]
        map_score = MetricsService.mean_average_precision(all_relevance)

        # Should be average of the APs
        assert 0.4 < map_score < 0.7

    def test_map_empty(self):
        """Test MAP with empty input."""
        map_score = MetricsService.mean_average_precision([])

        assert map_score == 0.0


class TestDCGAndNDCG:
    """Tests for DCG and NDCG metrics."""

    def test_dcg_perfect_ordering(self):
        """Test DCG with relevant items first."""
        relevance = [1, 1, 1, 0, 0]
        dcg = MetricsService.dcg_at_k(relevance, k=5)

        # DCG = 1/log2(2) + 1/log2(3) + 1/log2(4)
        expected = 1/1 + 1/1.585 + 1/2
        assert dcg == pytest.approx(expected, rel=0.01)

    def test_dcg_with_graded_relevance(self):
        """Test DCG with graded relevance scores."""
        relevance = [3, 2, 1, 0, 0]  # Graded relevance
        dcg = MetricsService.dcg_at_k(relevance, k=5)

        # Higher relevance should contribute more
        assert dcg > MetricsService.dcg_at_k([1, 1, 1, 0, 0], k=5)

    def test_ndcg_perfect(self):
        """Test NDCG with perfect ordering."""
        relevance = [1, 1, 1, 0, 0]
        ndcg = MetricsService.ndcg_at_k(relevance, k=5)

        # Perfect ordering means DCG = IDCG
        assert ndcg == 1.0

    def test_ndcg_imperfect(self):
        """Test NDCG with suboptimal ordering."""
        relevance = [0, 0, 1, 1, 1]  # Relevant items at end
        ndcg = MetricsService.ndcg_at_k(relevance, k=5)

        # Imperfect ordering should give NDCG < 1
        assert 0 < ndcg < 1

    def test_ndcg_no_relevant_items(self):
        """Test NDCG with no relevant items."""
        relevance = [0, 0, 0, 0, 0]
        ndcg = MetricsService.ndcg_at_k(relevance, k=5)

        assert ndcg == 0.0

    def test_ndcg_k_smaller_than_list(self):
        """Test NDCG with k smaller than list size."""
        relevance = [1, 0, 1, 0, 1, 0, 1, 0]
        ndcg_k4 = MetricsService.ndcg_at_k(relevance, k=4)
        ndcg_k8 = MetricsService.ndcg_at_k(relevance, k=8)

        # Both should be valid
        assert 0 < ndcg_k4 <= 1
        assert 0 < ndcg_k8 <= 1


class TestReciprocalRank:
    """Tests for Reciprocal Rank metric."""

    def test_rr_first_position(self):
        """Test RR when relevant item is first."""
        relevance = [1, 0, 0, 0, 0]
        rr = MetricsService.reciprocal_rank(relevance)

        assert rr == 1.0

    def test_rr_second_position(self):
        """Test RR when relevant item is second."""
        relevance = [0, 1, 0, 0, 0]
        rr = MetricsService.reciprocal_rank(relevance)

        assert rr == 0.5

    def test_rr_fifth_position(self):
        """Test RR when relevant item is fifth."""
        relevance = [0, 0, 0, 0, 1]
        rr = MetricsService.reciprocal_rank(relevance)

        assert rr == 0.2

    def test_rr_no_relevant_items(self):
        """Test RR when no relevant items exist."""
        relevance = [0, 0, 0, 0, 0]
        rr = MetricsService.reciprocal_rank(relevance)

        assert rr == 0.0


class TestMeanReciprocalRank:
    """Tests for Mean Reciprocal Rank metric."""

    def test_mrr_perfect(self):
        """Test MRR with all relevant items at first position."""
        all_relevance = [
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
        ]
        mrr = MetricsService.mean_reciprocal_rank(all_relevance)

        assert mrr == 1.0

    def test_mrr_mixed(self):
        """Test MRR with mixed positions."""
        all_relevance = [
            [1, 0, 0],  # RR = 1.0
            [0, 1, 0],  # RR = 0.5
            [0, 0, 1],  # RR = 0.33
        ]
        mrr = MetricsService.mean_reciprocal_rank(all_relevance)

        expected = (1.0 + 0.5 + 0.33) / 3
        assert mrr == pytest.approx(expected, rel=0.1)

    def test_mrr_empty(self):
        """Test MRR with empty input."""
        mrr = MetricsService.mean_reciprocal_rank([])

        assert mrr == 0.0


class TestMetricsServiceComputeAll:
    """Tests for compute_all_metrics method."""

    def test_compute_all_metrics(self):
        """Test computing all metrics together."""
        service = MetricsService()
        all_relevance = [
            [1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0],
            [0, 1, 1, 0, 0],
        ]

        result = service.compute_all_metrics(all_relevance)

        assert isinstance(result, MetricsResult)
        assert "1" in result.precision_at_k or 1 in result.precision_at_k
        assert "ndcg" in result.to_dict()
        assert "mrr" in result.to_dict()

    def test_compute_with_custom_k_values(self):
        """Test computing metrics with custom k values."""
        service = MetricsService(k_values=[1, 5, 10])
        all_relevance = [
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        ]

        result = service.compute_all_metrics(all_relevance, k_values=[2, 4])

        # Should use custom k_values, not defaults
        assert 2 in result.precision_at_k
        assert 4 in result.precision_at_k


class TestMetricsTracker:
    """Tests for MetricsTracker."""

    def test_record_and_retrieve(self):
        """Test recording and retrieving metrics."""
        tracker = MetricsTracker()

        metrics1 = {"ndcg": 0.8, "mrr": 0.75}
        metrics2 = {"ndcg": 0.85, "mrr": 0.80}

        tracker.record(metrics1, "2024-01-01")
        tracker.record(metrics2, "2024-01-02")

        history = tracker.get_history()
        assert len(history) == 2
        assert history[0]["metrics"] == metrics1
        assert history[1]["metrics"] == metrics2

    def test_get_history_limit(self):
        """Test retrieving limited history."""
        tracker = MetricsTracker()

        for i in range(10):
            tracker.record({"ndcg": i / 10})

        history = tracker.get_history(limit=5)
        assert len(history) == 5
        # Should get last 5
        assert history[0]["metrics"]["ndcg"] == 0.5

    def test_get_trend(self):
        """Test getting trend for specific metric."""
        tracker = MetricsTracker()

        tracker.record({"aggregate_metrics": {"ndcg": 0.7}})
        tracker.record({"aggregate_metrics": {"ndcg": 0.75}})
        tracker.record({"aggregate_metrics": {"ndcg": 0.80}})

        trend = tracker.get_trend("aggregate_metrics.ndcg")

        assert len(trend) == 3
        assert trend == [0.7, 0.75, 0.80]

    def test_get_average(self):
        """Test getting rolling average."""
        tracker = MetricsTracker()

        for i in range(5):
            tracker.record({"ndcg": i / 10})

        avg = tracker.get_average("ndcg", window=3)

        # Average of last 3: 0.2 + 0.3 + 0.4 / 3
        assert avg == pytest.approx(0.3)

    def test_singleton(self):
        """Test singleton pattern."""
        tracker1 = get_metrics_tracker()
        tracker2 = get_metrics_tracker()

        assert tracker1 is tracker2


class TestEvaluateMatchingSystem:
    """Tests for evaluate_matching_system function."""

    @pytest.fixture
    def sample_profiles(self):
        """Create sample profiles."""
        from app.models.profile import Profile

        return [
            Profile(
                id=1,
                full_name="Dev 1",
                parsed_skills=["python"],
                parsed_languages=["en"],
                parsed_location="paris",
                parsed_seniority="mid",
                availability_status="available",
            ),
            Profile(
                id=2,
                full_name="Dev 2",
                parsed_skills=["python", "react"],
                parsed_languages=["en"],
                parsed_location="paris",
                parsed_seniority="senior",
                availability_status="available",
            ),
            Profile(
                id=3,
                full_name="Dev 3",
                parsed_skills=["java"],
                parsed_languages=["fr"],
                parsed_location="lyon",
                parsed_seniority="junior",
                availability_status="not_available",
            ),
        ]

    @pytest.fixture
    def sample_missions(self):
        """Create sample missions."""
        from app.models.mission import Mission

        return [
            Mission(
                id=1,
                title="Python Dev",
                description="Need Python developer",
                required_skills=["python"],
                required_language="en",
                required_location="paris",
                required_seniority="mid",
                status="active",
            ),
            Mission(
                id=2,
                title="React Dev",
                description="Need React developer",
                required_skills=["react"],
                required_language="en",
                required_location="paris",
                required_seniority="senior",
                status="active",
            ),
        ]

    def test_evaluate_matching_system(self, sample_profiles, sample_missions):
        """Test full evaluation pipeline."""
        # Create predicted rankings
        predicted_rankings = {
            1: [2, 1, 3],  # Mission 1: profile 2, then 1, then 3
            2: [2, 1, 3],  # Mission 2: same
        }

        # Create ground truth (which profiles are relevant to which missions)
        ground_truth = {
            1: {1, 2},  # Profiles 1 and 2 are relevant to mission 1
            2: {2},     # Only profile 2 is relevant to mission 2
        }

        result = evaluate_matching_system(
            profiles=sample_profiles,
            missions=sample_missions,
            predicted_rankings=predicted_rankings,
            ground_truth=ground_truth,
        )

        assert "aggregate_metrics" in result
        assert "mission_metrics" in result
        assert "num_missions" in result
        assert "num_profiles" in result

        # Check aggregate metrics structure
        agg = result["aggregate_metrics"]
        assert "precision_at_k" in agg
        assert "recall_at_k" in agg
        assert "map_at_k" in agg
        assert "ndcg" in agg
        assert "mrr" in agg

        # Check mission metrics
        assert 1 in result["mission_metrics"]
        assert 2 in result["mission_metrics"]


class TestRankingResult:
    """Tests for RankingResult dataclass."""

    def test_ranking_result_creation(self):
        """Test creating a RankingResult."""
        result = RankingResult(
            mission_id=1,
            profile_ids=[1, 2, 3],
            scores=[0.9, 0.8, 0.7],
            relevance_labels=[1, 1, 0],
        )

        assert result.mission_id == 1
        assert len(result.profile_ids) == 3
        assert len(result.scores) == 3
        assert len(result.relevance_labels) == 3

    def test_ranking_result_with_metrics_service(self):
        """Test using RankingResult with MetricsService."""
        service = MetricsService()

        rankings = [
            RankingResult(
                mission_id=1,
                profile_ids=[1, 2, 3],
                scores=[0.9, 0.8, 0.7],
                relevance_labels=[1, 1, 0],
            ),
            RankingResult(
                mission_id=2,
                profile_ids=[2, 1, 3],
                scores=[0.85, 0.75, 0.65],
                relevance_labels=[1, 0, 0],
            ),
        ]

        result = service.evaluate_rankings(rankings)

        assert isinstance(result, MetricsResult)
        assert result.mrr > 0  # Should have some reciprocal rank