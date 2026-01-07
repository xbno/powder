"""End-to-end tests for the ski recommendation agent.

These tests make real API calls and require:
- ANTHROPIC_API_KEY in environment
- Database seeded (make seed-db)

Run with: .venv/bin/python -m pytest tests/test_run.py -v -s

NOTE: Tests are designed to be DB-agnostic. They verify the agent
understands queries and responds appropriately, without checking
for specific mountain names.
"""

import os
import pytest
import dspy

from powder.agent import recommend


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


class TestRecommendations:
    """End-to-end recommendation tests.

    These tests verify the agent understands different query types
    without depending on specific mountains in the database.
    """

    def test_produces_recommendation(self):
        """Test that agent produces a non-empty recommendation."""
        result = recommend("Where should I ski tomorrow?")

        assert result is not None
        assert len(result) > 50  # Should be a substantive response

    def test_pass_type_acknowledged(self):
        """Test that pass type is acknowledged in response."""
        result = recommend("I have an Ikon pass, where should I go?")
        result_lower = result.lower()

        # Should mention the pass type or related terms
        pass_terms = ["ikon", "pass", "included", "covered"]
        assert any(term in result_lower for term in pass_terms), \
            f"Expected pass-related terms in: {result[:200]}"

    def test_terrain_park_acknowledged(self):
        """Test that terrain park request is acknowledged."""
        result = recommend("Looking for a good terrain park to hit some rails")
        result_lower = result.lower()

        # Should mention parks, features, or freestyle terrain
        park_terms = ["park", "terrain", "rails", "features", "freestyle", "jump"]
        assert any(term in result_lower for term in park_terms), \
            f"Expected park-related terms in: {result[:200]}"

    def test_beginner_needs_acknowledged(self):
        """Test that beginner/learning needs are acknowledged."""
        result = recommend("Teaching my kid to ski for the first time")
        result_lower = result.lower()

        # Should mention beginner-friendly features
        beginner_terms = [
            "beginner", "learning", "lesson", "green", "easy",
            "first time", "kid", "family", "magic carpet", "bunny"
        ]
        assert any(term in result_lower for term in beginner_terms), \
            f"Expected beginner-related terms in: {result[:200]}"

    def test_expert_terrain_acknowledged(self):
        """Test that expert terrain request is acknowledged."""
        result = recommend("Want challenging terrain, double blacks and steeps")
        result_lower = result.lower()

        # Should mention expert terrain features
        expert_terms = [
            "expert", "advanced", "black", "double black", "steep",
            "challenging", "difficult", "extreme"
        ]
        assert any(term in result_lower for term in expert_terms), \
            f"Expected expert-related terms in: {result[:200]}"

    def test_glades_acknowledged(self):
        """Test that glades/tree skiing request is acknowledged."""
        result = recommend("Looking for tree skiing and glades")
        result_lower = result.lower()

        # Should mention glades or tree skiing
        glade_terms = ["glade", "tree", "woods", "forest"]
        assert any(term in result_lower for term in glade_terms), \
            f"Expected glade-related terms in: {result[:200]}"

    def test_drive_time_constraint_acknowledged(self):
        """Test that drive time constraint is acknowledged."""
        result = recommend("Best skiing within 1 hour drive?")
        result_lower = result.lower()

        # Should mention drive/distance or acknowledge the constraint
        drive_terms = ["hour", "drive", "close", "nearby", "distance", "minute"]
        assert any(term in result_lower for term in drive_terms), \
            f"Expected drive-related terms in: {result[:200]}"

    def test_night_skiing_acknowledged(self):
        """Test that night skiing request is acknowledged."""
        result = recommend("Any mountains with night skiing tonight?")
        result_lower = result.lower()

        # Should mention night skiing
        night_terms = ["night", "evening", "lights", "after dark", "lit"]
        assert any(term in result_lower for term in night_terms), \
            f"Expected night skiing terms in: {result[:200]}"

    def test_snowboard_acknowledged(self):
        """Test that snowboarding is acknowledged."""
        result = recommend("Best place to snowboard tomorrow?")
        result_lower = result.lower()

        # Should mention snowboarding or not exclude it
        # (some mountains like Mad River Glen don't allow snowboarding)
        board_terms = ["snowboard", "board", "riding", "ride"]
        assert any(term in result_lower for term in board_terms), \
            f"Expected snowboard-related terms in: {result[:200]}"

    def test_multiple_constraints_handled(self):
        """Test that multiple constraints are handled together."""
        result = recommend(
            "Ikon pass, looking for glades, within 3 hours of Boston"
        )
        result_lower = result.lower()

        # Should produce a substantive response
        assert len(result) > 50

        # Should acknowledge at least one of the constraints
        constraint_terms = ["ikon", "glade", "tree", "hour", "drive", "boston"]
        assert any(term in result_lower for term in constraint_terms), \
            f"Expected constraint acknowledgment in: {result[:200]}"
