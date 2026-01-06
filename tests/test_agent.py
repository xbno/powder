"""Tests for ski recommendation agent."""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from powder.agent import build_user_context, create_agent, search_mountains
from powder.signatures import SkiRecommendation


class TestUserContext:
    """Test user context building."""

    @pytest.mark.parametrize(
        "input_date, expected_today, expected_tomorrow",
        [
            (date(2024, 1, 15), "2024-01-15", "2024-01-16"),
            (date(2024, 12, 31), "2024-12-31", "2025-01-01"),  # Year boundary
            (date(2024, 2, 28), "2024-02-28", "2024-02-29"),  # Leap year
        ],
    )
    def test_date_context(self, input_date, expected_today, expected_tomorrow):
        """Test date formatting in context."""
        context = build_user_context(current_date=input_date)

        assert f"Today's date: {expected_today}" in context
        assert f"Tomorrow's date: {expected_tomorrow}" in context

    @pytest.mark.parametrize(
        "location, expected_name",
        [
            ({"name": "Boston, MA", "lat": 42.36, "lon": -71.06}, "Boston, MA"),
            ({"name": "NYC", "lat": 40.71, "lon": -74.01}, "NYC"),
        ],
    )
    def test_location_context(self, location, expected_name):
        """Test location in context."""
        context = build_user_context(
            current_date=date(2024, 1, 15),
            current_location=location,
        )

        assert expected_name in context
        assert str(location["lat"]) in context
        assert str(location["lon"]) in context

    def test_default_location_is_boston(self):
        """Test that default location is Boston."""
        context = build_user_context(current_date=date(2024, 1, 15))
        assert "Boston, MA" in context


class TestSearchMountains:
    """Test mountain search tool."""

    def test_returns_json_string(self):
        """Test that search_mountains returns valid JSON."""
        import json

        # Mock the database query
        mock_results = [
            {"name": "Stowe", "state": "VT", "distance_km": 270.0},
            {"name": "Jay Peak", "state": "VT", "distance_km": 320.0},
        ]

        with patch("powder.agent.query_mountains", return_value=mock_results):
            with patch("powder.agent.get_engine"):
                with patch("powder.agent.sessionmaker"):
                    result = search_mountains(max_drive_hours=4.0)

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)


class TestAgentCreation:
    """Test agent instantiation."""

    def test_create_agent_returns_react(self):
        """Test that create_agent returns a ReAct instance."""
        import dspy

        agent = create_agent()
        assert isinstance(agent, dspy.ReAct)

    def test_agent_has_three_tools(self):
        """Test that agent has the expected tools."""
        agent = create_agent()

        # ReAct stores tools as dict
        tool_names = list(agent.tools.keys())
        assert "search_mountains" in tool_names
        assert "get_mountain_conditions" in tool_names
        assert "get_driving_time" in tool_names


class TestSignature:
    """Test DSPy signature structure."""

    def test_signature_has_required_fields(self):
        """Test that SkiRecommendation has query, context, and recommendation."""
        import dspy

        sig = SkiRecommendation

        # Check input fields
        assert "query" in sig.input_fields
        assert "user_context" in sig.input_fields

        # Check output fields
        assert "recommendation" in sig.output_fields
