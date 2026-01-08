"""
Evaluation dataset and metrics for GenerateRecommendation signature.

GenerateRecommendation takes scored candidates and produces final recommendations.
Metrics are rule-based:
- Top pick matches highest-scored mountain (or acceptable alternatives)
- Alternatives mention real mountains from candidates
- Recommendation respects constraints (pass type, drive time)
- Caveat mentions relevant concerns (crowds, weather)
"""

import json
import dspy


def make_example(
    query: str,
    day_assessment: str,
    scored_candidates: list[dict],
    crowd_context: dict,
    expected: dict,
) -> dspy.Example:
    """Create a GenerateRecommendation evaluation example."""
    return dspy.Example(
        query=query,
        day_assessment=day_assessment,
        scored_candidates=json.dumps(scored_candidates),
        crowd_context=json.dumps(crowd_context),
        **expected,
    ).with_inputs("query", "day_assessment", "scored_candidates", "crowd_context")


# --- Scored Candidate Sets ---

# Powder day - Stowe clearly best
POWDER_DAY_CANDIDATES = [
    {
        "mountain": {"name": "Stowe", "state": "VT", "pass_types": "epic"},
        "score": 92,
        "key_pros": '14" fresh powder, excellent glades',
        "key_cons": "3+ hour drive",
        "tradeoff_note": "Best snow but longest drive",
    },
    {
        "mountain": {"name": "Sugarbush", "state": "VT", "pass_types": "ikon"},
        "score": 78,
        "key_pros": '8" fresh, good terrain variety',
        "key_cons": "Less snow than Stowe",
        "tradeoff_note": "Good alternative if you have Ikon",
    },
    {
        "mountain": {"name": "Killington", "state": "VT", "pass_types": "ikon"},
        "score": 72,
        "key_pros": '6" fresh, biggest vertical',
        "key_cons": "Crowded, less fresh snow",
        "tradeoff_note": "Big mountain but not the powder leader today",
    },
]

# Icy day - all options mediocre
ICY_DAY_CANDIDATES = [
    {
        "mountain": {"name": "Killington", "state": "VT", "pass_types": "ikon"},
        "score": 55,
        "key_pros": "Best snowmaking, biggest terrain",
        "key_cons": "No fresh snow, icy conditions",
        "tradeoff_note": "Best of a rough day",
    },
    {
        "mountain": {"name": "Okemo", "state": "VT", "pass_types": "epic"},
        "score": 52,
        "key_pros": "Good grooming, family-friendly",
        "key_cons": "Icy, warm temps",
        "tradeoff_note": "Decent alternative but conditions rough",
    },
    {
        "mountain": {"name": "Mount Snow", "state": "VT", "pass_types": "epic"},
        "score": 48,
        "key_pros": "Closest VT mountain",
        "key_cons": "Icy, crowded",
        "tradeoff_note": "Skip unless you must go",
    },
]

# Close tie - multiple good options
CLOSE_TIE_CANDIDATES = [
    {
        "mountain": {"name": "Jay Peak", "state": "VT", "pass_types": "ikon"},
        "score": 85,
        "key_pros": "Best natural snow, great glades",
        "key_cons": "Furthest drive (3.5 hrs)",
        "tradeoff_note": "Best snow if you can handle the drive",
    },
    {
        "mountain": {"name": "Sugarbush", "state": "VT", "pass_types": "ikon"},
        "score": 83,
        "key_pros": "Good snow, varied terrain",
        "key_cons": "Slightly less snow than Jay",
        "tradeoff_note": "Great balance of snow and distance",
    },
    {
        "mountain": {"name": "Killington", "state": "VT", "pass_types": "ikon"},
        "score": 80,
        "key_pros": "Biggest terrain, night skiing",
        "key_cons": "More crowded",
        "tradeoff_note": "Best if you want variety and night skiing",
    },
]


# --- Crowd Contexts ---

NORMAL_CROWDS = {
    "crowd_level": "normal",
    "is_holiday": False,
    "vacation_week": None,
    "note": "Regular weekday",
}

HOLIDAY_CROWDS = {
    "crowd_level": "extreme",
    "is_holiday": True,
    "vacation_week": "MA",
    "note": "MA February vacation week - expect long lift lines everywhere",
}

WEEKEND_CROWDS = {
    "crowd_level": "moderate",
    "is_holiday": False,
    "vacation_week": None,
    "note": "Saturday - busier than weekday",
}


# --- Day Assessments ---

EXCELLENT_DAY = (
    "Day quality: excellent\n"
    'Best available: Stowe has 14" fresh\n'
    "Context: Cold temps, powder preserved"
)

POOR_DAY = (
    "Day quality: fair\n"
    "Best available: No standout, all conditions mediocre\n"
    "Context: Warm temps, icy base, skip if you can"
)

GOOD_DAY = (
    "Day quality: good\n"
    'Best available: Jay Peak and Sugarbush both have 10"+ fresh\n'
    "Context: Multiple solid options today"
)


# --- Evaluation Examples ---

