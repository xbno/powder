"""
CLI for running ski recommendations.

Usage:
    # Live query (uses real weather API)
    python -m powder "Best powder day with Ikon pass?"

    # Historic query (uses fixtures from that date)
    python -m powder --date 2025-02-17 "Best powder day with Ikon pass?"

    # Use Pipeline instead of ReAct
    python -m powder --pipeline "Best powder today?"

    # Save execution trace for debugging
    python -m powder --date 2025-03-29 --save-trace "Epic pass powder?"
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

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
    parser.add_argument(
        "--save-trace",
        action="store_true",
        help="Save execution trace to traces/ directory",
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
    # Configure DSPy with LM we can access later for history
    lm = dspy.LM(args.model)
    dspy.configure(lm=lm)

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
            output, raw_result = _run_agent(query, query_date, location, args.pipeline)
    else:
        output, raw_result = _run_agent(query, query_date, location, args.pipeline)

    print(f"\n{output}")

    # Save trace if requested
    if getattr(args, 'save_trace', False):
        _save_trace(
            query=query,
            args=args,
            location=location,
            query_date=query_date,
            lm_history=lm.history,
            raw_result=raw_result,
            use_pipeline=args.pipeline,
        )


def _run_agent(query: str, query_date: date | None, location: dict, use_pipeline: bool) -> tuple[str, dict]:
    """Run either Pipeline or ReAct agent. Returns (output_string, raw_result)."""
    if use_pipeline:
        from powder.pipeline import SkiPipeline

        pipeline = SkiPipeline()
        result = pipeline(
            query=query,
            current_date=query_date,
            user_location=location,
        )
        # Build verbose output showing each pipeline stage
        import textwrap
        W = 90  # wrap width

        sections = []

        # 1. Parsed query
        parsed = result.parsed
        sections.append("PARSED QUERY")
        sections.append(f"  Date: {parsed.target_date}")
        if parsed.pass_type:
            sections.append(f"  Pass: {parsed.pass_type}")
        if parsed.max_drive_hours:
            sections.append(f"  Max drive: {parsed.max_drive_hours}h")
        if parsed.vibe:
            sections.append(f"  Vibe: {parsed.vibe}")
        if parsed.skill_level:
            sections.append(f"  Skill: {parsed.skill_level}")
        filters = []
        if parsed.needs_terrain_parks: filters.append("parks")
        if parsed.needs_glades: filters.append("glades")
        if parsed.needs_beginner_terrain: filters.append("beginner")
        if parsed.needs_expert_terrain: filters.append("expert")
        if parsed.needs_night_skiing: filters.append("night")
        if filters:
            sections.append(f"  Needs: {', '.join(filters)}")

        # 2. Day assessment
        if hasattr(result, 'day_assessment') and result.day_assessment:
            da = result.day_assessment
            sections.append("")
            sections.append("DAY ASSESSMENT")
            sections.append(f"  Quality:  {da.day_quality}")
            sections.append(f"  Best:     {da.best_available}")
            wrapped = textwrap.fill(da.day_context, width=W, initial_indent="  Context:  ", subsequent_indent="            ")
            sections.append(wrapped)

        # 3. Scored mountains (top 5)
        if result.scores:
            sections.append("")
            sections.append("MOUNTAIN SCORES")
            for s in result.scores[:5]:
                name = s["mountain"]["name"]
                score = s["score"]
                fresh = s["mountain"].get("conditions", {}).get("fresh_snow_24h_in", "?")
                temp = s["mountain"].get("conditions", {}).get("temp_f", "?")
                drive = s["mountain"].get("drive_time", {}).get("duration_minutes")
                drive_str = f"{drive/60:.1f}h" if drive else "?"
                sections.append(f"  {score:>5}  {name:<25} {fresh}\" fresh | {temp}°F | {drive_str} drive")

        # 4. Final recommendation
        sections.append("")
        sections.append("RECOMMENDATION")
        for line in textwrap.wrap(result.top_pick, width=W):
            sections.append(f"  {line}")
        sections.append("")
        sections.append("ALTERNATIVES")
        for line in textwrap.wrap(result.alternatives, width=W):
            sections.append(f"  {line}")
        sections.append("")
        sections.append("CAVEAT")
        for line in textwrap.wrap(result.caveat, width=W):
            sections.append(f"  {line}")

        output = "\n".join(sections)

        # Extract intermediate results for trace
        raw_result = {
            "agent": "pipeline",
            "top_pick": result.top_pick,
            "alternatives": result.alternatives,
            "caveat": result.caveat,
            "parsed": result.parsed.model_dump() if hasattr(result.parsed, 'model_dump') else str(result.parsed),
            "candidates": result.candidates,
            "day_assessment": {
                "day_quality": result.day_assessment.day_quality,
                "best_available": result.day_assessment.best_available,
                "day_context": result.day_assessment.day_context,
            } if hasattr(result, 'day_assessment') else None,
            "scores": result.scores,
            "crowd_info": result.crowd_info if hasattr(result, 'crowd_info') else None,
        }
        return output, raw_result
    else:
        from powder.agent import recommend

        recommendation = recommend(
            query=query,
            current_date=query_date,
            current_location=location,
        )
        raw_result = {
            "agent": "react",
            "recommendation": recommendation,
        }
        return recommendation, raw_result


def _save_trace(
    query: str,
    args,
    location: dict,
    query_date: date | None,
    lm_history: list,
    raw_result: dict,
    use_pipeline: bool,
):
    """Save execution trace to a JSON file."""
    traces_dir = Path(__file__).parent.parent / "traces"
    traces_dir.mkdir(exist_ok=True)

    # Build filename
    agent_type = "pipeline" if use_pipeline else "react"
    date_str = args.date or "live"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{agent_type}_{date_str}_{timestamp}.json"

    # Process LM history for JSON serialization
    serializable_history = []
    for entry in lm_history:
        serializable_entry = {
            "prompt": entry.get("prompt"),
            "messages": entry.get("messages"),
            "outputs": entry.get("outputs"),
            "usage": entry.get("usage"),
            "cost": entry.get("cost"),
            "timestamp": entry.get("timestamp"),
            "model": entry.get("model"),
        }
        serializable_history.append(serializable_entry)

    trace = {
        "meta": {
            "query": query,
            "agent": agent_type,
            "date": args.date,
            "location": location,
            "model": args.model,
            "timestamp": datetime.now().isoformat(),
        },
        "result": raw_result,
        "lm_history": serializable_history,
    }

    # Save trace
    trace_path = traces_dir / filename
    with open(trace_path, "w") as f:
        json.dump(trace, f, indent=2, default=str)

    print(f"\n📝 Trace saved to: {trace_path}")


if __name__ == "__main__":
    main()
