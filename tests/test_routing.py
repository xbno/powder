"""Tests for routing client."""

import pytest
from unittest.mock import patch, MagicMock

from powder.tools.routing import get_drive_time, get_drive_times_batch, estimate_max_distance_km


def make_mock_response(duration_sec: float, distance_m: float) -> dict:
    """Helper to create mock ORS API response."""
    return {
        "features": [
            {
                "properties": {
                    "segments": [
                        {
                            "duration": duration_sec,
                            "distance": distance_m,
                        }
                    ]
                }
            }
        ]
    }


class TestDriveTime:
    """Test single drive time calculation."""

    @pytest.mark.parametrize(
        "start_lat, start_lon, end_lat, end_lon, duration_sec, distance_m, expected_minutes, expected_km, expected_mi",
        [
            # Boston to Nashoba Valley - short trip ~45 min
            (42.3601, -71.0589, 42.48, -71.49, 2700, 45000, 45.0, 45.0, 28.0),
            # Boston to Stowe - long trip ~3.5 hours
            (42.3601, -71.0589, 44.5258, -72.7858, 12600, 320000, 210.0, 320.0, 198.8),
        ],
    )
    def test_duration_and_distance_conversions(
        self, start_lat, start_lon, end_lat, end_lon, duration_sec, distance_m, expected_minutes, expected_km, expected_mi
    ):
        """Test time and distance unit conversions."""
        mock_response = make_mock_response(duration_sec, distance_m)

        with patch("powder.tools.routing.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(json=MagicMock(return_value=mock_response))
            result = get_drive_time(start_lat, start_lon, end_lat, end_lon)

            # Only assert converted values (raw values are just what mock returns)
            assert result["duration_minutes"] == expected_minutes
            assert result["distance_km"] == expected_km
            assert result["distance_mi"] == expected_mi


class TestDriveTimeBatch:
    """Test batch drive time calculations."""

    @pytest.mark.parametrize(
        "start_lat, start_lon, destinations, durations, distances, expected_minutes",
        [
            # Boston to Nashoba + Stowe
            (
                42.3601, -71.0589,
                [(42.48, -71.49), (44.5258, -72.7858)],
                [2700, 12600],
                [45000, 320000],
                [45.0, 210.0],
            ),
        ],
    )
    def test_batch_returns_all_destinations(
        self, start_lat, start_lon, destinations, durations, distances, expected_minutes
    ):
        """Test batch call returns result for each destination."""
        responses = [
            make_mock_response(dur, dist) for dur, dist in zip(durations, distances)
        ]

        with patch("powder.tools.routing.httpx.get") as mock_get:
            mock_get.return_value = MagicMock()
            mock_get.return_value.json.side_effect = responses

            results = get_drive_times_batch(start_lat, start_lon, destinations)

            assert len(results) == len(destinations)
            assert mock_get.call_count == len(destinations)

            for i, result in enumerate(results):
                assert result["duration_minutes"] == expected_minutes[i]


class TestEstimateDistance:
    """Test drive time to distance estimation."""

    @pytest.mark.parametrize(
        "hours, expected_km",
        [
            (1.0, 120.0),    # 1 hour
            (2.0, 240.0),    # 2 hours
            (2.5, 300.0),    # 2.5 hours - typical "day trip" max
            (3.5, 420.0),    # 3.5 hours - longer trip
        ],
    )
    def test_hours_to_km(self, hours, expected_km):
        """Test time to distance conversion at 120 km/h."""
        assert estimate_max_distance_km(hours) == expected_km


class TestAPIKeyHandling:
    """Test API key validation."""

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch("powder.tools.routing.os.environ.get", return_value=None):
            with pytest.raises(ValueError, match="API_KEY"):
                get_drive_time(42.36, -71.06, 44.53, -72.79)


class TestCoordinateFormatting:
    """Test that coordinates are passed correctly to ORS API."""

    @pytest.mark.parametrize(
        "start_lat, start_lon, end_lat, end_lon, expected_start, expected_end",
        [
            # Boston to Stowe
            (42.36, -71.06, 44.53, -72.79, "-71.06,42.36", "-72.79,44.53"),
            # NYC to Jay Peak
            (40.71, -74.01, 44.97, -72.47, "-74.01,40.71", "-72.47,44.97"),
        ],
    )
    def test_coordinates_formatted_as_lon_lat(
        self, start_lat, start_lon, end_lat, end_lon, expected_start, expected_end
    ):
        """Test ORS receives coordinates in lon,lat order (GeoJSON standard)."""
        mock_response = make_mock_response(3600, 100000)

        with patch("powder.tools.routing.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(json=MagicMock(return_value=mock_response))
            get_drive_time(start_lat, start_lon, end_lat, end_lon)

            # Check the params passed to httpx.get
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs["params"]["start"] == expected_start
            assert call_kwargs["params"]["end"] == expected_end


@pytest.mark.network
class TestLiveAPI:
    """Test against live OpenRouteService API."""

    def test_boston_to_stowe(self):
        """Fetch real drive time from Boston to Stowe."""
        # Boston
        start_lat, start_lon = 42.3601, -71.0589
        # Stowe
        end_lat, end_lon = 44.5258, -72.7858

        result = get_drive_time(start_lat, start_lon, end_lat, end_lon)

        # Stowe is about 3-3.5 hours from Boston
        assert 150 < result["duration_minutes"] < 240
        assert 250 < result["distance_km"] < 350
        assert result["distance_mi"] > 0
