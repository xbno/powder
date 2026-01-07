"""Validate mountain data for the ski database."""

import json
import sys

from powder.tools.database import validate_mountain


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m powder.tools.validate_mountain '<json_data>'")
        print("Validates mountain data and prints errors if any.")
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)

    is_valid, errors = validate_mountain(data)

    if is_valid:
        print("Valid")
        sys.exit(0)
    else:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
