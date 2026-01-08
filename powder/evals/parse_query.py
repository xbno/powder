"""
Evaluation dataset and metrics for ParseSkiQuery signature.

ParseSkiQuery is highly evaluable with DETERMINISTIC metrics because
outputs are structured fields with known expected values.

Metrics are rule-based (no LLM scoring):
- Exact match on boolean fields (needs_terrain_parks, needs_glades, etc.)
- Exact match on enum fields (pass_type, skill_level, vibe)
- Numeric tolerance on max_drive_hours
- Date parsing accuracy
"""

import dspy
from datetime import date


def make_example(
    query: str,
    user_context: str,
    expected: dict,
) -> dspy.Example:
    """Create a ParseSkiQuery evaluation example."""
    return dspy.Example(
        query=query,
        user_context=user_context,
        **expected,
    ).with_inputs("query", "user_context")


# --- Standard user context (Boston, mid-January) ---
BOSTON_CONTEXT = (
    "Today's date: 2025-01-15\n"
    "Tomorrow's date: 2025-01-16\n"
    "User's location: Boston, MA (42.3601, -71.0589)"
)


# --- Evaluation Examples ---

# 1. Basic powder chase query
POWDER_CHASE = make_example(
    query="Best powder day within 3 hours of Boston, I have an Ikon pass",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_target_date": "today",
        "expected_max_drive_hours": 3.0,
        "expected_pass_type": "ikon",
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": False,
        "expected_needs_night_skiing": False,
        "expected_vibe": "powder_chase",
    },
)

# 2. Park day query
PARK_DAY = make_example(
    query="Looking for a mountain with a good terrain park this weekend, "
    "I'm an intermediate snowboarder",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_needs_terrain_parks": True,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": False,
        "expected_activity": "snowboard",
        "expected_skill_level": "intermediate",
        "expected_vibe": "park_day",
    },
)

# 3. Beginner/learning query
BEGINNER_LESSON = make_example(
    query="Taking my daughter skiing for the first time, "
    "need somewhere with a good learning area and magic carpet",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": True,
        "expected_needs_expert_terrain": False,
        "expected_vibe": "learning",
    },
)

# 4. Expert terrain query
EXPERT_TERRAIN = make_example(
    query="Want to hit some double blacks and steep chutes tomorrow, "
    "advanced skier here",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_target_date": "tomorrow",
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": True,
        "expected_skill_level": "advanced",
    },
)

# 5. Tree skiing / glades query
GLADE_DAY = make_example(
    query="Looking for tree skiing and glades, preferably Epic pass, "
    "max 2.5 hour drive",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_max_drive_hours": 2.5,
        "expected_pass_type": "epic",
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": True,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": False,
    },
)

# 6. Night skiing query
NIGHT_SKIING = make_example(
    query="Any mountains with night skiing? Want to go after work tonight",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_target_date": "today",
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": False,
        "expected_needs_night_skiing": True,
    },
)

# 7. Family day with mixed abilities
FAMILY_DAY = make_example(
    query="Family trip - I want some blacks while my wife teaches our "
    "kids on the bunny hill. Need terrain for everyone.",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": True,  # bunny hill for kids
        "expected_needs_expert_terrain": False,  # blacks aren't double blacks
        "expected_vibe": "family_day",
    },
)

# 8. Indy pass specific
INDY_PASS = make_example(
    query="Where can I use my Indy pass? Don't want to drive more than 1.5 hours",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_max_drive_hours": 1.5,
        "expected_pass_type": "indy",
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": False,
    },
)

# 9. Casual day, no constraints
CASUAL_DAY = make_example(
    query="Just want a chill day on the mountain, nothing too crazy",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": False,
        "expected_vibe": "casual",
    },
)

# 10. Multiple features (park + glades)
PARK_AND_GLADES = make_example(
    query="Looking for somewhere with both terrain parks and tree runs, "
    "Ikon pass preferred",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_pass_type": "ikon",
        "expected_needs_terrain_parks": True,
        "expected_needs_glades": True,
        "expected_needs_beginner_terrain": False,
        "expected_needs_expert_terrain": False,
    },
)

