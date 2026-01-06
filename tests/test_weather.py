"""Tests for weather client."""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from powder.tools.weather import get_conditions, _weather_code_to_description


def make_mock_response(target_date: date, snow_depth_m: float, snowfall_hourly: list[float], temp_c: float = -5.0):
    """Helper to create mock API response for a specific date."""
    date_str = target_date.isoformat()
    hours = [f"{date_str}T{h:02d}:00" for h in range(24)]
    return {
        "hourly": {
            "time": hours,
            "temperature_2m": [temp_c] * 24,
            "wind_speed_10m": [15.0] * 24,
            "visibility": [10000.0] * 24,
            "weather_code": [73] * 24,
            "snowfall": snowfall_hourly + [0.0] * (24 - len(snowfall_hourly)),
            "snow_depth": [snow_depth_m] * 24,
        }
    }


class TestSnowCalculations:
    """Test snow depth and fresh snow calculations."""

    @pytest.mark.parametrize(
        "date_str, snow_depth_m, hourly_snowfall, expected_fresh_cm, expected_depth_cm",
        [
            # Powder day - 10cm fresh
            ("2024-01-15", 0.50, [0, 0, 0, 0, 0, 0, 0, 0, 2.5, 3.0, 2.0, 1.5, 1.0], 10.0, 50.0),
            # No new snow
            ("2024-01-16", 0.45, [0] * 13, 0.0, 45.0),
            # Big storm - 25cm
            ("2024-01-17", 0.75, [2.0] * 12 + [1.0], 25.0, 75.0),
            # Light flurries - 2cm
            ("2024-01-18", 0.30, [0, 0, 0, 0, 0, 0, 0.5, 0.5, 0.5, 0.5, 0, 0, 0], 2.0, 30.0),
            # Early morning dump - all snow before 8am
            ("2024-01-19", 0.60, [3.0, 3.0, 3.0, 3.0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 12.0, 60.0),
        ],
    )
    def test_fresh_snow_and_depth(self, date_str, snow_depth_m, hourly_snowfall, expected_fresh_cm, expected_depth_cm):
        """Test snow calculations for various storm scenarios."""
        target_date = date.fromisoformat(date_str)
        mock_response = make_mock_response(target_date, snow_depth_m, hourly_snowfall)

        with patch("powder.tools.weather.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(json=MagicMock(return_value=mock_response))
            result = get_conditions(44.5, -72.8, target_date)

            assert result["fresh_snow_24h_cm"] == expected_fresh_cm
            assert result["snow_depth_cm"] == expected_depth_cm


class TestUnitConversions:
    """Test metric to imperial conversions."""

    @pytest.mark.parametrize(
        "temp_c, expected_f",
        [
            (-40, -40.0),   # Where C and F are equal
            (-20, -4.0),
            (-10, 14.0),
            (-5, 23.0),
            (0, 32.0),      # Freezing point
            (10, 50.0),
        ],
    )
    def test_temperature_conversion(self, temp_c, expected_f):
        """Test Celsius to Fahrenheit conversion."""
        target_date = date(2024, 1, 15)
        mock_response = make_mock_response(target_date, 0.5, [0] * 13, temp_c=temp_c)

        with patch("powder.tools.weather.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(json=MagicMock(return_value=mock_response))
            result = get_conditions(44.5, -72.8, target_date)

            assert result["temperature_c"] == temp_c
            assert result["temperature_f"] == expected_f

    @pytest.mark.parametrize(
        "snow_cm, expected_in",
        [
            (0.0, 0.0),
            (2.54, 1.0),    # Exact inch
            (5.08, 2.0),    # 2 inches
            (12.7, 5.0),    # 5 inches
            (25.4, 10.0),   # 10 inches
            (50.8, 20.0),   # 20 inches - big storm
        ],
    )
    def test_snow_inch_conversion(self, snow_cm, expected_in):
        """Test snow cm to inches conversion."""
        target_date = date(2024, 1, 15)
        # Put all snow in first hour so sum through hour 12 = snow_cm
        mock_response = make_mock_response(target_date, 0.0, [snow_cm] + [0.0] * 12)

        with patch("powder.tools.weather.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(json=MagicMock(return_value=mock_response))
            result = get_conditions(44.5, -72.8, target_date)

            assert result["fresh_snow_24h_in"] == expected_in


class TestWeatherCodes:
    """Test WMO weather code translation."""

    @pytest.mark.parametrize(
        "code, expected_description",
        [
            (0, "Clear sky"),
            (1, "Mainly clear"),
            (2, "Partly cloudy"),
            (3, "Overcast"),
            (45, "Foggy"),
            (71, "Slight snow"),
            (73, "Moderate snow"),
            (75, "Heavy snow"),
            (85, "Slight snow showers"),
            (86, "Heavy snow showers"),
            (95, "Thunderstorm"),
            (None, "Unknown"),
            (999, "Unknown (999)"),
        ],
    )
    def test_weather_code_to_description(self, code, expected_description):
        """Test WMO code translation to human-readable description."""
        assert _weather_code_to_description(code) == expected_description


class TestMultipleDates:
    """Test fetching conditions across a multi-day storm event."""

    @pytest.mark.parametrize(
        "date_str, snow_depth_m, hourly_snowfall, expected_fresh_cm, expected_depth_cm",
        [
            # Day 1 - Storm arrives, steady snow
            ("2024-01-15", 0.50, [1.0] * 13, 13.0, 50.0),
            # Day 2 - Lull between waves
            ("2024-01-16", 0.55, [0.5] * 13, 6.5, 55.0),
            # Day 3 - Second wave dumps hard
            ("2024-01-17", 0.70, [2.0] * 13, 26.0, 70.0),
        ],
    )
    def test_storm_progression(self, date_str, snow_depth_m, hourly_snowfall, expected_fresh_cm, expected_depth_cm):
        """Test conditions across consecutive days of a multi-day storm."""
        target_date = date.fromisoformat(date_str)
        mock_response = make_mock_response(target_date, snow_depth_m, hourly_snowfall)

        with patch("powder.tools.weather.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(json=MagicMock(return_value=mock_response))
            result = get_conditions(44.5, -72.8, target_date)

            assert result["fresh_snow_24h_cm"] == expected_fresh_cm
            assert result["snow_depth_cm"] == expected_depth_cm


@pytest.mark.network
class TestLiveAPI:
    """Test against live Open-Meteo API."""

    def test_stowe_conditions(self):
        """Fetch real conditions for Stowe, VT."""
        result = get_conditions(44.5258, -72.7858)

        # Verify all fields present with reasonable values
        assert result["snow_depth_cm"] >= 0
        assert result["snow_depth_in"] >= 0
        assert result["temperature_c"] is not None
        assert result["temperature_f"] is not None
        assert result["wind_speed_kmh"] >= 0
        assert result["wind_speed_mph"] >= 0
        assert result["visibility_m"] > 0
        assert result["weather_code"] is not None
        assert result["weather_description"] is not None
