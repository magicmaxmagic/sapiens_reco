"""Tests for the simplified matching service."""

import pytest

from app.services.matching_service import (
    calculate_location_match,
    calculate_seniority_match,
    calculate_skills_match,
)


class TestSkillsMatch:
    """Tests for calculate_skills_match."""

    def test_exact_match(self):
        """Test exact skills match."""
        required = ["python", "fastapi", "sql"]
        profile = ["python", "fastapi", "sql"]
        assert calculate_skills_match(required, profile) == 1.0

    def test_partial_match(self):
        """Test partial skills match."""
        required = ["python", "fastapi", "sql"]
        profile = ["python", "fastapi"]
        assert calculate_skills_match(required, profile) == pytest.approx(2/3, rel=0.01)

    def test_no_match(self):
        """Test no skills match."""
        required = ["python", "fastapi"]
        profile = ["javascript", "react"]
        assert calculate_skills_match(required, profile) == 0.0

    def test_empty_required(self):
        """Test with empty required skills."""
        assert calculate_skills_match([], ["python"]) == 0.0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        required = ["Python", "FastAPI"]
        profile = ["python", "fastapi"]
        assert calculate_skills_match(required, profile) == 1.0


class TestSeniorityMatch:
    """Tests for calculate_seniority_match."""

    def test_exact_match(self):
        """Test exact seniority match."""
        assert calculate_seniority_match("senior", "senior") == 1.0

    def test_profile_higher(self):
        """Test profile with higher seniority."""
        assert calculate_seniority_match("junior", "senior") == 1.0
        assert calculate_seniority_match("mid", "lead") == 1.0

    def test_profile_lower(self):
        """Test profile with lower seniority."""
        assert calculate_seniority_match("senior", "junior") == 0.0
        assert calculate_seniority_match("lead", "mid") == 0.0

    def test_no_required_seniority(self):
        """Test with no required seniority."""
        assert calculate_seniority_match(None, "junior") == 1.0

    def test_unknown_seniority(self):
        """Test with unknown seniority value."""
        assert calculate_seniority_match("expert", "junior") == 1.0


class TestLocationMatch:
    """Tests for calculate_location_match."""

    def test_exact_match(self):
        """Test exact location match."""
        assert calculate_location_match("paris", "paris") == 1.0

    def test_fuzzy_match(self):
        """Test fuzzy location match."""
        assert calculate_location_match("paris", "paris, france") == 0.5
        assert calculate_location_match("montreal", "montreal, qc") == 0.5

    def test_no_match(self):
        """Test no location match."""
        assert calculate_location_match("paris", "london") == 0.0

    def test_no_required_location(self):
        """Test with no required location."""
        assert calculate_location_match(None, "paris") == 1.0

    def test_no_profile_location(self):
        """Test with no profile location."""
        assert calculate_location_match("paris", None) == 0.0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert calculate_location_match("PARIS", "paris") == 1.0