# 11. Specific date
SPECIFIC_DATE = make_example(
    query="Planning a trip for January 20th, intermediate skier with Epic pass",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_target_date": "2025-01-20",
        "expected_pass_type": "epic",
        "expected_skill_level": "intermediate",
        "expected_needs_terrain_parks": False,
        "expected_needs_glades": False,
    },
)

# 12. Snowboarder specific (should not recommend Mad River Glen)
SNOWBOARDER = make_example(
    query="Best snowboarding spot with good parks? Expert rider here.",
    user_context=BOSTON_CONTEXT,
    expected={
        "expected_activity": "snowboard",
        "expected_skill_level": "expert",
        "expected_needs_terrain_parks": True,
        "expected_vibe": "park_day",
    },
)

# All examples
TRAIN_EXAMPLES = [
    POWDER_CHASE,
    PARK_DAY,
    BEGINNER_LESSON,
    EXPERT_TERRAIN,
    GLADE_DAY,
    INDY_PASS,
    CASUAL_DAY,
    PARK_AND_GLADES,
    SPECIFIC_DATE,
]
VAL_EXAMPLES = [
    NIGHT_SKIING,
    FAMILY_DAY,
    SNOWBOARDER,
]

# --- Metric Function ---


def parse_query_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """
    Score a ParseSkiQuery prediction with DETERMINISTIC metrics.

    Scoring breakdown:
    - Boolean fields: exact match (1.0 or 0.0)
    - Enum fields: exact match (1.0 or 0.0)
    - Numeric fields: within tolerance (1.0, 0.5, or 0.0)
    - Date fields: exact match or reasonable interpretation (1.0 or 0.0)

    Returns:
        Float between 0 and 1 (average of all applicable checks)
    """
    scores = []

    # Access the ParsedQuery Pydantic model
    parsed = pred.parsed

    # --- Boolean field checks (exact match) ---
    bool_fields = [
        "needs_terrain_parks",
        "needs_glades",
        "needs_beginner_terrain",
        "needs_expert_terrain",
        "needs_night_skiing",
    ]

    for field in bool_fields:
        expected_key = f"expected_{field}"
        if hasattr(example, expected_key):
            expected = getattr(example, expected_key)
            actual = getattr(parsed, field, None)
            # Pydantic handles bool coercion, but just in case
            if isinstance(actual, str):
                actual = actual.lower() == "true"
            scores.append(1.0 if actual == expected else 0.0)

    # --- Enum field checks (exact match, case-insensitive) ---
    enum_fields = ["pass_type", "skill_level", "activity", "vibe"]

    for field in enum_fields:
        expected_key = f"expected_{field}"
        if hasattr(example, expected_key):
            expected = getattr(example, expected_key)
            actual = getattr(parsed, field, None)

            if expected is None:
                # Pydantic gives us None directly, not "null" string
                scores.append(1.0 if actual is None else 0.0)
            elif actual is None:
                scores.append(0.0)
            else:
                # Case-insensitive match, handle underscore variants
                expected_norm = expected.lower().replace("_", "").replace("-", "")
                actual_norm = str(actual).lower().replace("_", "").replace("-", "")
                scores.append(1.0 if expected_norm == actual_norm else 0.0)

    # --- Numeric field checks (with tolerance) ---
    if hasattr(example, "expected_max_drive_hours"):
        expected = example.expected_max_drive_hours
        actual = parsed.max_drive_hours

        if actual is None:
            scores.append(0.0)
        else:
            try:
                actual = float(actual)
                diff = abs(actual - expected)
                if diff < 0.1:
                    scores.append(1.0)
                elif diff < 0.5:
                    scores.append(0.5)
                else:
                    scores.append(0.0)
            except (ValueError, TypeError):
                scores.append(0.0)

    # --- Date field checks ---
    if hasattr(example, "expected_target_date"):
        expected = example.expected_target_date
        actual = parsed.target_date

        if actual is None:
            scores.append(0.0)
        else:
            actual_str = str(actual).lower().strip()
            expected_str = str(expected).lower().strip()

            # Direct match
            if actual_str == expected_str:
                scores.append(1.0)
            # "today" should resolve to current date in context
            elif expected_str == "today" and actual_str in ["today", "2025-01-15"]:
                scores.append(1.0)
            # "tomorrow" should resolve correctly
            elif expected_str == "tomorrow" and actual_str in [
                "tomorrow",
                "2025-01-16",
            ]:
                scores.append(1.0)
            else:
                scores.append(0.0)

    return sum(scores) / len(scores) if scores else 0.0


