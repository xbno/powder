"""End-to-end tests for DSPy signatures.

These tests make real API calls and require:
- ANTHROPIC_API_KEY in environment

Run with: .venv/bin/python -m pytest tests/test_signatures.py -v -s
"""

import os
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

    @pytest.mark.parametrize(
        "query,expected_date_pattern",
        [
            ("Where should I ski today?", "today"),
            ("Best powder tomorrow", "tomorrow"),
            ("Skiing this Saturday", "2026-01"),  # Should be a January 2026 date
            ("Where to go Sunday?", "2026-01"),
        ],
    )
    def test_date_parsing(self, parser, user_context, query, expected_date_pattern):
        """Test that dates are correctly extracted."""
        result = parser(query=query, user_context=user_context)
        assert expected_date_pattern in result.target_date.lower()

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
