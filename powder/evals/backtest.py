"""
Backtesting harness for running evaluations with mocked conditions.

This module provides:
1. Proper mocking of weather API using unittest.mock.patch
2. Loading conditions from historic fixtures
3. Running pipeline against labeled examples

Usage:
    from powder.evals.backtest import run_backtest
    results = run_backtest(examples, conditions_fixture)
"""

import json
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator
from unittest.mock import patch, MagicMock

from powder.pipeline import SkiPipeline
from powder.tools.database import haversine_km


def load_fixture(fixture_name: str, fixtures_dir: Path = None) -> dict:
    """
    Load a conditions fixture by name or date.

    Args:
        fixture_name: Either a date "2025-01-15" or scenario name

    Returns:
        Dict mapping mountain name -> conditions dict
    """
    if fixtures_dir is None:
        fixtures_dir = Path(__file__).parent / "fixtures"

    # Try loading by date from full season data
    by_date_file = fixtures_dir / "by_date.json"
    if by_date_file.exists():
        with open(by_date_file) as f:
            data = json.load(f)
            dates = data.get("dates", {})
            if fixture_name in dates:
                return dates[fixture_name]

    # Try individual mountain files
    for filepath in fixtures_dir.glob("*.json"):
        if fixture_name in filepath.stem:
            with open(filepath) as f:
                data = json.load(f)
                return data.get("conditions", data)

    raise FileNotFoundError(f"Fixture not found: {fixture_name}")


def find_mountain_by_coords(
    lat: float, lon: float, conditions: dict[str, dict]
) -> tuple[str, dict] | None:
    """
    Find the closest mountain in conditions by coordinates.

    Returns (name, conditions_dict) or None if no match.
    """
    # Mountain coordinates (from database)
    MOUNTAIN_COORDS = {
        "Stowe": (44.5258, -72.7858),
        "Killington": (43.6045, -72.8201),
        "Jay Peak": (44.97, -72.47),
        "Sugarbush": (44.14, -72.88),
        "Okemo": (43.41, -72.72),
        "Mount Snow": (42.96, -72.92),
        "Stratton": (43.12, -72.90),
        "Mad River Glen": (44.2009, -72.9246),
        "Smugglers' Notch": (44.5553, -72.7957),
        "Waterville Valley": (43.9592, -71.5233),
        "Gunstock": (43.53, -71.37),
        "Attitash": (44.09, -71.21),
        "Bretton Woods": (44.2558, -71.4573),
        "Nashoba Valley": (42.48, -71.49),
    }

    best_match = None
    best_distance = float("inf")

    for name, (mtn_lat, mtn_lon) in MOUNTAIN_COORDS.items():
        if name not in conditions:
            continue

        dist = haversine_km(lat, lon, mtn_lat, mtn_lon)
        if dist < best_distance:
            best_distance = dist
            best_match = (name, conditions[name])

    return best_match if best_distance < 10 else None  # Within 10km


def make_mock_conditions(conditions: dict[str, dict]) -> callable:
    """
    Create a mock get_conditions function that returns fixture data.

    Args:
        conditions: Dict mapping mountain name -> conditions dict

    Returns:
        Mock function compatible with weather.get_conditions signature
    """
    def mock_get_conditions(lat: float, lon: float, target_date) -> dict:
        match = find_mountain_by_coords(lat, lon, conditions)

        if match:
            name, cond = match
            # Return in expected format
            return {
                "fresh_snow_24h_cm": cond.get("fresh_snow_24h_cm", 0),
                "fresh_snow_24h_in": cond.get("fresh_snow_24h_in", 0),
                "snow_depth_cm": cond.get("snow_depth_cm", 0),
                "snow_depth_in": cond.get("snow_depth_in", 0),
                "temp_c": cond.get("temp_c", 0),
                "temp_f": cond.get("temp_f", 32),
                "wind_kph": cond.get("wind_kph", 0),
                "wind_mph": cond.get("wind_mph", 0),
                "visibility_km": cond.get("visibility_km", 10),
                "visibility_mi": cond.get("visibility_mi", 6),
                "weather_code": cond.get("weather_code", 0),
                "weather_description": cond.get("weather_description", "Clear"),
            }

        # Default conditions if no match
        return {
            "fresh_snow_24h_cm": 0,
            "fresh_snow_24h_in": 0,
            "snow_depth_cm": 50,
            "snow_depth_in": 20,
            "temp_c": -5,
            "temp_f": 23,
            "wind_kph": 15,
            "wind_mph": 9,
            "visibility_km": 10,
            "visibility_mi": 6,
            "weather_code": 0,
            "weather_description": "Clear",
        }

    return mock_get_conditions


