"""Tests for crowd calendar."""

from datetime import date

import pytest

from powder.tools.crowds import get_crowd_context


class TestHolidayPeriods:
    """Test major holiday detection."""

    @pytest.mark.parametrize(
        "target_date,expected_level",
        [
            (date(2025, 12, 24), "extreme"),  # Christmas Eve
            (date(2025, 12, 25), "extreme"),  # Christmas
            (date(2025, 12, 28), "extreme"),  # Between Christmas & NY
            (date(2025, 12, 31), "extreme"),  # New Year's Eve
            (date(2025, 1, 1), "extreme"),  # New Year's Day
            (date(2025, 1, 2), "extreme"),  # Jan 2
        ],
    )
    def test_christmas_new_years(self, target_date, expected_level):
        result = get_crowd_context(target_date, "VT")
        assert result["crowd_level"] == expected_level
        assert result["is_holiday_weekend"] is True


class TestMLKWeekend:
    """Test MLK weekend detection."""

    @pytest.mark.parametrize(
        "target_date,expected_level",
        [
            (date(2025, 1, 18), "high"),  # Saturday before MLK
            (date(2025, 1, 19), "high"),  # Sunday before MLK
            (date(2025, 1, 20), "high"),  # MLK Monday
        ],
    )
    def test_mlk_weekend(self, target_date, expected_level):
        result = get_crowd_context(target_date, "VT")
        assert result["crowd_level"] == expected_level
        assert result["is_holiday_weekend"] is True


class TestPresidentsDay:
    """Test Presidents Day weekend detection (part of MA vacation week)."""

    @pytest.mark.parametrize(
        "target_date,expected_level",
        [
            (date(2025, 2, 15), "extreme"),  # Saturday - MA vacation weekend
            (date(2025, 2, 16), "extreme"),  # Sunday - MA vacation weekend
            (date(2025, 2, 17), "high"),  # Presidents Day Monday - weekday during vacation
        ],
    )
    def test_presidents_day_weekend(self, target_date, expected_level):
        # Presidents Day is part of MA vacation week
        result = get_crowd_context(target_date, "VT")
        assert result["crowd_level"] == expected_level
        assert result["vacation_week"] == "MA/NH"


class TestVacationWeeks:
    """Test school vacation week detection."""

    def test_ma_vacation_week_vt_weekend(self):
        # MA vacation week, Saturday, Vermont
        result = get_crowd_context(date(2025, 2, 15), "VT")
        assert result["vacation_week"] == "MA/NH"
        assert result["crowd_level"] == "extreme"

    def test_ma_vacation_week_vt_weekday(self):
        # MA vacation week, Wednesday, Vermont
        result = get_crowd_context(date(2025, 2, 19), "VT")
        assert result["vacation_week"] == "MA/NH"
        assert result["crowd_level"] == "high"

    def test_ma_vacation_week_maine_weekend(self):
        # MA vacation week, Saturday, Maine (less affected)
        result = get_crowd_context(date(2025, 2, 15), "ME")
        assert result["vacation_week"] == "MA/NH"
        assert result["crowd_level"] == "high"
        assert "Maine" in result["crowd_note"]

    def test_ny_vacation_week_vt_weekend(self):
        # NY vacation week, Saturday (Mar 1, 2025), Vermont
        # NY vacation is week after Presidents Day: Feb 24 - Mar 2
        result = get_crowd_context(date(2025, 3, 1), "VT")
        assert result["vacation_week"] == "NY"
        assert result["crowd_level"] == "extreme"

    def test_ny_vacation_week_maine_weekend(self):
        # NY vacation week, Saturday (Mar 1, 2025), Maine (escape route)
        result = get_crowd_context(date(2025, 3, 1), "ME")
        assert result["vacation_week"] == "NY"
        assert result["crowd_level"] == "moderate"
        assert "escape" in result["crowd_note"].lower() or "fewer" in result["crowd_note"].lower()


class TestRegularDays:
    """Test non-holiday periods."""

    def test_regular_weekday(self):
        # Regular Wednesday in January
        result = get_crowd_context(date(2025, 1, 8), "VT")
        assert result["crowd_level"] == "normal"
        assert result["vacation_week"] is None
        assert result["is_holiday_weekend"] is False

    def test_regular_weekend(self):
        # Regular Saturday in January (not holiday)
        result = get_crowd_context(date(2025, 1, 11), "VT")
        assert result["crowd_level"] == "moderate"
        assert result["vacation_week"] is None
        assert result["is_holiday_weekend"] is False
