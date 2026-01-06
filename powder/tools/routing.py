"""OpenRouteService routing client for drive times."""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def get_drive_time(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> dict:
    """
    Get driving time and distance between two points.

    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Destination latitude
        end_lon: Destination longitude

    Returns:
        dict with:
            - duration_seconds: Drive time in seconds
            - duration_minutes: Drive time in minutes
            - distance_m: Distance in meters
            - distance_km: Distance in kilometers
            - distance_mi: Distance in miles
    """
    api_key = os.environ.get("OPEN_ROUTE_SERVICE_API_KEY")
    if not api_key:
        raise ValueError("OPEN_ROUTE_SERVICE_API_KEY environment variable not set")

    # ORS uses lon,lat order (GeoJSON standard)
    params = {
        "api_key": api_key,
        "start": f"{start_lon},{start_lat}",
        "end": f"{end_lon},{end_lat}",
    }

    response = httpx.get(BASE_URL, params=params, timeout=10.0)
    response.raise_for_status()
    data = response.json()

    # Extract from GeoJSON response
    segment = data["features"][0]["properties"]["segments"][0]
    duration_sec = segment["duration"]
    distance_m = segment["distance"]

    return {
        "duration_seconds": round(duration_sec),
        "duration_minutes": round(duration_sec / 60, 1),
        "distance_m": round(distance_m),
        "distance_km": round(distance_m / 1000, 1),
        "distance_mi": round(distance_m / 1609.34, 1),
    }


def get_drive_times_batch(
    start_lat: float,
    start_lon: float,
    destinations: list[tuple[float, float]],
) -> list[dict]:
    """
    Get drive times to multiple destinations.

    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        destinations: List of (lat, lon) tuples

    Returns:
        List of dicts with duration/distance info for each destination.
    """
    results = []
    for dest_lat, dest_lon in destinations:
        result = get_drive_time(start_lat, start_lon, dest_lat, dest_lon)
        results.append(result)
    return results