@contextmanager
def mock_weather_api(conditions: dict[str, dict]) -> Generator[None, None, None]:
    """
    Context manager that mocks the weather API with fixture data.

    Patches at all import locations to ensure mocking works for both
    Pipeline and ReAct agent.
    """
    mock_fn = make_mock_conditions(conditions)

    # Patch at all locations where get_conditions might be imported
    with patch("powder.pipeline.get_conditions", mock_fn), \
         patch("powder.tools.weather.get_conditions", mock_fn), \
         patch("powder.agent.get_conditions", mock_fn):
        yield


@contextmanager
def mock_routing_api() -> Generator[None, None, None]:
    """
    Context manager that mocks the routing API with estimated drive times.

    Uses haversine distance * 1.3 for rough drive time estimate.
    """
    def mock_get_drive_time(start_lat, start_lon, end_lat, end_lon) -> dict:
        distance_km = haversine_km(start_lat, start_lon, end_lat, end_lon)
        # Rough estimate: 80 km/h average speed with 1.3x factor for roads
        duration_minutes = (distance_km * 1.3) / 80 * 60

        return {
            "duration_seconds": duration_minutes * 60,
            "duration_minutes": duration_minutes,
            "distance_m": distance_km * 1000,
            "distance_km": distance_km,
            "distance_mi": distance_km / 1.609,
        }

    with patch("powder.pipeline.get_drive_time", mock_get_drive_time), \
         patch("powder.tools.routing.get_drive_time", mock_get_drive_time), \
         patch("powder.agent.get_drive_time", mock_get_drive_time):
        yield


def run_pipeline_with_mocks(
    query: str,
    query_date: date,
    user_location: dict,
    conditions: dict[str, dict],
) -> dict:
    """
    Run the pipeline with mocked APIs.

    Args:
        query: User query string
        query_date: Date for the query
        user_location: Dict with 'name', 'lat', 'lon'
        conditions: Dict mapping mountain name -> conditions

    Returns:
        Pipeline result dict
    """
    pipeline = SkiPipeline()

    with mock_weather_api(conditions), mock_routing_api():
        result = pipeline(
            query=query,
            current_date=query_date,
            user_location=user_location,
        )

    return {
        "top_pick": result.top_pick,
        "alternatives": result.alternatives,
        "caveat": result.caveat,
        "parsed": result.parsed,
        "candidates": result.candidates,
        "scores": result.scores,
    }


def run_react_with_mocks(
    query: str,
    query_date: date,
    user_location: dict,
    conditions: dict[str, dict],
) -> dict:
    """
    Run the ReAct agent with mocked APIs.

    Args:
        query: User query string
        query_date: Date for the query
        user_location: Dict with 'name', 'lat', 'lon'
        conditions: Dict mapping mountain name -> conditions

    Returns:
        Dict with recommendation string and extracted info
    """
    from powder.agent import recommend

    with mock_weather_api(conditions), mock_routing_api():
        recommendation = recommend(
            query=query,
            current_date=query_date,
            current_location=user_location,
        )

    return {
        "recommendation": recommendation,
        # ReAct returns unstructured text, so we extract what we can
        "top_pick": recommendation,  # Full text, will be parsed by eval
    }


def run_backtest_example(example, conditions: dict[str, dict] = None) -> dict:
    """
    Run a single backtest example.

    Args:
        example: EndToEndExample or similar with query, query_date, user_location, conditions_snapshot
        conditions: Override conditions (uses example.conditions_snapshot if None)

    Returns:
        Dict with prediction and metrics
    """
    conds = conditions or example.conditions_snapshot

    result = run_pipeline_with_mocks(
        query=example.query,
        query_date=example.query_date,
        user_location=example.user_location,
        conditions=conds,
    )

    return {
        "example_id": example.id,
        "query": example.query,
        "predicted_top_pick": result["top_pick"],
        "predicted_top_3": [s["mountain"]["name"] for s in result["scores"][:3]] if result["scores"] else [],
        "candidates_count": len(result["candidates"]) if result["candidates"] else 0,
        "result": result,
    }


if __name__ == "__main__":
    # Quick test
    from datetime import date

    print("Testing backtest harness...")

    # Create sample conditions
    test_conditions = {
        "Stowe": {"fresh_snow_24h_in": 12, "temp_f": 20, "wind_mph": 10},
        "Killington": {"fresh_snow_24h_in": 8, "temp_f": 22, "wind_mph": 15},
        "Jay Peak": {"fresh_snow_24h_in": 14, "temp_f": 18, "wind_mph": 12},
    }

    result = run_pipeline_with_mocks(
        query="Best powder day with Ikon pass?",
        query_date=date.today(),
        user_location={"name": "Boston", "lat": 42.3601, "lon": -71.0589},
        conditions=test_conditions,
    )

    print(f"\nTop pick: {result['top_pick'][:100]}...")
    print(f"Candidates found: {len(result['candidates']) if result['candidates'] else 0}")
