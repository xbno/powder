"""Crowd calendar for ski mountains."""

from datetime import date, timedelta


def _nthday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth weekday of a month (1-indexed)."""
    first = date(year, month, 1)
    # Days until first occurrence of weekday
    days_until = (weekday - first.weekday()) % 7
    first_occurrence = first + timedelta(days=days_until)
    return first_occurrence + timedelta(weeks=n - 1)


def get_crowd_context(target_date: date, mountain_state: str) -> dict:
    """Assess expected crowds for a date + location.

    Args:
        target_date: The date to check
        mountain_state: Two-letter state code (e.g., "VT", "ME")

    Returns:
        Dictionary with crowd assessment:
        - is_holiday_weekend: bool
        - vacation_week: "MA/NH" | "NY" | None
        - crowd_level: "extreme" | "high" | "moderate" | "normal"
        - crowd_note: str explaining the crowd situation
    """
    year = target_date.year
    is_weekend = target_date.weekday() >= 5  # Sat=5, Sun=6

    # Christmas-New Year's (Dec 24 - Jan 2)
    christmas_start = date(year, 12, 24)
    christmas_end = date(year, 12, 31)
    new_years_end = date(year, 1, 2)

    if christmas_start <= target_date <= christmas_end:
        return {
            "is_holiday_weekend": True,
            "vacation_week": None,
            "crowd_level": "extreme",
            "crowd_note": "Christmas week - expect extreme crowds everywhere",
        }

    if date(year, 1, 1) <= target_date <= new_years_end:
        return {
            "is_holiday_weekend": True,
            "vacation_week": None,
            "crowd_level": "extreme",
            "crowd_note": "New Year's holiday - expect extreme crowds everywhere",
        }

    # MLK Weekend (3rd Monday of January + surrounding weekend)
    mlk_monday = _nthday_of_month(year, 1, 0, 3)  # Monday = 0
    mlk_saturday = mlk_monday - timedelta(days=2)
    mlk_sunday = mlk_monday - timedelta(days=1)

    if target_date in (mlk_saturday, mlk_sunday, mlk_monday):
        return {
            "is_holiday_weekend": True,
            "vacation_week": None,
            "crowd_level": "high",
            "crowd_note": "MLK weekend - expect high crowds",
        }

    # February vacation weeks are key for ski crowds
    # MA/NH February Vacation: week containing Presidents Day (3rd Monday of Feb)
    # NY February Vacation: typically the week AFTER MA/NH
    presidents_monday = _nthday_of_month(year, 2, 0, 3)

    # MA/NH: Saturday before Presidents Day through following Sunday
    ma_vacation_start = presidents_monday - timedelta(days=2)  # Saturday
    ma_vacation_end = presidents_monday + timedelta(days=6)  # Following Sunday

    # NY: Monday after MA vacation ends through following Sunday
    ny_vacation_start = presidents_monday + timedelta(days=7)  # Monday after
    ny_vacation_end = ny_vacation_start + timedelta(days=6)  # Following Sunday

    if ma_vacation_start <= target_date <= ma_vacation_end:
        vacation_week = "MA/NH"
        # Maine gets less NY traffic, so during MA week it's extreme everywhere
        if mountain_state == "ME":
            crowd_level = "high" if is_weekend else "moderate"
            crowd_note = "MA/NH vacation week - Maine less packed than Vermont"
        else:
            crowd_level = "extreme" if is_weekend else "high"
            crowd_note = "MA/NH vacation week - expect extreme crowds"

        return {
            "is_holiday_weekend": is_weekend,
            "vacation_week": vacation_week,
            "crowd_level": crowd_level,
            "crowd_note": crowd_note,
        }

    if ny_vacation_start <= target_date <= ny_vacation_end:
        vacation_week = "NY"
        # Maine is further from NYC, less affected
        if mountain_state == "ME":
            crowd_level = "moderate" if is_weekend else "normal"
            crowd_note = "NY vacation week - Maine gets fewer NYC crowds, good escape option"
        else:
            crowd_level = "extreme" if is_weekend else "high"
            crowd_note = "NY vacation week - VT will be packed, consider Maine"

        return {
            "is_holiday_weekend": is_weekend,
            "vacation_week": vacation_week,
            "crowd_level": crowd_level,
            "crowd_note": crowd_note,
        }

    # Regular weekend vs weekday
    if is_weekend:
        return {
            "is_holiday_weekend": False,
            "vacation_week": None,
            "crowd_level": "moderate",
            "crowd_note": "Regular weekend - typical crowds",
        }

    return {
        "is_holiday_weekend": False,
        "vacation_week": None,
        "crowd_level": "normal",
        "crowd_note": "Weekday - lighter crowds expected",
    }
