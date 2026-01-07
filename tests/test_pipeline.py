"""End-to-end tests for the SkiPipeline.

These tests make real API calls and require:
- ANTHROPIC_API_KEY in environment

Run with: .venv/bin/python -m pytest tests/test_pipeline.py -v -s
"""

import os
from datetime import date

import pytest
import dspy

from powder.pipeline import SkiPipeline, recommend


# Mark all tests as requiring LLM, skip if no API key
pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    ),
]


@pytest.fixture(scope="module", autouse=True)
def configure_lm():
    """Configure DSPy LM for all tests in this module."""
    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))


class TestSkiPipeline:
    """Test the explicit multi-step pipeline."""

    @pytest.fixture
    def pipeline(self):
        return SkiPipeline()

    def test_basic_query(self, pipeline):
        """Test that pipeline produces a recommendation."""
        result = pipeline(
            query="Where should I ski tomorrow?",
            current_date=date.today(),  # Use today to stay in weather API range
        )

        # Check we got outputs
        assert result.top_pick is not None
        assert len(result.top_pick) > 0

        # Check intermediate results are captured
        assert result.parsed is not None
        assert result.candidates is not None
        # May have 0 candidates if filters are too strict - just check structure
        assert isinstance(result.candidates, list)

    def test_beginner_filter(self, pipeline):
        """Test that beginner terrain filter works."""
        result = pipeline(
            query="Teaching my kid to ski for the first time",
            current_date=date.today(),
        )

        # Should have parsed needs_beginner_terrain
        assert result.parsed.needs_beginner_terrain is True

        # All candidates should have magic carpet (if any returned)
        for candidate in result.candidates:
            assert candidate.get("has_magic_carpet") is True

    def test_pass_type_filter(self, pipeline):
        """Test that pass type filter works."""
        result = pipeline(
            query="I have an Epic pass, where should I go?",
            current_date=date.today(),
        )

        # Should have parsed pass_type
        assert result.parsed.pass_type is not None
        assert "epic" in result.parsed.pass_type.lower()

        # All candidates should be Epic pass mountains (if any returned)
        for candidate in result.candidates:
            pass_types = candidate.get("pass_types", "") or ""
            assert "epic" in pass_types.lower()

    def test_no_candidates(self, pipeline):
        """Test graceful handling when no mountains match."""
        result = pipeline(
            query="Night skiing with terrain park within 30 minutes of Boston",
            current_date=date.today(),
        )

        # Should handle gracefully
        assert result.top_pick is not None
        # Either found something or explains no results
        assert len(result.top_pick) > 0


class TestRecommendFunction:
    """Test the convenience recommend() function."""

    def test_returns_dict(self):
        """Test that recommend returns expected structure."""
        result = recommend(
            query="Best skiing tomorrow?",
            current_date=date.today(),
        )

        assert isinstance(result, dict)
        assert "top_pick" in result
        assert "alternatives" in result
        assert "caveat" in result
