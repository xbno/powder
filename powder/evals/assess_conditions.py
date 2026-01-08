"""
Evaluation dataset and metrics for AssessConditions signature.

This follows the DSPy pattern:
1. Define examples with inputs AND expected outputs
2. Write a metric function that scores predictions
3. Use with optimizers like MIPROv2

The metric checks:
- Structural validity (is day_quality a valid enum?)
- Grounding (does best_available mention a real mountain?)
- Consistency (does assessment match the conditions?)
- Accuracy (when we have labels, do they match?)
"""

import json
import dspy


# --- Example Dataset ---
# Each example has inputs (all_candidates, user_preferences)
# and expected outputs for evaluation


def make_example(
    candidates: list[dict], preferences: dict, expected: dict
) -> dspy.Example:
    """Helper to create a properly structured example."""
    return dspy.Example(
        all_candidates=json.dumps(candidates),
        user_preferences=json.dumps(preferences),
        **expected,
    ).with_inputs("all_candidates", "user_preferences")


# Powder day scenario - should be "excellent" or "good"
POWDER_DAY = make_example(
    candidates=[
        {
            "name": "Stowe",
            "state": "VT",
            "conditions": {
                "fresh_snow_24h_in": 14,
                "temp_f": 22,
                "wind_mph": 8,
                "visibility": "good",
            },
        },
        {
            "name": "Killington",
            "state": "VT",
            "conditions": {
                "fresh_snow_24h_in": 10,
                "temp_f": 24,
                "wind_mph": 12,
                "visibility": "good",
            },
        },
        {
            "name": "Okemo",
            "state": "VT",
            "conditions": {
                "fresh_snow_24h_in": 8,
                "temp_f": 26,
                "wind_mph": 10,
                "visibility": "good",
            },
        },
    ],
    preferences={"vibe": "powder_chase", "skill_level": "advanced"},
    expected={
        "expected_day_quality": ["excellent", "good"],  # Either is acceptable
        "expected_best_mountain": "Stowe",  # Has most fresh snow
        "expected_mention_snow": True,  # Should mention fresh snow
    },
)

# Icy/poor conditions - should be "fair" or "poor"
ICY_DAY = make_example(
    candidates=[
        {
            "name": "Gunstock",
            "state": "NH",
            "conditions": {
                "fresh_snow_24h_in": 0,
                "temp_f": 38,
                "wind_mph": 5,
                "visibility": "good",
            },
        },
        {
            "name": "Waterville Valley",
            "state": "NH",
            "conditions": {
                "fresh_snow_24h_in": 0,
                "temp_f": 40,
                "wind_mph": 8,
                "visibility": "good",
            },
        },
    ],
    preferences={"vibe": "casual", "skill_level": "intermediate"},
    expected={
        "expected_day_quality": ["fair", "poor"],  # No fresh snow, warm = icy
        "expected_mention_conditions": True,  # Should mention lack of snow or warmth
    },
)

# Windy day - should mention wind, maybe downgrade quality
WINDY_DAY = make_example(
    candidates=[
        {
            "name": "Jay Peak",
            "state": "VT",
            "conditions": {
                "fresh_snow_24h_in": 6,
                "temp_f": 18,
                "wind_mph": 35,
                "visibility": "poor",
            },
        },
        {
            "name": "Smugglers' Notch",
            "state": "VT",
            "conditions": {
                "fresh_snow_24h_in": 5,
                "temp_f": 20,
                "wind_mph": 25,
                "visibility": "fair",
            },
        },
    ],
    preferences={"vibe": "powder_chase", "needs_glades": True},
    expected={
        "expected_day_quality": ["good", "fair"],  # Fresh snow but wind is issue
        "expected_mention_wind": True,  # Should definitely mention wind
    },
)

# Extreme cold - should mention or warn
BITTER_COLD = make_example(
    candidates=[
        {
            "name": "Sugarloaf",
            "state": "ME",
            "conditions": {
                "fresh_snow_24h_in": 4,
                "temp_f": -15,
                "wind_mph": 20,
                "visibility": "good",
            },
        },
    ],
    preferences={"vibe": "casual", "skill_level": "intermediate"},
    expected={
        "expected_day_quality": ["fair", "poor", "stay_home"],
        "expected_mention_cold": True,
    },
)

