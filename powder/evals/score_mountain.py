"""
Evaluation dataset and metrics for ScoreMountain signature.

ScoreMountain scores individual mountains based on conditions + preferences.
Metrics are primarily rule-based:
- Score range validity (0-100)
- Score ordering (better conditions = higher score)
- Grounding (pros/cons reference actual mountain data)
- Consistency (cons mention actual drawbacks)
"""

import json
import dspy


def make_example(
    mountain: dict,
    user_preferences: dict,
    day_context: str,
    expected: dict,
) -> dspy.Example:
    """Create a ScoreMountain evaluation example."""
    return dspy.Example(
        mountain=json.dumps(mountain),
        user_preferences=json.dumps(user_preferences),
        day_context=day_context,
        **expected,
    ).with_inputs("mountain", "user_preferences", "day_context")


# --- Example Mountains (from actual database) ---

STOWE_POWDER = {
    "name": "Stowe",
    "state": "VT",
    "lat": 44.5258,
    "lon": -72.7858,
    "vertical_drop": 2360,
    "num_trails": 116,
    "green_pct": 16,
    "blue_pct": 59,
    "black_pct": 18,
    "double_black_pct": 7,
    "terrain_parks": "easy,intermediate,hard",
    "glades": "intermediate,hard",
    "pass_types": "epic",
    "lift_types": "gondola,highspeed,fixed",
    "snowmaking_pct": 83,
    "conditions": {
        "fresh_snow_24h_in": 14,
        "snow_depth_in": 48,
        "temp_f": 18,
        "wind_mph": 12,
        "visibility_mi": 10,
        "weather_description": "Light snow",
    },
    "drive_time": {"duration_minutes": 195, "distance_mi": 180},
}

KILLINGTON_ICY = {
    "name": "Killington",
    "state": "VT",
    "lat": 43.6045,
    "lon": -72.8201,
    "vertical_drop": 3050,
    "num_trails": 155,
    "green_pct": 17,
    "blue_pct": 40,
    "black_pct": 33,
    "double_black_pct": 10,
    "terrain_parks": "easy,intermediate,hard,superpipe",
    "glades": "easy,intermediate,hard",
    "pass_types": "ikon",
    "lift_types": "gondola,bubble,highspeed,fixed",
    "snowmaking_pct": 71,
    "conditions": {
        "fresh_snow_24h_in": 0,
        "snow_depth_in": 30,
        "temp_f": 38,
        "wind_mph": 5,
        "visibility_mi": 10,
        "weather_description": "Partly cloudy",
    },
    "drive_time": {"duration_minutes": 165, "distance_mi": 155},
}

JAY_PEAK_WINDY = {
    "name": "Jay Peak",
    "state": "VT",
    "lat": 44.97,
    "lon": -72.47,
    "vertical_drop": 2153,
    "num_trails": 81,
    "green_pct": 20,
    "blue_pct": 40,
    "black_pct": 30,
    "double_black_pct": 10,
    "terrain_parks": "intermediate,hard",
    "glades": "easy,intermediate,hard",
    "pass_types": "ikon",
    "lift_types": "tram,highspeed,fixed",
    "snowmaking_pct": 80,
    "conditions": {
        "fresh_snow_24h_in": 8,
        "snow_depth_in": 52,
        "temp_f": 15,
        "wind_mph": 35,
        "visibility_mi": 3,
        "weather_description": "Snow with high winds",
    },
    "drive_time": {"duration_minutes": 220, "distance_mi": 200},
}

NASHOBA_CLOSE = {
    "name": "Nashoba Valley",
    "state": "MA",
    "lat": 42.48,
    "lon": -71.49,
    "vertical_drop": 240,
    "num_trails": 17,
    "green_pct": 30,
    "blue_pct": 40,
    "black_pct": 30,
    "double_black_pct": 0,
    "terrain_parks": "easy,intermediate",
    "glades": None,
    "pass_types": "indy",
    "lift_types": "fixed",
    "snowmaking_pct": 100,
    "has_night_skiing": True,
    "conditions": {
        "fresh_snow_24h_in": 2,
        "snow_depth_in": 24,
        "temp_f": 28,
        "wind_mph": 8,
        "visibility_mi": 10,
        "weather_description": "Clear",
    },
    "drive_time": {"duration_minutes": 35, "distance_mi": 30},
}

