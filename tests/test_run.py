"""End-to-end tests for the ski recommendation agent.

These tests make real API calls and require:
- ANTHROPIC_API_KEY in environment
- Database seeded (make seed-db)

Run with: .venv/bin/python -m pytest tests/test_run.py -v -s
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
    """End-to-end recommendation tests."""

    @pytest.mark.parametrize(
        "query,expected_terms",
        [
            (
                "Where should I ski tomorrow? I have an Ikon pass and want terrain parks.",
                ["Jay Peak"],  # Only Ikon mountain with terrain parks
            ),
            (
                "Best place to snowboard within 2 hours of Boston?",
                ["Nashoba", "Gunstock", "Waterville"],  # Close mountains
            ),
            (
                "I want to hit some glades, have an Epic pass",
                ["Stowe", "Okemo"],  # Epic mountains with glades
            ),
            (
                "Teaching my kid to ski for the first time tomorrow",
                ["magic carpet", "beginner", "learning", "green"],  # Beginner-friendly terms
            ),
            (
                "Looking for double blacks and expert terrain tomorrow",
                ["Jay Peak", "Stowe"],  # Mountains with double black %
            ),
        ],
    )
    def test_recommendation_contains_expected(self, query, expected_terms):
        """Test that recommendations mention expected mountains or terms."""
        result = recommend(query)

        # At least one expected term should appear in the result
        result_lower = result.lower()
        found = any(term.lower() in result_lower for term in expected_terms)

        print(f"\nQuery: {query}")
        print(f"Result: {result}")
        print(f"Expected one of: {expected_terms}")

        assert found, f"Expected one of {expected_terms} in result"
