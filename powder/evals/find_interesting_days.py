"""
Find interesting days in historic weather data for spot-checking and eval examples.

This script analyzes the fetched historic weather fixtures to find days with
notable characteristics that make good test cases:

1. Powder days - High fresh snow variance (some mountains got dumped on, others didn't)
2. Clear winners - One mountain objectively best based on conditions
3. Extreme cold - Brutally cold days where conditions matter
4. High snow days - Big snow everywhere (tests differentiation)
5. Variable days - Mixed conditions across mountains (tests nuanced ranking)

Usage:
    python -m powder.evals.find_interesting_days
    python -m powder.evals.find_interesting_days --type powder --limit 10
    python -m powder.evals.find_interesting_days --date 2025-01-15
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class DayAnalysis:
    """Analysis of a single day's conditions across mountains."""
    date_str: str
    mountains: dict[str, dict]

    # Computed metrics
    max_fresh_snow: float = 0
    min_fresh_snow: float = 0
    avg_fresh_snow: float = 0
    snow_variance: float = 0

    best_snow_mountain: str = ""
    worst_snow_mountain: str = ""

    coldest_temp: float = 100
    warmest_temp: float = -100
    coldest_mountain: str = ""
    warmest_mountain: str = ""

    def compute_metrics(self):
        """Compute all metrics from mountain conditions."""
        if not self.mountains:
            return

        fresh_snows = []
        temps = []

        for name, cond in self.mountains.items():
            fresh = cond.get("fresh_snow_24h_in", 0) or 0
            temp = cond.get("temp_f", 32) or 32

            fresh_snows.append((fresh, name))
            temps.append((temp, name))

        if fresh_snows:
            fresh_snows.sort(reverse=True)
            self.max_fresh_snow = fresh_snows[0][0]
            self.best_snow_mountain = fresh_snows[0][1]
            self.min_fresh_snow = fresh_snows[-1][0]
            self.worst_snow_mountain = fresh_snows[-1][1]
            self.avg_fresh_snow = sum(f for f, _ in fresh_snows) / len(fresh_snows)
            self.snow_variance = self.max_fresh_snow - self.min_fresh_snow

        if temps:
            temps.sort()
            self.coldest_temp = temps[0][0]
            self.coldest_mountain = temps[0][1]
            self.warmest_temp = temps[-1][0]
            self.warmest_mountain = temps[-1][1]


def load_historic_data(fixtures_dir: Path = None) -> dict:
    """Load the by_date.json fixture file."""
    if fixtures_dir is None:
        fixtures_dir = Path(__file__).parent / "fixtures"

    by_date_file = fixtures_dir / "by_date.json"
    if not by_date_file.exists():
        raise FileNotFoundError(
            f"No fixtures found at {by_date_file}. Run 'make fetch-historic' first."
        )

    with open(by_date_file) as f:
        return json.load(f)


def analyze_all_days(data: dict) -> list[DayAnalysis]:
    """Analyze all days in the dataset."""
    dates_data = data.get("dates", {})
    analyses = []

    for date_str, mountains in dates_data.items():
        analysis = DayAnalysis(date_str=date_str, mountains=mountains)
        analysis.compute_metrics()
        analyses.append(analysis)

    return analyses


def find_powder_days(analyses: list[DayAnalysis], limit: int = 10) -> list[DayAnalysis]:
    """
    Find days with high snow variance - some mountains got powder, others didn't.
    These are great test cases because there's a clear "right" answer.
    """
    # Sort by snow variance (difference between best and worst)
    sorted_days = sorted(analyses, key=lambda a: a.snow_variance, reverse=True)
    return sorted_days[:limit]


def find_big_snow_days(analyses: list[DayAnalysis], limit: int = 10) -> list[DayAnalysis]:
    """
    Find days with the most fresh snow overall.
    Good for testing powder-chasing queries.
    """
    sorted_days = sorted(analyses, key=lambda a: a.max_fresh_snow, reverse=True)
    return sorted_days[:limit]


def find_cold_days(analyses: list[DayAnalysis], limit: int = 10) -> list[DayAnalysis]:
    """
    Find the coldest days.
    Good for testing weather-conscious recommendations.
    """
    sorted_days = sorted(analyses, key=lambda a: a.coldest_temp)
    return sorted_days[:limit]


def find_clear_winner_days(analyses: list[DayAnalysis], limit: int = 10) -> list[DayAnalysis]:
    """
    Find days where one mountain is clearly better than others.
    Criteria: High snow variance AND the best mountain has significant snow.
    """
    # Filter to days where best mountain has 4+ inches AND variance is high
    candidates = [
        a for a in analyses
        if a.max_fresh_snow >= 4 and a.snow_variance >= 3
    ]
    sorted_days = sorted(candidates, key=lambda a: a.snow_variance, reverse=True)
    return sorted_days[:limit]