OKEMO_FAMILY = {
    "name": "Okemo",
    "state": "VT",
    "lat": 43.41,
    "lon": -72.72,
    "vertical_drop": 2200,
    "num_trails": 123,
    "green_pct": 32,
    "blue_pct": 36,
    "black_pct": 32,
    "double_black_pct": 0,
    "terrain_parks": "easy,intermediate,hard,superpipe",
    "glades": "easy,intermediate,hard",
    "pass_types": "epic",
    "lift_types": "bubble,highspeed,fixed",
    "snowmaking_pct": 95,
    "has_magic_carpet": True,
    "learning_area_quality": "excellent",
    "conditions": {
        "fresh_snow_24h_in": 4,
        "snow_depth_in": 36,
        "temp_f": 25,
        "wind_mph": 10,
        "visibility_mi": 10,
        "weather_description": "Light snow",
    },
    "drive_time": {"duration_minutes": 150, "distance_mi": 135},
}


# --- User Preference Profiles ---

POWDER_CHASER = {
    "skill_level": "advanced",
    "activity": "ski",
    "vibe": "powder_chase",
    "needs_terrain_parks": False,
    "needs_glades": True,
}

PARK_RAT = {
    "skill_level": "intermediate",
    "activity": "snowboard",
    "vibe": "park_day",
    "needs_terrain_parks": True,
    "needs_glades": False,
}

FAMILY_SKIER = {
    "skill_level": "intermediate",
    "activity": "ski",
    "vibe": "family_day",
    "needs_terrain_parks": False,
    "needs_beginner_terrain": True,
}

CASUAL_SKIER = {
    "skill_level": "intermediate",
    "activity": "either",
    "vibe": "casual",
    "needs_terrain_parks": False,
    "needs_glades": False,
}


# --- Day Contexts ---

POWDER_DAY_CONTEXT = (
    "Day quality: excellent\n"
    'Best available: Stowe has 14" fresh, everyone else <5"\n'
    "Context: Cold temps preserving powder, moderate winds"
)

ICY_DAY_CONTEXT = (
    "Day quality: fair\n"
    "Best available: No fresh snow anywhere, warm temps\n"
    "Context: 38°F causing soft/icy conditions, good visibility"
)

WINDY_DAY_CONTEXT = (
    "Day quality: good\n"
    'Best available: Jay Peak has 8" fresh but very windy\n'
    "Context: High winds (35mph) may close upper lifts, stick to trees"
)


# --- Evaluation Examples ---

# 1. Powder day at Stowe - should score HIGH for powder chaser
STOWE_POWDER_DAY = make_example(
    mountain=STOWE_POWDER,
    user_preferences=POWDER_CHASER,
    day_context=POWDER_DAY_CONTEXT,
    expected={
        "expected_score_min": 80,
        "expected_score_max": 100,
        "expected_pros_mention": ["fresh", "snow", "powder", "14", "glades"],
        "expected_cons_mention": ["drive", "distance", "far"],
    },
)

# 2. Icy day at Killington - should score LOW for powder chaser
KILLINGTON_ICY_DAY = make_example(
    mountain=KILLINGTON_ICY,
    user_preferences=POWDER_CHASER,
    day_context=ICY_DAY_CONTEXT,
    expected={
        "expected_score_min": 20,
        "expected_score_max": 50,
        "expected_pros_mention": ["terrain", "vertical", "variety", "glades"],
        "expected_cons_mention": ["no", "fresh", "snow", "icy", "warm", "conditions"],
    },
)

# 3. Windy day at Jay Peak - mixed (fresh snow but wind)
JAY_WINDY_DAY = make_example(
    mountain=JAY_PEAK_WINDY,
    user_preferences=POWDER_CHASER,
    day_context=WINDY_DAY_CONTEXT,
    expected={
        "expected_score_min": 55,
        "expected_score_max": 80,
        "expected_pros_mention": ["fresh", "snow", "glades", "trees"],
        "expected_cons_mention": ["wind", "visibility", "lifts"],
    },
)

