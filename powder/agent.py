"""Ski recommendation agent using DSPy ReAct."""

import dspy
from datetime import date, timedelta
from pathlib import Path

from powder.signatures import SkiRecommendation
from powder.tools.database import get_engine, query_mountains
from powder.tools.weather import get_conditions
from powder.tools.routing import get_drive_time, estimate_max_distance_km

from sqlalchemy.orm import sessionmaker


# Default user context - can be overridden
DEFAULT_CONTEXT = {
    "current_date": None,  # Will be set to today if not provided
    "tomorrow_date": None,  # Will be set to tomorrow if not provided
    "current_location": {
        "name": "Boston, MA",
        "lat": 42.3601,
        "lon": -71.0589,
    },
}


def build_user_context(
    current_date: date | None = None,
    current_location: dict | None = None,
) -> str:
    """Build user context string from defaults and overrides."""
    ctx_date = current_date or date.today()
    ctx_tomorrow = ctx_date + timedelta(days=1)
    ctx_location = current_location or DEFAULT_CONTEXT["current_location"]

    return (
        f"Today's date: {ctx_date.isoformat()}\n"
        f"Tomorrow's date: {ctx_tomorrow.isoformat()}\n"
        f"User's location: {ctx_location['name']} "
        f"({ctx_location['lat']}, {ctx_location['lon']})"
    )


# --- Tool functions with clear docstrings for DSPy ---

def search_mountains(
    max_drive_hours: float = 3.0,
    pass_type: str | None = None,
    user_lat: float = 42.3601,
    user_lon: float = -71.0589,
) -> str:
    """
    Search for ski mountains within driving distance.

    Args:
        max_drive_hours: Maximum driving time in hours (default 3.0)
        pass_type: Filter by pass type - 'epic', 'ikon', or 'indy' (optional)
        user_lat: User's latitude (default Boston)
        user_lon: User's longitude (default Boston)

    Returns:
        JSON string with list of mountains including name, state, vertical drop,
        terrain percentages, lift types, and approximate distance.
    """
    import json

    # Convert hours to km for haversine prefilter
    max_distance_km = estimate_max_distance_km(max_drive_hours)

    # Get database session
    db_path = Path(__file__).parent / "data" / "mountains.db"
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        results = query_mountains(
            session,
            lat=user_lat,
            lon=user_lon,
            max_distance_km=max_distance_km,
            pass_type=pass_type,
        )
        return json.dumps(results, indent=2)
    finally:
        session.close()


def get_mountain_conditions(
    lat: float,
    lon: float,
    target_date: str | None = None,
) -> str:
    """
    Get weather and snow conditions for a mountain location.

    Args:
        lat: Mountain latitude
        lon: Mountain longitude
        target_date: Date to check conditions for (YYYY-MM-DD format, default today)

    Returns:
        JSON string with temperature, wind, visibility, snow depth,
        fresh snow in last 24h, and weather description.
    """
    import json

    if target_date:
        check_date = date.fromisoformat(target_date)
    else:
        check_date = date.today()

    conditions = get_conditions(lat, lon, check_date)
    return json.dumps(conditions, indent=2)


def get_driving_time(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> str:
    """
    Get actual driving time between two locations.

    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Destination latitude
        end_lon: Destination longitude

    Returns:
        JSON string with duration in minutes and distance in km/miles.
    """
    import json

    result = get_drive_time(start_lat, start_lon, end_lat, end_lon)
    return json.dumps(result, indent=2)


def create_agent() -> dspy.ReAct:
    """
    Create the ski recommendation ReAct agent.

    Returns:
        Configured dspy.ReAct agent with ski tools.
    """
    tools = [
        dspy.Tool(search_mountains),
        dspy.Tool(get_mountain_conditions),
        dspy.Tool(get_driving_time),
    ]

    agent = dspy.ReAct(
        signature=SkiRecommendation,
        tools=tools,
        max_iters=8,
    )

    return agent


def recommend(
    query: str,
    current_date: date | None = None,
    current_location: dict | None = None,
) -> str:
    """
    Get ski recommendations for a user query.

    Args:
        query: Natural language query like "Where should I ski tomorrow?"
        current_date: Override current date (for testing/backtesting)
        current_location: Override location dict with 'name', 'lat', 'lon'

    Returns:
        Recommendation string with top picks and reasoning.
    """
    agent = create_agent()
    user_context = build_user_context(current_date, current_location)

    result = agent(query=query, user_context=user_context)
    return result.recommendation