def find_ambiguous_days(analyses: list[DayAnalysis], limit: int = 10) -> list[DayAnalysis]:
    """
    Find days where multiple mountains are roughly equal.
    Good for testing tie-breaking logic and preference handling.
    """
    # Low variance but decent conditions
    candidates = [
        a for a in analyses
        if a.snow_variance < 2 and a.avg_fresh_snow >= 1
    ]
    sorted_days = sorted(candidates, key=lambda a: a.avg_fresh_snow, reverse=True)
    return sorted_days[:limit]


def print_day_summary(analysis: DayAnalysis, verbose: bool = False):
    """Print a summary of a day's conditions."""
    print(f"\n  {analysis.date_str}:")
    print(f"    Best snow: {analysis.best_snow_mountain} ({analysis.max_fresh_snow:.1f}\")")
    print(f"    Worst snow: {analysis.worst_snow_mountain} ({analysis.min_fresh_snow:.1f}\")")
    print(f"    Variance: {analysis.snow_variance:.1f}\" | Avg: {analysis.avg_fresh_snow:.1f}\"")
    print(f"    Coldest: {analysis.coldest_mountain} ({analysis.coldest_temp:.0f}°F)")

    if verbose:
        print(f"    All mountains:")
        for name, cond in sorted(analysis.mountains.items(),
                                  key=lambda x: x[1].get("fresh_snow_24h_in", 0) or 0,
                                  reverse=True):
            fresh = cond.get("fresh_snow_24h_in", 0) or 0
            temp = cond.get("temp_f", 32) or 32
            print(f"      {name}: {fresh:.1f}\" fresh, {temp:.0f}°F")


def get_day_details(date_str: str, fixtures_dir: Path = None) -> DayAnalysis | None:
    """Get detailed analysis for a specific date."""
    data = load_historic_data(fixtures_dir)
    dates_data = data.get("dates", {})

    if date_str not in dates_data:
        return None

    analysis = DayAnalysis(date_str=date_str, mountains=dates_data[date_str])
    analysis.compute_metrics()
    return analysis


def generate_eval_candidates(analyses: list[DayAnalysis]) -> dict:
    """
    Generate candidate days for eval examples.

    Returns a dict with categorized days that would make good test cases.
    """
    return {
        "powder_variance": find_powder_days(analyses, 5),
        "big_snow": find_big_snow_days(analyses, 5),
        "cold_days": find_cold_days(analyses, 5),
        "clear_winners": find_clear_winner_days(analyses, 5),
        "ambiguous": find_ambiguous_days(analyses, 5),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Find interesting days in historic weather data"
    )
    parser.add_argument(
        "--type",
        choices=["powder", "snow", "cold", "winner", "ambiguous", "all"],
        default="all",
        help="Type of interesting days to find",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of days to show per category",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Show details for a specific date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all mountain conditions for each day",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON for programmatic use",
    )

    args = parser.parse_args()

    # Load data
    try:
        data = load_historic_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Single date lookup
    if args.date:
        analysis = get_day_details(args.date)
        if analysis:
            print(f"\n=== Conditions for {args.date} ===")
            print_day_summary(analysis, verbose=True)
        else:
            print(f"No data for {args.date}")
        return

    # Analyze all days
    analyses = analyze_all_days(data)

    if args.json:
        candidates = generate_eval_candidates(analyses)
        output = {
            category: [
                {
                    "date": a.date_str,
                    "best_mountain": a.best_snow_mountain,
                    "max_fresh_snow_in": a.max_fresh_snow,
                    "snow_variance_in": a.snow_variance,
                    "coldest_temp_f": a.coldest_temp,
                }
                for a in days
            ]
            for category, days in candidates.items()
        }
        print(json.dumps(output, indent=2))
        return

    print(f"\n=== Interesting Days Analysis ===")
    print(f"Total days: {len(analyses)}")
    print(f"Mountains: {len(data.get('mountains', []))}")

    if args.type in ("powder", "all"):
        print(f"\n--- High Snow Variance (Powder at some, not others) ---")
        for day in find_powder_days(analyses, args.limit):
            print_day_summary(day, args.verbose)

    if args.type in ("snow", "all"):
        print(f"\n--- Biggest Snow Days ---")
        for day in find_big_snow_days(analyses, args.limit):
            print_day_summary(day, args.verbose)

    if args.type in ("cold", "all"):
        print(f"\n--- Coldest Days ---")
        for day in find_cold_days(analyses, args.limit):
            print_day_summary(day, args.verbose)

    if args.type in ("winner", "all"):
        print(f"\n--- Clear Winner Days (one mountain obviously best) ---")
        winners = find_clear_winner_days(analyses, args.limit)
        if winners:
            for day in winners:
                print_day_summary(day, args.verbose)
        else:
            print("  No days with clear winners (4\"+ snow, 3\"+ variance)")

    if args.type in ("ambiguous", "all"):
        print(f"\n--- Ambiguous Days (similar conditions, tests tie-breaking) ---")
        ambiguous = find_ambiguous_days(analyses, args.limit)
        if ambiguous:
            for day in ambiguous:
                print_day_summary(day, args.verbose)
        else:
            print("  No ambiguous days found")


if __name__ == "__main__":
    main()