# 4. Small local mountain - good for casual, short drive
NASHOBA_CASUAL = make_example(
    mountain=NASHOBA_CLOSE,
    user_preferences=CASUAL_SKIER,
    day_context=ICY_DAY_CONTEXT,
    expected={
        "expected_score_min": 50,
        "expected_score_max": 75,
        "expected_pros_mention": ["close", "quick", "drive", "night"],
        "expected_cons_mention": ["small", "limited", "terrain", "vertical"],
    },
)

# 5. Park rat at Okemo (good parks)
OKEMO_PARK = make_example(
    mountain=OKEMO_FAMILY,
    user_preferences=PARK_RAT,
    day_context=POWDER_DAY_CONTEXT,
    expected={
        "expected_score_min": 70,
        "expected_score_max": 95,
        "expected_pros_mention": ["park", "terrain", "superpipe", "features"],
        "expected_cons_mention": ["drive", "crowds", "epic"],  # Maybe wrong pass
    },
)

# 6. Family at Okemo (excellent learning area)
OKEMO_FAMILY_DAY = make_example(
    mountain=OKEMO_FAMILY,
    user_preferences=FAMILY_SKIER,
    day_context=POWDER_DAY_CONTEXT,
    expected={
        "expected_score_min": 75,
        "expected_score_max": 95,
        "expected_pros_mention": [
            "family",
            "learning",
            "beginner",
            "green",
            "magic carpet",
        ],
        "expected_cons_mention": ["drive", "price", "crowds"],
    },
)

# 7. Powder chaser at small local mountain - should score LOW
NASHOBA_POWDER_CHASER = make_example(
    mountain=NASHOBA_CLOSE,
    user_preferences=POWDER_CHASER,
    day_context=POWDER_DAY_CONTEXT,
    expected={
        "expected_score_min": 20,
        "expected_score_max": 45,
        "expected_pros_mention": ["close", "quick"],
        "expected_cons_mention": [
            "small",
            "limited",
            "terrain",
            "no glades",
            "vertical",
        ],
    },
)

# 8. Wrong pass type scenario
STOWE_IKON_HOLDER = make_example(
    mountain=STOWE_POWDER,
    user_preferences={**POWDER_CHASER, "pass_type_held": "ikon"},
    day_context=POWDER_DAY_CONTEXT,
    expected={
        "expected_score_min": 60,
        "expected_score_max": 85,
        "expected_pros_mention": ["fresh", "snow", "powder"],
        "expected_cons_mention": ["epic", "pass", "pay", "ticket"],
    },
)


# All examples
TRAIN_EXAMPLES = [
    STOWE_POWDER_DAY,
    KILLINGTON_ICY_DAY,
    JAY_WINDY_DAY,
    OKEMO_PARK,
    NASHOBA_POWDER_CHASER,
    STOWE_IKON_HOLDER,
]
VAL_EXAMPLES = [
    OKEMO_FAMILY_DAY,
    NASHOBA_CASUAL,
]


# --- Metric Function ---


