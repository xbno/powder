"""
Script to add missing mountains via Claude Code CLI.

Usage:
    python scripts/seed_missing_mountains.py              # List missing mountains
    python scripts/seed_missing_mountains.py --run        # Add all via Claude
    python scripts/seed_missing_mountains.py --run --num 1  # Add first N only
"""

import argparse
import json
import subprocess
from pathlib import Path

# Major alpine ski resorts by state (from skimap.org)
# Filtered to ~30 larger resorts for POC
ALL_MOUNTAINS = {
    "VT": [
        # "Bolton Valley",
        # "Bromley Mountain",
        # "Burke Mountain",
        "Jay Peak",
        "Killington",
        "Mad River Glen",
        # "Magic Mountain",
        "Mount Snow",
        "Okemo",
        # "Pico Mountain",
        "Smugglers' Notch",
        "Stowe",
        "Stratton",
        "Sugarbush",
        # "Saskadena Six",
    ],
    "NH": [
        "Attitash",
        # "Black Mountain",
        "Bretton Woods",
        "Cannon Mountain",
        "Cranmore",
        # "Crotched Mountain",
        "Gunstock",
        # "King Pine",
        "Loon Mountain",
        "Mount Sunapee",
        # "Pats Peak",
        # "Ragged Mountain",
        "Waterville Valley",
        "Wildcat Mountain",
    ],
    "ME": [
        # "Big Rock Mountain",
        # "Camden Snow Bowl",
        # "Lost Valley",
        # "Mt. Abram",
        # "Pleasant Mountain",
        "Saddleback",
        "Sugarloaf",
        "Sunday River",
    ],
    "MA": [
        "Berkshire East",
        # "Blue Hills",
        # "Bousquet Mountain",
        "Jiminy Peak",
        "Nashoba Valley",
        # "Ski Butternut",
        "Wachusett Mountain",
    ],
    "CT": [
        # "Mohawk Mountain",
        # "Mount Southington",
        # "Powder Ridge",
        # "Ski Sundown",
    ],
    "NY": [
        "Belleayre Mountain",
        "Gore Mountain",
        # "Greek Peak",
        "Holiday Valley",
        "Hunter Mountain",
        "Whiteface",
        "Windham Mountain",
    ],
}

DATA_FILE = Path(__file__).parent.parent / "powder" / "data" / "mountains.jsonl"
PROJECT_ROOT = Path(__file__).parent.parent


def load_existing() -> set[str]:
    """Load existing mountain names (normalized)."""
    existing = set()
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            for line in f:
                if line.strip():
                    name = json.loads(line)["name"].lower()
                    existing.add(name)
    return existing


def get_missing() -> list[tuple[str, str]]:
    """Get (name, state) tuples for missing mountains."""
    existing = load_existing()
    missing = []
    for state, mountains in ALL_MOUNTAINS.items():
        for name in mountains:
            if name.lower() not in existing:
                missing.append((name, state))
    return missing


ALLOWED_TOOLS = [
    "WebSearch",
    "WebFetch",
    "Bash(.venv/bin/python -m powder.tools.validate_mountain:*)",
    "Bash(make seed-db:*)",
]


def add_mountain(name: str) -> bool:
    """Call Claude CLI with /add_mountain command."""
    prompt = f'/add_mountain "{name}"'
    print(f"\n{'='*60}")
    print(f"Adding: {name}")
    print(f"{'='*60}")

    result = subprocess.run(
        [
            "claude",
            "-p",  # print mode - non-interactive, exits when done
            "--permission-mode",
            "acceptEdits",
            # "--allowedTools", # fails, dunno why
            # ",".join(ALLOWED_TOOLS),
            prompt,
        ],
        cwd=PROJECT_ROOT,
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Add missing ski mountains via Claude Code"
    )
    parser.add_argument(
        "--run", action="store_true", help="Actually run Claude to add mountains"
    )
    parser.add_argument(
        "--num", type=int, default=None, help="Limit number of mountains to add"
    )
    args = parser.parse_args()

    missing = get_missing()

    if not missing:
        print("All mountains are already in the database!")
        return

    print(f"Found {len(missing)} missing mountains:\n")
    for i, (name, state) in enumerate(missing, 1):
        print(f"  {i:2}. {name} ({state})")

    if not args.run:
        print(f"\nRun with --run to add these via Claude Code")
        return

    to_add = missing[: args.num] if args.num else missing
    print(f"\nAdding {len(to_add)} mountains via Claude Code...\n")

    for name, state in to_add:
        success = add_mountain(name)
        if not success:
            print(f"Failed to add {name}, stopping.")
            break


if __name__ == "__main__":
    main()