def get_examples() -> list[dspy.Example]:
    """Get all examples."""
    return TRAIN_EXAMPLES + VAL_EXAMPLES


def get_trainset() -> list[dspy.Example]:
    """Get training examples (first 9 of 12 = 75%)."""
    return TRAIN_EXAMPLES


def get_valset() -> list[dspy.Example]:
    """Get validation examples (last 3 of 12 = 25%)."""
    return VAL_EXAMPLES


def get_metric():
    """Get the metric function."""
    return parse_query_metric


# --- Detailed scoring for analysis ---


def score_detailed(example: dspy.Example, pred: dspy.Prediction) -> dict:
    """
    Get detailed per-field scoring for error analysis.

    Returns dict with each field's score and values.
    """
    details = {}
    parsed = pred.parsed

    # Boolean fields
    bool_fields = [
        "needs_terrain_parks",
        "needs_glades",
        "needs_beginner_terrain",
        "needs_expert_terrain",
        "needs_night_skiing",
    ]

    for field in bool_fields:
        expected_key = f"expected_{field}"
        if hasattr(example, expected_key):
            expected = getattr(example, expected_key)
            actual = getattr(parsed, field, None)
            if isinstance(actual, str):
                actual = actual.lower() == "true"
            details[field] = {
                "expected": expected,
                "actual": actual,
                "score": 1.0 if actual == expected else 0.0,
            }

    # Enum fields
    enum_fields = ["pass_type", "skill_level", "activity", "vibe"]

    for field in enum_fields:
        expected_key = f"expected_{field}"
        if hasattr(example, expected_key):
            expected = getattr(example, expected_key)
            actual = getattr(parsed, field, None)
            match = False
            if expected is None and actual is None:
                match = True
            elif expected and actual:
                expected_norm = expected.lower().replace("_", "")
                actual_norm = str(actual).lower().replace("_", "")
                match = expected_norm == actual_norm
            details[field] = {
                "expected": expected,
                "actual": actual,
                "score": 1.0 if match else 0.0,
            }

    # Numeric
    if hasattr(example, "expected_max_drive_hours"):
        expected = example.expected_max_drive_hours
        actual = parsed.max_drive_hours
        try:
            actual_f = float(actual) if actual else None
            diff = abs(actual_f - expected) if actual_f else 999
            score = 1.0 if diff < 0.1 else 0.5 if diff < 0.5 else 0.0
        except (ValueError, TypeError):
            actual_f = None
            score = 0.0
        details["max_drive_hours"] = {
            "expected": expected,
            "actual": actual_f,
            "score": score,
        }

    return details


if __name__ == "__main__":
    # Quick test
    import dspy
    from powder.signatures import ParseSkiQuery

    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))

    predictor = dspy.Predict(ParseSkiQuery)

    print("Testing ParseSkiQuery metric...\n")

    total_score = 0.0
    for i, example in enumerate(TRAIN_EXAMPLES):
        pred = predictor(query=example.query, user_context=example.user_context)
        score = parse_query_metric(example, pred)
        total_score += score

        print(f"Example {i + 1}: {example.query[:50]}...")
        print(f"  Score: {score:.2f}")

        if score < 1.0:
            details = score_detailed(example, pred)
            for field, info in details.items():
                if info["score"] < 1.0:
                    print(
                        f"  ❌ {field}: expected={info['expected']}, got={info['actual']}"
                    )
        print()

    print(f"Average score: {total_score / len(TRAIN_EXAMPLES):.2%}")
