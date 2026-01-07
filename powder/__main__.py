"""
CLI for running ski recommendations.

Usage:
    # Live query (uses real weather API)
    python -m powder "Best powder day with Ikon pass?"

    # Historic query (uses fixtures from that date)
    python -m powder --date 2025-02-17 "Best powder day with Ikon pass?"

    # Use Pipeline instead of ReAct
    python -m powder --pipeline "Best powder today?"
"""

import argparse
import os
import sys
from datetime import date

import dspy


def main():
    parser = argparse.ArgumentParser(
        description="Powder - Ski Mountain Recommendation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m powder "Best powder day with Ikon pass?"
  python -m powder --date 2025-02-17 "Where should I ski today?"
  python -m powder --pipeline "Epic pass, best terrain park?"
  python -m powder --date 2025-01-01 --pipeline "Powder day from Boston"
        """,
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Natural language ski query",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Historic date to use (YYYY-MM-DD format, uses fixtures)",
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Use Pipeline instead of ReAct agent",
    )
    parser.add_argument(
        "--location",
        type=str,
        default="Boston",
        help="Starting location (default: Boston)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="anthropic/claude-haiku-4-5-20251001",
        help="Model to use (default: claude-haiku)",
    )

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Interactive mode if no query provided
    if not args.query:
        print("🎿 Powder - Ski Recommendation Agent")
        print("=" * 40)
        if args.date:
            print(f"Using historic data from: {args.date}")
        print("Type your query (or 'quit' to exit):\n")

        while True:
            try:
                query = input("❄️  ").strip()
                if query.lower() in ("quit", "exit", "q"):
                    break
                if not query:
                    continue

                run_query(query, args)
                print()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
    else:
        run_query(args.query, args)


def run_query(query: str, args):
    """Run a single query with the given arguments."""
    # Configure DSPy
    dspy.configure(lm=dspy.LM(args.model))

    # Parse location
    LOCATIONS = {
        "boston": {"name": "Boston, MA", "lat": 42.3601, "lon": -71.0589},
        "nyc": {"name": "New York, NY", "lat": 40.7128, "lon": -74.0060},
        "hartford": {"name": "Hartford, CT", "lat": 41.7658, "lon": -72.6734},
        "albany": {"name": "Albany, NY", "lat": 42.6526, "lon": -73.7562},
    }
    location = LOCATIONS.get(args.location.lower(), LOCATIONS["boston"])

    # Parse date
    query_date = None
    if args.date:
        query_date = date.fromisoformat(args.date)

    # Run with historic fixtures if date provided
    if args.date:
        from powder.evals.backtest import load_fixture, mock_weather_api, mock_routing_api

        try:
            conditions = load_fixture(args.date)
        except FileNotFoundError:
            print(f"Error: No fixture data for {args.date}")
            print("Run 'make fetch-historic' to fetch weather data, or use a date in range.")
            return

        print(f"\n📅 Using historic conditions from {args.date}")
        print("-" * 40)

        with mock_weather_api(conditions), mock_routing_api():
            result = _run_agent(query, query_date, location, args.pipeline)
    else:
        result = _run_agent(query, query_date, location, args.pipeline)

    print(f"\n{result}")


def _run_agent(query: str, query_date: date | None, location: dict, use_pipeline: bool) -> str:
    """Run either Pipeline or ReAct agent."""
    if use_pipeline:
        from powder.pipeline import SkiPipeline

        pipeline = SkiPipeline()
        result = pipeline(
            query=query,
            current_date=query_date,
            user_location=location,
        )
        return f"**{result.top_pick}**\n\nAlternatives: {result.alternatives}\n\n{result.caveat}"
    else:
        from powder.agent import recommend

        return recommend(
            query=query,
            current_date=query_date,
            current_location=location,
        )


if __name__ == "__main__":
    main()
