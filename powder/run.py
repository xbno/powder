"""CLI for running the ski recommendation agent."""

import argparse
import os
import sys

import dspy
from dotenv import load_dotenv

from powder.agent import recommend, build_user_context
from powder.signatures import ParseSkiQuery


def clarify_date_if_needed(query: str) -> str:
    """Check if query specifies a date, ask user if not."""
    user_context = build_user_context()

    # Use ParseSkiQuery to check if date is specified
    parser = dspy.Predict(ParseSkiQuery)
    result = parser(query=query, user_context=user_context)

    if result.target_date == "unspecified":
        print("When are you looking to ski?")
        print("  1. Today")
        print("  2. Tomorrow")
        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            return f"{query} today"
        else:
            return f"{query} tomorrow"

    return query


def main():
    parser = argparse.ArgumentParser(description="Get ski recommendations")
    parser.add_argument(
        "query",
        nargs="?",
        default="Where should I ski?",
        help="Your ski query (default: 'Where should I ski?')",
    )
    parser.add_argument(
        "--model",
        default="anthropic/claude-haiku-4-5-20251001",
        help="LLM model to use (default: anthropic/claude-haiku-4-5-20251001)",
    )
    args = parser.parse_args()

    # Load .env file
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY") and "anthropic" in args.model:
        print("Error: ANTHROPIC_API_KEY not set in environment or .env file")
        sys.exit(1)

    dspy.configure(lm=dspy.LM(args.model))

    # Clarify date if not specified
    query = clarify_date_if_needed(args.query)

    result = recommend(query)
    print(result)


if __name__ == "__main__":
    main()
