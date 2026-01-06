"""Open-Meteo weather and snow data client."""

import httpx
from datetime import date


BASE_URL = "https://api.open-meteo.com/v1/forecast"


def get_conditions(lat: float, lon: float, target_date: date | None = None) -> dict:
    """
    Get weather and snow conditions for a location.

    Args:
        lat: Latitude
        lon: Longitude
        target_date: Date to get forecast for (default: today)

    Returns:
        dict with metric and imperial units:
            - temperature_c / temperature_f
            - wind_speed_kmh / wind_speed_mph
            - visibility_m / visibility_ft
            - snow_depth_cm / snow_depth_in
            - fresh_snow_24h_cm / fresh_snow_24h_in
            - weather_code: WMO weather code
            - weather_description: Human-readable weather
    """
    if target_date is None:
        target_date = date.today()

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,wind_speed_10m,visibility,weather_code,snowfall,snow_depth",
        "timezone": "America/New_York",
        "forecast_days": 7,
    }

    response = httpx.get(BASE_URL, params=params, timeout=10.0)
    response.raise_for_status()
    data = response.json()

    # Find midday (12:00) hourly data for the target date
    date_str = target_date.isoformat()
    hour_str = f"{date_str}T12:00"
    try:
        hour_idx = data["hourly"]["time"].index(hour_str)
    except ValueError:
        raise ValueError(f"Date {date_str} not in forecast range")

    # Extract values
    hourly = data["hourly"]
    temp = hourly["temperature_2m"][hour_idx]
    wind = hourly["wind_speed_10m"][hour_idx]
    visibility = hourly["visibility"][hour_idx]
    weather_code = hourly["weather_code"][hour_idx]
    snow_depth = hourly["snow_depth"][hour_idx]  # in meters
    snowfall = hourly["snowfall"][hour_idx]  # cm per hour

    # Sum snowfall over 24 hours for fresh snow
    start_idx = max(0, hour_idx - 24)
    fresh_snow_cm = sum(hourly["snowfall"][start_idx:hour_idx + 1] or [0])
    snow_depth_cm = snow_depth * 100 if snow_depth else 0

    # Conversions
    temp_f = (temp * 9 / 5) + 32 if temp is not None else None
    wind_mph = wind * 0.621371 if wind is not None else None
    visibility_ft = visibility * 3.28084 if visibility is not None else None
    snow_depth_in = snow_depth_cm / 2.54
    fresh_snow_in = fresh_snow_cm / 2.54

    return {
        # Metric
        "temperature_c": temp,
        "wind_speed_kmh": wind,
        "visibility_m": visibility,
        "snow_depth_cm": round(snow_depth_cm, 1),
        "fresh_snow_24h_cm": round(fresh_snow_cm, 1),
        # Imperial
        "temperature_f": round(temp_f, 1) if temp_f is not None else None,
        "wind_speed_mph": round(wind_mph, 1) if wind_mph is not None else None,
        "visibility_ft": round(visibility_ft, 0) if visibility_ft is not None else None,
        "snow_depth_in": round(snow_depth_in, 1),
        "fresh_snow_24h_in": round(fresh_snow_in, 1),
        # Weather
        "weather_code": weather_code,
        "weather_description": _weather_code_to_description(weather_code),
    }


def _weather_code_to_description(code: int | None) -> str:
    """Convert WMO weather code to human-readable description."""
    if code is None:
        return "Unknown"

    # WMO Weather interpretation codes (WW)
    # https://open-meteo.com/en/docs
    codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return codes.get(code, f"Unknown ({code})")
