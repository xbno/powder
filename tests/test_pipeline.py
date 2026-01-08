"""Smoke tests for the SkiPipeline.

These are minimal integration tests to verify the pipeline works end-to-end.
Detailed behavior testing is done via the eval framework in powder/evals/.

Run with: .venv/bin/python -m pytest tests/test_pipeline.py -v -s
"""

import os
from datetime import date
from unittest.mock import patch, MagicMock

import pytest
import dspy

from powder.pipeline import SkiPipeline


# Mark all tests as requiring LLM, skip if no API key
pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    ),
]


TEST_DATE = "2025-01-08"


def _mock_weather_response(target_date: str = TEST_DATE) -> dict:
    """Generate a mock Open-Meteo API response for a given date."""
    times = [f"{target_date}T{h:02d}:00" for h in range(24)]
    return {
        "hourly": {
            "time": times,
            "temperature_2m": [-5.0] * 24,
            "wind_speed_10m": [15.0] * 24,
            "visibility": [10000.0] * 24,
            "weather_code": [71] * 24,
            "snowfall": [0.5] * 24,
            "snow_depth": [0.3] * 24,
        }
    }


@pytest.fixture(autouse=True)
def mock_weather_api():
    """Mock the Open-Meteo weather API for all tests."""
    with patch("powder.tools.weather.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = _mock_weather_response()
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture(scope="module", autouse=True)
def configure_lm():
    """Configure DSPy LM for all tests in this module."""
    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))


def test_pipeline_smoke():
    """Smoke test: pipeline produces a recommendation with expected structure."""
    pipeline = SkiPipeline()
    result = pipeline(
        query="Best skiing in Vermont today?",
        current_date=date.fromisoformat(TEST_DATE),
    )

    # Basic structure checks
    assert result.top_pick is not None
    assert len(result.top_pick) > 0
    assert result.parsed is not None
    assert isinstance(result.candidates, list)
    assert isinstance(result.scores, list)
