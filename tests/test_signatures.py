"""End-to-end tests for DSPy signatures.

These tests make real API calls and require:
- ANTHROPIC_API_KEY in environment

Run with: .venv/bin/python -m pytest tests/test_signatures.py -v -s
"""

import os
from datetime import date, timedelta

import pytest
import dspy

from powder.agent import build_user_context
from powder.signatures import ParseSkiQuery


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


class TestParseSkiQuery:
    """Test query parsing extracts correct constraints."""

    @pytest.fixture
    def parser(self):
        return dspy.Predict(ParseSkiQuery)

    @pytest.fixture
    def user_context(self):
        return build_user_context()

    def test_date_parsing_today(self, parser, user_context):
        """Test that 'today' is correctly extracted."""
        result = parser(query="Where should I ski today?", user_context=user_context)
        # Accept "today" or actual today's date
        assert "today" in result.target_date.lower() or date.today().isoformat() in result.target_date

    def test_date_parsing_tomorrow(self, parser, user_context):
        """Test that 'tomorrow' is correctly extracted."""
        result = parser(query="Best powder tomorrow", user_context=user_context)
        # Accept "tomorrow" or actual tomorrow's date
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        assert "tomorrow" in result.target_date.lower() or tomorrow in result.target_date

    @pytest.mark.parametrize(
        "query",
        [
            "Skiing this Saturday",
            "Where to go Sunday?",
        ],
    )
    def test_date_parsing_weekday(self, parser, user_context, query):
        """Test that weekday references return a date."""
        result = parser(query=query, user_context=user_context)
        # Should return an actual date (YYYY-MM-DD format) or the day name
        assert (
            result.target_date.count("-") == 2  # Has date format
            or "saturday" in result.target_date.lower()
            or "sunday" in result.target_date.lower()
        )

    @pytest.mark.parametrize(
        "query",
        [
            "I want to hit rails and jumps",
            "Looking for a good terrain park",
            "Where has the best halfpipe?",
            "Want to session some boxes tomorrow",
        ],
    )
    def test_terrain_park_detection(self, parser, user_context, query):
        """Test that terrain park keywords are detected."""
        result = parser(query=query, user_context=user_context)
        assert result.needs_terrain_parks is True

    @pytest.mark.parametrize(
        "query",
        [
            "I want to ski some glades",
            "Looking for tree skiing",
            "Best mountain for woods runs?",
        ],
    )
    def test_glades_detection(self, parser, user_context, query):
        """Test that glade/tree skiing keywords are detected."""
        result = parser(query=query, user_context=user_context)
        assert result.needs_glades is True

    @pytest.mark.parametrize(
        "query,expected_pass",
        [
            ("I have an Ikon pass", "ikon"),
            ("Epic pass holder here", "epic"),
            ("Looking for Indy pass mountains", "indy"),
        ],
    )
    def test_pass_type_detection(self, parser, user_context, query, expected_pass):
        """Test that pass types are correctly extracted."""
        result = parser(query=query, user_context=user_context)
        assert result.pass_type.lower() == expected_pass

    @pytest.mark.parametrize(
        "query",
        [
            "Teaching my kid to ski for the first time",
            "First time skiing, need beginner terrain",
            "Looking for a good bunny hill",
        ],
    )
    def test_beginner_detection(self, parser, user_context, query):
        """Test that beginner/learning keywords are detected."""
        result = parser(query=query, user_context=user_context)
        assert result.needs_beginner_terrain is True

    def test_unspecified_date(self, parser, user_context):
        """Test that queries without date info return unspecified."""
        result = parser(query="Teaching my kid to ski, have Epic pass", user_context=user_context)
        assert result.target_date == "unspecified"