# 1. Clear winner on powder day
CLEAR_WINNER = make_example(
    query="Best powder day within 4 hours, I have Epic pass",
    day_assessment=EXCELLENT_DAY,
    scored_candidates=POWDER_DAY_CANDIDATES,
    crowd_context=NORMAL_CROWDS,
    expected={
        "expected_top_pick": ["Stowe"],
        "expected_alternatives_mention": ["Sugarbush", "Killington"],
        "expected_top_pick_keywords": ["powder", "fresh", "snow", "14"],
    },
)

# 2. Icy day - should recommend best option but with caveats
ICY_RECOMMENDATION = make_example(
    query="Where should I ski today?",
    day_assessment=POOR_DAY,
    scored_candidates=ICY_DAY_CANDIDATES,
    crowd_context=NORMAL_CROWDS,
    expected={
        "expected_top_pick": ["Killington"],
        "expected_caveat_keywords": [
            "icy",
            "conditions",
            "rough",
            "postpone",
            "tomorrow",
        ],
        "expected_alternatives_mention": ["Okemo"],
    },
)

# 3. Close tie - either top pick is acceptable
CLOSE_TIE = make_example(
    query="Looking for fresh powder with Ikon pass",
    day_assessment=GOOD_DAY,
    scored_candidates=CLOSE_TIE_CANDIDATES,
    crowd_context=NORMAL_CROWDS,
    expected={
        "expected_top_pick": ["Jay Peak", "Sugarbush"],  # Either acceptable
        "expected_alternatives_mention": ["Killington", "Sugarbush", "Jay Peak"],
        "expected_mention_tradeoff": True,  # Should discuss drive vs snow tradeoff
    },
)

# 4. Holiday crowds - should warn
HOLIDAY_WARNING = make_example(
    query="Family ski trip this week",
    day_assessment=EXCELLENT_DAY,
    scored_candidates=POWDER_DAY_CANDIDATES,
    crowd_context=HOLIDAY_CROWDS,
    expected={
        "expected_top_pick": ["Stowe"],
        "expected_caveat_keywords": ["crowd", "busy", "lines", "vacation", "wait"],
    },
)

# 5. Pass type mismatch awareness
PASS_MISMATCH = make_example(
    query="I have Ikon pass, where should I go?",
    day_assessment=EXCELLENT_DAY,
    scored_candidates=POWDER_DAY_CANDIDATES,  # Stowe is Epic, not Ikon
    crowd_context=NORMAL_CROWDS,
    expected={
        # Should recommend Sugarbush (Ikon) over Stowe (Epic)
        "expected_top_pick": ["Sugarbush", "Killington"],  # Ikon mountains
        "expected_pass_awareness": True,  # Should mention pass compatibility
    },
)

# 6. Short drive preference
SHORT_DRIVE = make_example(
    query="Quick trip, don't want to drive far",
    day_assessment=GOOD_DAY,
    scored_candidates=[
        {
            "mountain": {"name": "Nashoba Valley", "state": "MA", "pass_types": "indy"},
            "score": 65,
            "key_pros": "35 min drive, night skiing",
            "key_cons": "Small mountain",
            "tradeoff_note": "Convenient but limited terrain",
        },
        {
            "mountain": {"name": "Gunstock", "state": "NH", "pass_types": "indy"},
            "score": 70,
            "key_pros": "Good variety, 1.5hr drive",
            "key_cons": "Longer than Nashoba",
            "tradeoff_note": "Better terrain if you have time",
        },
    ],
    crowd_context=NORMAL_CROWDS,
    expected={
        "expected_top_pick": ["Nashoba Valley", "Gunstock"],
        "expected_top_pick_keywords": ["close", "quick", "drive", "convenient"],
    },
)

# 7. Weekend crowds consideration
WEEKEND_TRIP = make_example(
    query="Saturday ski trip",
    day_assessment=EXCELLENT_DAY,
    scored_candidates=POWDER_DAY_CANDIDATES,
    crowd_context=WEEKEND_CROWDS,
    expected={
        "expected_top_pick": ["Stowe"],
        "expected_caveat_keywords": ["weekend", "Saturday", "busier", "early"],
    },
)


TRAIN_EXAMPLES = [
    CLEAR_WINNER,
    ICY_RECOMMENDATION,
    CLOSE_TIE,
    PASS_MISMATCH,
    SHORT_DRIVE,
]
VAL_EXAMPLES = [
    HOLIDAY_WARNING,
    WEEKEND_TRIP,
]


# --- Metric Function ---


