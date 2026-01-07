"""
Fetch historic weather data from Open-Meteo for backtesting.

This script pulls real weather/snow data from the ski season and saves
it as JSON fixtures for reproducible evaluation.

Usage:
    # Fetch full 2024-2025 season (Dec 1 - Apr 15)
    python -m powder.evals.fetch_historic

    # Fetch specific date range
    python -m powder.evals.fetch_historic --start 2025-01-01 --end 2025-01-31

    # Show summary of fetched data
    python -m powder.evals.fetch_historic --summary
"""

import json
import httpx
from datetime import date, timedelta
from pathlib import Path
from time import sleep

def get_mountains_from_db() -> list[dict]:
    """
    Load mountains from the database/JSONL file.

    This ensures we always fetch data for all mountains in the system,
    even when new ones are added.
    """
    from pathlib import Path
    import json

    # Try loading from JSONL file first (source of truth)
    jsonl_path = Path(__file__).parent.parent / "data" / "mountains.jsonl"
    if jsonl_path.exists():
        mountains = []
        with open(jsonl_path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    mountains.append({
                        "name": data["name"],
                        "lat": data["lat"],
                        "lon": data["lon"],
                        "state": data.get("state", ""),
                    })
        return mountains

    # Fallback: load from SQLite database
    try:
        from sqlalchemy.orm import sessionmaker
        from powder.tools.database import get_engine, Mountain

        db_path = Path(__file__).parent.parent / "data" / "mountains.db"
        if db_path.exists():
            engine = get_engine(db_path)
            Session = sessionmaker(bind=engine)
            session = Session()

            mountains = []
            for m in session.query(Mountain).all():
                mountains.append({
                    "name": m.name,
                    "lat": m.lat,
                    "lon": m.lon,
                    "state": m.state or "",
                })
            session.close()
            return mountains
    except Exception:
        pass

    raise FileNotFoundError(
        "No mountains found. Ensure mountains.jsonl or mountains.db exists."
    )

# Open-Meteo historical API endpoint
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Default season: Dec 1, 2024 - Apr 15, 2025
DEFAULT_START = date(2024, 12, 1)
DEFAULT_END = date(2025, 4, 15)


def fetch_mountain_season(
    mountain: dict,
    start_date: date,
    end_date: date,
) -> dict[str, dict]:
    """
    Fetch weather data for a single mountain over a date range.

    Open-Meteo allows fetching multiple days in one request, which is
    much more efficient than day-by-day requests.

    Returns:
        Dict mapping date string (YYYY-MM-DD) -> conditions dict
    """
    params = {
        "latitude": mountain["lat"],
        "longitude": mountain["lon"],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": [
            "temperature_2m",
            "wind_speed_10m",
            "visibility",
            "weather_code",
            "snowfall",
            "snow_depth",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "snowfall_sum",
        ],
        "timezone": "America/New_York",
    }

    response = httpx.get(ARCHIVE_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    hourly = data.get("hourly", {})

    dates = daily.get("time", [])
    results = {}

    for i, date_str in enumerate(dates):
        # Daily aggregates
        snowfall_sum = daily.get("snowfall_sum", [None] * len(dates))[i]
        temp_max = daily.get("temperature_2m_max", [None] * len(dates))[i]
        temp_min = daily.get("temperature_2m_min", [None] * len(dates))[i]

        # Get noon values from hourly (index = day * 24 + 12)
        noon_idx = i * 24 + 12
        if noon_idx < len(hourly.get("temperature_2m", [])):
            temp_noon = hourly["temperature_2m"][noon_idx]
            wind_noon = hourly.get("wind_speed_10m", [0] * (noon_idx + 1))[noon_idx]
            vis_noon = hourly.get("visibility", [10000] * (noon_idx + 1))[noon_idx]
            weather_code = hourly.get("weather_code", [0] * (noon_idx + 1))[noon_idx]
            snow_depth = hourly.get("snow_depth", [0] * (noon_idx + 1))[noon_idx]
        else:
            temp_noon = (temp_max + temp_min) / 2 if temp_max and temp_min else 0
            wind_noon = 10
            vis_noon = 10000
            weather_code = 0
            snow_depth = 0

        # Calculate fresh snow in last 24h from hourly data
        if noon_idx >= 24:
            hourly_snowfall = hourly.get("snowfall", [])
            fresh_24h = sum(
                s for s in hourly_snowfall[noon_idx - 24:noon_idx]
                if s is not None
            )
        else:
            fresh_24h = snowfall_sum or 0

        # Handle None values
        snow_depth = snow_depth or 0
        temp_noon = temp_noon or 0
        wind_noon = wind_noon or 0
        vis_noon = vis_noon or 10000

        results[date_str] = {
            "fresh_snow_24h_cm": round(fresh_24h, 1),
            "fresh_snow_24h_in": round(fresh_24h / 2.54, 1),
            "snow_depth_cm": round(snow_depth, 1),
            "snow_depth_in": round(snow_depth / 2.54, 1),
            "temp_c": round(temp_noon, 1),
            "temp_f": round(temp_noon * 9 / 5 + 32, 1),
            "temp_max_f": round(temp_max * 9 / 5 + 32, 1) if temp_max else None,
            "temp_min_f": round(temp_min * 9 / 5 + 32, 1) if temp_min else None,
            "wind_kph": round(wind_noon, 1),
            "wind_mph": round(wind_noon / 1.609, 1),
            "visibility_m": round(vis_noon, 0),
            "visibility_km": round(vis_noon / 1000, 1),
            "visibility_mi": round(vis_noon / 1609, 1),
            "weather_code": weather_code,
        }

    return results


def fetch_full_season(
    start_date: date = DEFAULT_START,
    end_date: date = DEFAULT_END,
    output_dir: Path = None,
) -> dict:
    """
    Fetch weather data for all mountains over the full season.

    Reads mountains dynamically from mountains.jsonl, so new mountains
    are automatically included when you re-run.

    Saves data in two formats:
    1. By mountain: {mountain_name}.json with all dates
    2. By date: by_date.json with {date: {mountain: conditions}}

    Args:
        start_date: Start of date range
        end_date: End of date range
        output_dir: Where to save fixtures

    Returns:
        Combined data structure
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "fixtures"

    output_dir.mkdir(exist_ok=True)

    # Load mountains from database (dynamic - picks up new mountains automatically)
    mountains = get_mountains_from_db()

    print(f"Fetching {start_date} to {end_date}")
    print(f"Mountains: {len(mountains)}")
    print(f"Days: {(end_date - start_date).days + 1}")
    print()

    # Fetch each mountain
    all_data = {}  # {mountain_name: {date: conditions}}

    for mountain in mountains:
        name = mountain["name"]
        print(f"Fetching {name}...", end=" ", flush=True)

        try:
            mountain_data = fetch_mountain_season(mountain, start_date, end_date)
            all_data[name] = mountain_data
            print(f"OK ({len(mountain_data)} days)")

            # Save individual mountain file
            safe_name = name.lower().replace(" ", "_").replace("'", "")
            outfile = output_dir / f"{safe_name}.json"
            with open(outfile, "w") as f:
                json.dump({
                    "mountain": name,
                    "state": mountain["state"],
                    "lat": mountain["lat"],
                    "lon": mountain["lon"],
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "conditions": mountain_data,
                }, f, indent=2)

        except Exception as e:
            print(f"ERROR: {e}")
            all_data[name] = {"error": str(e)}

        # Rate limit
        sleep(1)

    # Build date-indexed structure from fetched data
    print("\nBuilding date index...")

    # Get dates from first successful mountain
    sample_dates = []
    for mtn_data in all_data.values():
        if isinstance(mtn_data, dict) and "error" not in mtn_data:
            sample_dates = list(mtn_data.keys())
            break

    # Build {date: {mountain: conditions}} structure
    by_date = {}
    for date_str in sample_dates:
        by_date[date_str] = {}
        for mtn_name, mtn_data in all_data.items():
            if isinstance(mtn_data, dict) and date_str in mtn_data:
                by_date[date_str][mtn_name] = mtn_data[date_str]

    # Save combined by-date file
    successful_mountains = [k for k, v in all_data.items() if isinstance(v, dict) and "error" not in v]
    combined_file = output_dir / "by_date.json"
    with open(combined_file, "w") as f:
        json.dump({
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "mountains": successful_mountains,
            "dates": by_date,
        }, f)  # No indent - file would be huge

    print(f"Saved {combined_file} ({len(by_date)} dates, {len(successful_mountains)} mountains)")

    # Save metadata
    meta_file = output_dir / "metadata.json"
    with open(meta_file, "w") as f:
        json.dump({
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "mountains": successful_mountains,
            "total_days": len(by_date),
            "total_mountains": len(successful_mountains),
            "fetched_at": date.today().isoformat(),
        }, f, indent=2)

    print(f"\nDone! Data saved to {output_dir}")
    return by_date


def load_conditions_for_date(target_date: date | str, fixtures_dir: Path = None) -> dict[str, dict]:
    """
    Load conditions for all mountains on a specific date.

    Args:
        target_date: Date to load (date object or YYYY-MM-DD string)

    Returns:
        Dict mapping mountain name -> conditions dict
    """
    if fixtures_dir is None:
        fixtures_dir = Path(__file__).parent / "fixtures"

    if isinstance(target_date, date):
        date_str = target_date.isoformat()
    else:
        date_str = target_date

    # Try loading from by_date.json
    by_date_file = fixtures_dir / "by_date.json"
    if by_date_file.exists():
        with open(by_date_file) as f:
            data = json.load(f)
            dates = data.get("dates", {})
            if date_str in dates:
                return dates[date_str]

    raise FileNotFoundError(
        f"No data for {date_str}. Run 'python -m powder.evals.fetch_historic' first."
    )


def summarize_fixtures(fixtures_dir: Path = None):
    """Print summary of available fixture data."""
    if fixtures_dir is None:
        fixtures_dir = Path(__file__).parent / "fixtures"

    meta_file = fixtures_dir / "metadata.json"
    if not meta_file.exists():
        print("No fixtures found. Run 'python -m powder.evals.fetch_historic' first.")
        return

    with open(meta_file) as f:
        meta = json.load(f)

    print("\n=== Historic Weather Fixtures ===\n")
    print(f"Date range: {meta['start_date']} to {meta['end_date']}")
    print(f"Total days: {meta['total_days']}")
    print(f"Mountains: {len(meta['mountains'])}")
    print(f"Fetched: {meta['fetched_at']}")
    print()

    # Load by_date to find interesting days
    by_date_file = fixtures_dir / "by_date.json"
    if by_date_file.exists():
        with open(by_date_file) as f:
            data = json.load(f)
            dates = data.get("dates", {})

        # Find best powder days
        powder_days = []
        for date_str, conditions in dates.items():
            max_fresh = max(
                (c.get("fresh_snow_24h_in", 0) for c in conditions.values()),
                default=0
            )
            if max_fresh >= 6:  # 6+ inches
                best_mtn = max(
                    conditions.items(),
                    key=lambda x: x[1].get("fresh_snow_24h_in", 0)
                )
                powder_days.append((date_str, best_mtn[0], max_fresh))

        powder_days.sort(key=lambda x: x[2], reverse=True)

        print("Top 10 powder days:")
        for date_str, mtn, fresh in powder_days[:10]:
            print(f"  {date_str}: {mtn} - {fresh:.1f}\" fresh")

        # Find coldest days
        print("\nColdest days:")
        cold_days = []
        for date_str, conditions in dates.items():
            min_temp = min(
                (c.get("temp_f", 100) for c in conditions.values()),
                default=100
            )
            if min_temp < 0:
                cold_days.append((date_str, min_temp))

        cold_days.sort(key=lambda x: x[1])
        for date_str, temp in cold_days[:5]:
            print(f"  {date_str}: {temp:.0f}°F")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch historic weather data for backtesting"
    )
    parser.add_argument(
        "--start",
        type=str,
        default=DEFAULT_START.isoformat(),
        help=f"Start date YYYY-MM-DD (default: {DEFAULT_START})",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=DEFAULT_END.isoformat(),
        help=f"End date YYYY-MM-DD (default: {DEFAULT_END})",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary of existing fixtures",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory for fixtures",
    )

    args = parser.parse_args()

    if args.summary:
        summarize_fixtures(args.output)
    else:
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)

        mountains = get_mountains_from_db()
        print("Fetching historic weather data for backtesting...")
        print(f"This will fetch {(end - start).days + 1} days x {len(mountains)} mountains")
        print()

        fetch_full_season(start, end, args.output)


if __name__ == "__main__":
    main()