def score_mountain_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """
    Score a ScoreMountain prediction with rule-based metrics.

    Checks:
    1. Score validity: is it a number between 0-100?
    2. Score range: is it within expected range for this scenario?
    3. Grounding: do pros mention expected keywords?
    4. Grounding: do cons mention expected keywords?
    5. Tradeoff coherence: does tradeoff_note make sense?

    Returns:
        Float between 0 and 1
    """
    scores = []

    # 1. Score validity - must be a number 0-100
    try:
        score_val = float(pred.score)
        valid_range = 0 <= score_val <= 100
        scores.append(1.0 if valid_range else 0.0)
    except (ValueError, TypeError):
        scores.append(0.0)
        score_val = None

    # 2. Score in expected range
    if score_val is not None and hasattr(example, "expected_score_min"):
        min_score = example.expected_score_min
        max_score = example.expected_score_max

        if min_score <= score_val <= max_score:
            scores.append(1.0)
        elif min_score - 10 <= score_val <= max_score + 10:
            # Close but not quite
            scores.append(0.5)
        else:
            scores.append(0.0)

    # 3. Pros grounding - check if expected keywords are mentioned
    if hasattr(example, "expected_pros_mention"):
        keywords = example.expected_pros_mention
        pros_text = pred.key_pros.lower()
        matches = sum(1 for kw in keywords if kw.lower() in pros_text)
        # At least 2 of the expected keywords should appear
        pros_score = min(matches / 2, 1.0)
        scores.append(pros_score)

    # 4. Cons grounding - check if expected keywords are mentioned
    if hasattr(example, "expected_cons_mention"):
        keywords = example.expected_cons_mention
        cons_text = pred.key_cons.lower()
        matches = sum(1 for kw in keywords if kw.lower() in cons_text)
        # At least 1 of the expected keywords should appear
        cons_score = min(matches / 1, 1.0)
        scores.append(cons_score)

    # 5. Tradeoff note exists and is non-empty
    has_tradeoff = bool(pred.tradeoff_note and len(pred.tradeoff_note.strip()) > 10)
    scores.append(1.0 if has_tradeoff else 0.0)

    return sum(scores) / len(scores) if scores else 0.0


def get_trainset() -> list[dspy.Example]:
    """Get training examples (first 6 of 8 = 75%)."""
    return TRAIN_EXAMPLES


def get_valset() -> list[dspy.Example]:
    """Get validation examples (last 2 of 8 = 25%)."""
    return VAL_EXAMPLES


def get_metric():
    """Get the metric function."""
    return score_mountain_metric


# --- Detailed scoring ---


def score_detailed(example: dspy.Example, pred: dspy.Prediction) -> dict:
    """Get detailed per-check scoring for error analysis."""
    details = {}

    # Score validity
    try:
        score_val = float(pred.score)
        details["score_valid"] = {
            "score": score_val,
            "valid": 0 <= score_val <= 100,
        }
    except (ValueError, TypeError):
        details["score_valid"] = {"score": pred.score, "valid": False}
        score_val = None

    # Score range
    if score_val and hasattr(example, "expected_score_min"):
        in_range = example.expected_score_min <= score_val <= example.expected_score_max
        details["score_range"] = {
            "expected": f"{example.expected_score_min}-{example.expected_score_max}",
            "actual": score_val,
            "in_range": in_range,
        }

    # Pros keywords
    if hasattr(example, "expected_pros_mention"):
        found = [
            kw
            for kw in example.expected_pros_mention
            if kw.lower() in pred.key_pros.lower()
        ]
        details["pros_grounding"] = {
            "expected_any": example.expected_pros_mention,
            "found": found,
            "text": pred.key_pros,
        }

    # Cons keywords
    if hasattr(example, "expected_cons_mention"):
        found = [
            kw
            for kw in example.expected_cons_mention
            if kw.lower() in pred.key_cons.lower()
        ]
        details["cons_grounding"] = {
            "expected_any": example.expected_cons_mention,
            "found": found,
            "text": pred.key_cons,
        }

    return details


if __name__ == "__main__":
    import dspy
    from powder.signatures import ScoreMountain

    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))

    predictor = dspy.Predict(ScoreMountain)

    print("Testing ScoreMountain metric...\n")

    total_score = 0.0
    for i, example in enumerate(TRAIN_EXAMPLES):
        pred = predictor(
            mountain=example.mountain,
            user_preferences=example.user_preferences,
            day_context=example.day_context,
        )
        score = score_mountain_metric(example, pred)
        total_score += score

        mountain_name = json.loads(example.mountain)["name"]
        print(f"Example {i + 1}: {mountain_name}")
        print(f"  Predicted score: {pred.score}")
        print(f"  Metric score: {score:.2f}")

        if score < 0.8:
            details = score_detailed(example, pred)
            print(f"  Details: {json.dumps(details, indent=4, default=str)[:500]}")
        print()

    print(f"Average score: {total_score / len(TRAIN_EXAMPLES):.2%}")