def generate_recommendation_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """
    Score a GenerateRecommendation prediction with rule-based metrics.

    Checks:
    1. Top pick correctness - mentions expected mountain(s)
    2. Alternatives grounding - mentions real mountains from candidates
    3. Top pick reasoning - uses expected keywords
    4. Caveat relevance - mentions expected concerns
    5. Pass awareness - if query mentions pass, respects it

    Returns:
        Float between 0 and 1
    """
    scores = []

    # 1. Top pick correctness
    if hasattr(example, "expected_top_pick"):
        acceptable = example.expected_top_pick
        top_pick_lower = pred.top_pick.lower()
        matches = any(mtn.lower() in top_pick_lower for mtn in acceptable)
        scores.append(1.0 if matches else 0.0)

    # 2. Alternatives grounding - mentions real mountains
    if hasattr(example, "expected_alternatives_mention"):
        expected_mtns = example.expected_alternatives_mention
        alts_lower = pred.alternatives.lower()
        matches = sum(1 for mtn in expected_mtns if mtn.lower() in alts_lower)
        # At least 1 expected alternative should be mentioned
        scores.append(1.0 if matches >= 1 else 0.5 if alts_lower else 0.0)

    # 3. Top pick keywords
    if hasattr(example, "expected_top_pick_keywords"):
        keywords = example.expected_top_pick_keywords
        top_pick_lower = pred.top_pick.lower()
        matches = sum(1 for kw in keywords if kw.lower() in top_pick_lower)
        # At least 1 keyword should appear
        scores.append(min(matches / 1, 1.0))

    # 4. Caveat keywords (when expected)
    if hasattr(example, "expected_caveat_keywords"):
        keywords = example.expected_caveat_keywords
        # Check both caveat and top_pick for these concerns
        full_text = (
            pred.caveat + " " + pred.top_pick + " " + pred.alternatives
        ).lower()
        matches = sum(1 for kw in keywords if kw.lower() in full_text)
        scores.append(1.0 if matches >= 1 else 0.0)

    # 5. Pass awareness (special check)
    if hasattr(example, "expected_pass_awareness") and example.expected_pass_awareness:
        # Check if pass type is mentioned in recommendation
        full_text = (
            pred.top_pick + " " + pred.alternatives + " " + pred.caveat
        ).lower()
        pass_words = ["pass", "ikon", "epic", "indy", "ticket"]
        mentions_pass = any(pw in full_text for pw in pass_words)
        scores.append(1.0 if mentions_pass else 0.0)

    # 6. Non-empty outputs
    has_top_pick = bool(pred.top_pick and len(pred.top_pick.strip()) > 10)
    has_alternatives = bool(pred.alternatives and len(pred.alternatives.strip()) > 5)
    scores.append(1.0 if has_top_pick and has_alternatives else 0.5)

    return sum(scores) / len(scores) if scores else 0.0


def get_examples() -> list[dspy.Example]:
    """Get all examples."""
    return TRAIN_EXAMPLES + VAL_EXAMPLES


def get_trainset() -> list[dspy.Example]:
    """Get training examples (first 5 of 7 = 71%)."""
    return TRAIN_EXAMPLES


def get_valset() -> list[dspy.Example]:
    """Get validation examples (last 2 of 7 = 29%)."""
    return VAL_EXAMPLES


def get_metric():
    """Get the metric function."""
    return generate_recommendation_metric


# --- Detailed scoring ---


def score_detailed(example: dspy.Example, pred: dspy.Prediction) -> dict:
    """Get detailed per-check scoring for error analysis."""
    details = {
        "top_pick": pred.top_pick[:100] if pred.top_pick else "",
        "alternatives": pred.alternatives[:100] if pred.alternatives else "",
        "caveat": pred.caveat[:100] if pred.caveat else "",
    }

    if hasattr(example, "expected_top_pick"):
        acceptable = example.expected_top_pick
        matches = [mtn for mtn in acceptable if mtn.lower() in pred.top_pick.lower()]
        details["top_pick_check"] = {
            "expected_any": acceptable,
            "found": matches,
            "pass": len(matches) > 0,
        }

    if hasattr(example, "expected_caveat_keywords"):
        full_text = (pred.caveat + " " + pred.top_pick).lower()
        found = [
            kw for kw in example.expected_caveat_keywords if kw.lower() in full_text
        ]
        details["caveat_check"] = {
            "expected_any": example.expected_caveat_keywords,
            "found": found,
        }

    return details


if __name__ == "__main__":
    import dspy
    from powder.signatures import GenerateRecommendation

    dspy.configure(lm=dspy.LM("anthropic/claude-haiku-4-5-20251001"))

    predictor = dspy.Predict(GenerateRecommendation)

    print("Testing GenerateRecommendation metric...\n")

    total_score = 0.0
    for i, example in enumerate(TRAIN_EXAMPLES):
        pred = predictor(
            query=example.query,
            day_assessment=example.day_assessment,
            scored_candidates=example.scored_candidates,
            crowd_context=example.crowd_context,
        )
        score = generate_recommendation_metric(example, pred)
        total_score += score

        print(f"Example {i + 1}: {example.query[:50]}...")
        print(f"  Top pick: {pred.top_pick[:60]}...")
        print(f"  Metric score: {score:.2f}")

        if score < 0.8:
            details = score_detailed(example, pred)
            for key, val in details.items():
                if isinstance(val, dict) and "pass" in val and not val["pass"]:
                    print(f"  ❌ {key}: {val}")
        print()

    print(f"Average score: {total_score / len(TRAIN_EXAMPLES):.2%}")