# All examples for training/evaluation
TRAIN_EXAMPLES = [POWDER_DAY, ICY_DAY, WINDY_DAY]
VAL_EXAMPLES = [BITTER_COLD]

# --- Metric Function ---

VALID_DAY_QUALITIES = {"excellent", "good", "fair", "poor", "stay_home"}


def assess_conditions_metric(example, pred, trace=None) -> float:
    """
    Score an AssessConditions prediction.

    Checks:
    1. Structural validity - is day_quality valid?
    2. Grounding - does best_available mention a real mountain?
    3. Consistency - does quality match conditions?
    4. Accuracy - matches expected outputs when available

    Returns:
        Float between 0 and 1
    """
    scores = []

    # 1. Structural validity: day_quality is valid enum
    day_quality_valid = pred.day_quality.lower().strip() in VALID_DAY_QUALITIES
    scores.append(1.0 if day_quality_valid else 0.0)

    # 2. Grounding: best_available mentions a real mountain from candidates
    candidates = json.loads(example.all_candidates)
    mountain_names = [c["name"].lower() for c in candidates]
    mentions_real_mountain = any(
        name in pred.best_available.lower() for name in mountain_names
    )
    scores.append(1.0 if mentions_real_mountain else 0.0)

    # 3. Accuracy: day_quality matches expected (if provided)
    if hasattr(example, "expected_day_quality"):
        expected = example.expected_day_quality
        if isinstance(expected, list):
            matches = pred.day_quality.lower().strip() in [e.lower() for e in expected]
        else:
            matches = pred.day_quality.lower().strip() == expected.lower()
        scores.append(1.0 if matches else 0.0)

    # 4. Accuracy: mentions expected best mountain (if provided)
    if hasattr(example, "expected_best_mountain"):
        mentions_best = (
            example.expected_best_mountain.lower() in pred.best_available.lower()
        )
        scores.append(1.0 if mentions_best else 0.0)

    # 5. Consistency: mentions wind if it's windy (if expected)
    if hasattr(example, "expected_mention_wind") and example.expected_mention_wind:
        mentions_wind = "wind" in pred.day_context.lower()
        scores.append(1.0 if mentions_wind else 0.0)

    # 6. Consistency: mentions cold if it's bitter cold (if expected)
    if hasattr(example, "expected_mention_cold") and example.expected_mention_cold:
        cold_words = [
            "cold",
            "frigid",
            "bitter",
            "freezing",
            "temperature",
            "frostbite",
        ]
        mentions_cold = any(w in pred.day_context.lower() for w in cold_words)
        scores.append(1.0 if mentions_cold else 0.0)

    # Average all scores
    return sum(scores) / len(scores) if scores else 0.0


# --- Convenience functions for optimization ---


def get_examples() -> list[dspy.Example]:
    """Get all examples."""
    return TRAIN_EXAMPLES + VAL_EXAMPLES


def get_trainset() -> list[dspy.Example]:
    """Get training examples (first 3 of 4 = 75%)."""
    return TRAIN_EXAMPLES


def get_valset() -> list[dspy.Example]:
    """Get validation examples (last 1 of 4 = 25%)."""
    return VAL_EXAMPLES


def get_metric():
    """Get the metric function."""
    return assess_conditions_metric


if __name__ == "__main__":
    # Quick test: run the signature on examples and score
    import dspy
    from powder.signatures import AssessConditions

    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))

    predictor = dspy.Predict(AssessConditions)

    print("Testing AssessConditions metric...\n")

    for i, example in enumerate(TRAIN_EXAMPLES):
        pred = predictor(
            all_candidates=example.all_candidates,
            user_preferences=example.user_preferences,
        )

        score = assess_conditions_metric(example, pred)

        print(f"Example {i + 1}:")
        print(f"  Day Quality: {pred.day_quality}")
        print(f"  Best Available: {pred.best_available[:60]}...")
        print(f"  Score: {score:.2f}")
        print()
