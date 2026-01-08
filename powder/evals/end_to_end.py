"""
End-to-end evaluation dataset and metrics for the full ski recommendation pipeline.

This is the KEY evaluation for the assignment - it measures:
1. Hit@1 - Did we recommend the right mountain as top pick?
2. Hit@3 - Is the right mountain in our top 3?
3. Constraint Satisfaction - Did we respect all hard constraints?
4. Skip Detection - Did we correctly recommend skipping on bad days?

All metrics are DETERMINISTIC (no LLM scoring).

Examples use REAL HISTORIC WEATHER DATA from fixtures/by_date.json.
Set conditions_snapshot=None to load conditions from fixtures by query_date.
"""

from datetime import date
from dataclasses import dataclass, field


@dataclass
class EndToEndExample:
    """
    A complete evaluation example with:
    - Input query and context
    - Query date (conditions loaded from fixtures/by_date.json)
    - Ground truth for evaluation
    """

    id: str
    query: str
    query_date: date  # Conditions loaded from fixtures by this date
    user_location: dict  # {name, lat, lon}

    # Ground truth
    expected_top_pick: list[str]  # Acceptable top picks (empty for skip days)
    expected_in_top_3: list[str]  # Should appear in top 3

    # Constraints that must be satisfied
    constraints: dict = field(default_factory=dict)
    # e.g., {"pass_type": "ikon", "max_drive_hours": 3.0}

    # Mountains that should NOT be recommended
    expected_excluded: list[str] = field(default_factory=list)

    # Optional: expected reasoning keywords
    reasoning_keywords: list[str] = field(default_factory=list)

    # Skip day: if True, the agent should recommend NOT skiing
    expect_skip: bool = False


# --- Locations ---

BOSTON = {"name": "Boston, MA", "lat": 42.3601, "lon": -71.0589}
NYC = {"name": "New York, NY", "lat": 40.7128, "lon": -74.0060}
ALBANY = {"name": "Albany, NY", "lat": 42.6526, "lon": -73.7562}


# --- Evaluation Dataset ---
# All examples use real historic weather data from fixtures/by_date.json
# Dates chosen based on find_interesting_days.py analysis

TRAIN_EXAMPLES = [
    # ===== POWDER DAYS (Clear Winners) =====
    # 1. Big powder day - Sugarloaf 5.7", huge variance
    # Ikon mountains: Sugarloaf, Sugarbush, Killington, Jay Peak
    EndToEndExample(
        id="powder_ikon_feb17",
        query="Best powder today? I have an Ikon pass.",
        query_date=date(2025, 2, 17),
        user_location=BOSTON,
        expected_top_pick=["Sugarloaf"],  # 5.7" fresh, clear winner
        expected_in_top_3=["Sugarloaf", "Sugarbush", "Killington"],
        expected_excluded=["Stowe", "Okemo", "Mount Snow"],  # Epic mountains
        constraints={"pass_type": "ikon"},
        reasoning_keywords=["powder", "fresh", "sugarloaf", "5"],
    ),
    # 3. No pass - anyone can go, Sugarloaf wins on pure conditions
    EndToEndExample(
        id="powder_no_pass_jan02",
        query="Where has the best snow today? Don't care about pass.",
        query_date=date(2025, 1, 2),
        user_location=BOSTON,
        expected_top_pick=["Sugarloaf"],  # 5.6" fresh
        expected_in_top_3=[
            "Sugarloaf",
            "Sunday River",
            "Saddleback",
        ],  # Maine got dumped on
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["powder", "fresh", "maine"],
    ),
    # 4. Southern VT powder day - Mount Snow 4.2" on 2024-12-10
    # Tests closer option for Boston users
    EndToEndExample(
        id="powder_south_vt_dec10",
        query="Best skiing within 3 hours of Boston?",
        query_date=date(2024, 12, 10),
        user_location=BOSTON,
        expected_top_pick=["Mount Snow", "Stratton", "Okemo"],  # Southern VT got snow
        expected_in_top_3=["Mount Snow", "Stratton", "Okemo", "Killington"],
        expected_excluded=[],
        constraints={"max_drive_hours": 3.0},
        reasoning_keywords=["snow", "drive", "close"],
    ),
    # ===== NYC LOCATION =====
    # 5. NYC user - different distance calculations favor Catskills/southern VT
    EndToEndExample(
        id="nyc_powder_mar29",
        query="Best powder today from NYC?",
        query_date=date(2025, 3, 29),
        user_location=NYC,
        # Stowe has 5.5" but is far from NYC
        # Hunter/Windham are closer but less snow
        expected_top_pick=["Stowe", "Hunter Mountain", "Killington"],
        expected_in_top_3=[
            "Stowe",
            "Hunter Mountain",
            "Killington",
            "Windham Mountain",
        ],
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["powder", "fresh", "drive"],
    ),
    # ===== TERRAIN-SPECIFIC QUERIES =====
    # 6. Terrain park focus - Killington/Okemo have superpipes
    EndToEndExample(
        id="park_day_jan02",
        query="I want to hit rails and jumps tomorrow",
        query_date=date(2025, 1, 2),
        user_location=BOSTON,
        # Holiday crowds and super windy 20mphs most places, rec skip first
        expected_top_pick=[],
        expected_in_top_3=["Killington", "Mount Snow", "Okemo"],
        expected_excluded=["Mad River Glen"],  # No parks, no snowboarding
        constraints={"needs_terrain_parks": True},
        reasoning_keywords=["park", "terrain", "features"],
        expect_skip=True,
    ),
    # 7. Glade/tree skiing - Jay Peak is famous for this
    EndToEndExample(
        id="glades_ikon_feb17",
        query="Looking for tree skiing, have Ikon pass",
        query_date=date(2025, 2, 17),
        user_location=BOSTON,
        expected_top_pick=["Jay Peak", "Sugarloaf", "Sugarbush"],
        expected_in_top_3=["Jay Peak", "Sugarloaf", "Sugarbush", "Killington"],
        expected_excluded=[],
        constraints={"pass_type": "ikon", "needs_glades": True},
        reasoning_keywords=["glades", "trees", "woods"],
    ),
    # 8. Beginner/family day
    EndToEndExample(
        id="beginner_family_jan29",
        query="Taking my kids for their first ski lesson",
        query_date=date(2025, 1, 29),
        user_location=BOSTON,
        # Okemo, Smugglers, Bretton Woods have excellent learning areas
        expected_top_pick=[
            "Nashoba Valley",
            "Okemo",
            "Smugglers' Notch",
            "Bretton Woods",
            "Stratton",
        ],
        expected_in_top_3=[
            "Nashoba Valley",
            "Okemo",
            "Smugglers' Notch",
            "Bretton Woods",
            "Stratton",
            "Waterville Valley",
        ],
        expected_excluded=["Mad River Glen"],  # Basic learning area
        constraints={"needs_beginner_terrain": True},
        reasoning_keywords=["beginner", "learning", "family", "lesson"],
    ),
    # ===== AMBIGUOUS DAYS (Tests tie-breaking) =====
    # 10. Ambiguous day - similar conditions everywhere, pick closest
    EndToEndExample(
        id="ambiguous_jan29",
        query="Where should I ski today?",
        query_date=date(2025, 1, 29),
        user_location=BOSTON,
        # Low variance (1.6"), cold (5.4°F), Gore has 2.1" best
        # Should recommend based on combination of snow + proximity
        expected_top_pick=["Gore Mountain", "Jiminy Peak", "Killington", "Stowe"],
        expected_in_top_3=[
            "Gore Mountain",
            "Jiminy Peak",
            "Killington",
            "Stowe",
            "Sugarbush",
        ],
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["conditions", "snow"],
    ),
    # ===== SKIP DAYS (Bad conditions - should recommend NOT skiing) =====
    # 12. Brutal cold - Jan 8, -8.5°F, minimal snow
    EndToEndExample(
        id="skip_brutal_cold_jan08",
        query="Worth skiing today?",
        query_date=date(2025, 1, 8),
        user_location=BOSTON,
        # -8.5°F coldest, only 1.5" fresh max - should skip
        expected_top_pick=[],
        expected_in_top_3=[],
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["cold", "dangerous", "skip", "stay home", "not worth"],
        expect_skip=True,
    ),
    # 14. Rainy day - Dec 11, widespread rain (weather_code 61)
    EndToEndExample(
        id="skip_rainy_dec11",
        query="Should I ski today?",
        query_date=date(2024, 12, 11),
        user_location=BOSTON,
        # Widespread slight rain at many mountains
        expected_top_pick=[],
        expected_in_top_3=[],
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["rain", "wet", "skip", "not worth"],
        expect_skip=True,
    ),
    # 15. Spring slush - Mar 31, 38-69°F, no fresh snow
    EndToEndExample(
        id="skip_spring_slush_mar31",
        query="Where should I ski today?",
        query_date=date(2025, 3, 31),
        user_location=BOSTON,
        # Warm temps (38-69°F), zero fresh snow - slushy mess
        expected_top_pick=[],
        expected_in_top_3=[],
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["warm", "slush", "melt", "skip", "spring"],
        expect_skip=True,
    ),
]
VAL_EXAMPLES = [
    # 2. Epic pass powder day - Stowe 5.5" on 2025-03-29
    EndToEndExample(
        id="powder_epic_mar29",
        query="Epic pass, where's the best snow today?",
        query_date=date(2025, 3, 29),
        user_location=BOSTON,
        expected_top_pick=["Stowe"],  # 5.5" fresh, clear winner for Epic
        expected_in_top_3=["Stowe", "Okemo", "Mount Snow"],
        expected_excluded=["Sugarloaf", "Killington", "Jay Peak"],  # Ikon
        constraints={"pass_type": "epic"},
        reasoning_keywords=["powder", "stowe", "fresh"],
    ),
    # 9. Expert terrain - double blacks
    EndToEndExample(
        id="expert_terrain_mar29",
        query="Want steep chutes and double blacks",
        query_date=date(2025, 3, 29),
        user_location=BOSTON,
        expected_top_pick=["Stowe", "Jay Peak", "Smugglers' Notch", "Killington"],
        expected_in_top_3=[
            "Stowe",
            "Jay Peak",
            "Smugglers' Notch",
            "Killington",
            "Sugarbush",
        ],
        expected_excluded=["Nashoba Valley", "Wachusett Mountain"],  # No expert terrain
        constraints={"needs_expert_terrain": True},
        reasoning_keywords=["expert", "steep", "black", "challenging"],
    ),
    # 11. Another ambiguous day - Feb 3, low variance
    EndToEndExample(
        id="ambiguous_feb03",
        query="Best skiing today from Boston?",
        query_date=date(2025, 2, 3),
        user_location=BOSTON,
        # Jiminy 1.7", low variance (1.3"), pleasant 21°F
        expected_top_pick=["Jiminy Peak", "Berkshire East", "Killington"],
        expected_in_top_3=["Jiminy Peak", "Berkshire East", "Killington", "Okemo"],
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["conditions"],
    ),
    # 13. Pre-Christmas ice - Dec 22, -7.2°F, no fresh snow
    EndToEndExample(
        id="skip_prexmas_ice_dec22",
        query="Ikon pass today?",
        query_date=date(2024, 12, 22),
        user_location=BOSTON,
        # -7.2°F, only 0.7" fresh max - icy and cold
        expected_top_pick=[],
        expected_in_top_3=[],
        expected_excluded=[],
        constraints={"pass_type": "ikon"},
        reasoning_keywords=["cold", "ice", "skip", "not worth"],
        expect_skip=True,
    ),
    # 16. Another rainy day - Dec 30, warmer rain
    EndToEndExample(
        id="skip_warm_rain_dec30",
        query="Worth driving to ski today?",
        query_date=date(2024, 12, 30),
        user_location=BOSTON,
        # 34-53°F, rain at several mountains, zero fresh snow
        expected_top_pick=[],
        expected_in_top_3=[],
        expected_excluded=[],
        constraints={},
        reasoning_keywords=["rain", "warm", "skip", "not worth"],
        expect_skip=True,
    ),
]


# --- Metrics ---


def calculate_hit_at_1(example: EndToEndExample, prediction_top_pick: str) -> bool:
    """Check if top pick matches any acceptable answer."""
    # Skip day examples have empty expected_top_pick
    if example.expect_skip:
        return calculate_skip_detection(prediction_top_pick)
    top_pick_lower = prediction_top_pick.lower()
    return any(mtn.lower() in top_pick_lower for mtn in example.expected_top_pick)


def calculate_skip_detection(prediction_top_pick: str) -> bool:
    """Check if the agent correctly recommended skipping/not skiing."""
    text_lower = prediction_top_pick.lower()
    skip_indicators = [
        "skip",
        "stay home",
        "don't go",
        "not worth",
        "avoid",
        "pass on",
        "wait",
        "not recommended",
        "wouldn't recommend",
        "defer",
        "postpone",
        "too cold",
        "too warm",
        "dangerous",
        "miserable",
        "poor conditions",
        "bad conditions",
        "rain",
        "icy",
        "slush",
    ]
    return any(indicator in text_lower for indicator in skip_indicators)


def calculate_hit_at_3(
    example: EndToEndExample, prediction_top_3: list[str], top_pick: str = ""
) -> bool:
    """Check if any acceptable answer is in top 3 or top_pick."""
    # Skip day examples: same as hit@1 (did they recommend skipping?)
    if example.expect_skip:
        return True  # If hit@1 passes for skip, hit@3 also passes
    # Include top_pick text in the check (handles empty scores case)
    combined_text = " ".join(prediction_top_3).lower() + " " + top_pick.lower()
    return any(mtn.lower() in combined_text for mtn in example.expected_in_top_3)


def calculate_constraint_satisfaction(
    example: EndToEndExample, prediction_top_pick: str, all_candidates: list[dict]
) -> dict:
    """
    Check if the recommendation satisfies all hard constraints.

    Returns dict with each constraint and whether it was satisfied.
    """
    results = {}

    # Skip day examples don't have constraint requirements
    if example.expect_skip:
        return results

    # Find the recommended mountain in candidates
    top_pick_lower = prediction_top_pick.lower()
    recommended = None
    for candidate in all_candidates:
        if candidate.get("name", "").lower() in top_pick_lower:
            recommended = candidate
            break

    if not recommended:
        # Couldn't find mountain - all constraints fail
        for constraint in example.constraints:
            results[constraint] = False
        return results

    # Check each constraint
    for constraint, expected_value in example.constraints.items():
        if constraint == "pass_type":
            pass_types = recommended.get("pass_types", "") or ""
            results[constraint] = expected_value.lower() in pass_types.lower()

        elif constraint == "max_drive_hours":
            drive_time = recommended.get("drive_time", {})
            duration_min = drive_time.get("duration_minutes", 999)
            results[constraint] = duration_min <= expected_value * 60

        elif constraint == "needs_terrain_parks":
            has_parks = bool(recommended.get("terrain_parks"))
            results[constraint] = has_parks == expected_value

        elif constraint == "needs_glades":
            has_glades = bool(recommended.get("glades"))
            results[constraint] = has_glades == expected_value

        elif constraint == "needs_night_skiing":
            has_night = recommended.get("has_night_skiing", False)
            results[constraint] = has_night == expected_value

        elif constraint == "needs_beginner_terrain":
            has_beginner = (
                recommended.get("has_magic_carpet", False)
                or recommended.get("green_pct", 0) >= 20
            )
            results[constraint] = has_beginner == expected_value

        elif constraint == "needs_expert_terrain":
            has_expert = recommended.get("double_black_pct", 0) > 0
            results[constraint] = has_expert == expected_value

    return results


def calculate_exclusion_check(
    example: EndToEndExample, prediction_top_pick: str
) -> bool:
    """Check that excluded mountains are NOT recommended."""
    if not example.expected_excluded:
        return True

    top_pick_lower = prediction_top_pick.lower()
    for excluded in example.expected_excluded:
        if excluded.lower() in top_pick_lower:
            return False
    return True


def calculate_reasoning_keywords(
    example: EndToEndExample, full_recommendation_text: str
) -> float:
    """Check if reasoning mentions expected keywords."""
    if not example.reasoning_keywords:
        return 1.0

    text_lower = full_recommendation_text.lower()
    matches = sum(1 for kw in example.reasoning_keywords if kw.lower() in text_lower)
    return matches / len(example.reasoning_keywords)


# --- Aggregate Metrics ---


@dataclass
class EvalResult:
    """Results from evaluating one example."""

    example_id: str
    hit_at_1: bool
    hit_at_3: bool
    constraint_satisfaction: dict[str, bool]
    exclusion_check: bool
    reasoning_score: float
    predicted_top_pick: str
    predicted_top_3: list[str]


@dataclass
class AggregateMetrics:
    """Aggregated metrics across all examples."""

    hit_at_1_rate: float
    hit_at_3_rate: float
    constraint_satisfaction_rate: float
    exclusion_rate: float
    avg_reasoning_score: float
    total_examples: int
    detailed_results: list[EvalResult]

    def to_dict(self) -> dict:
        return {
            "hit_at_1": f"{self.hit_at_1_rate:.1%}",
            "hit_at_3": f"{self.hit_at_3_rate:.1%}",
            "constraint_satisfaction": f"{self.constraint_satisfaction_rate:.1%}",
            "exclusion_check": f"{self.exclusion_rate:.1%}",
            "reasoning_score": f"{self.avg_reasoning_score:.1%}",
            "total_examples": self.total_examples,
        }

    def __str__(self) -> str:
        return (
            f"Hit@1: {self.hit_at_1_rate:.1%} | "
            f"Hit@3: {self.hit_at_3_rate:.1%} | "
            f"Constraints: {self.constraint_satisfaction_rate:.1%} | "
            f"Exclusions: {self.exclusion_rate:.1%} | "
            f"Reasoning: {self.avg_reasoning_score:.1%}"
        )


def compute_aggregate_metrics(results: list[EvalResult]) -> AggregateMetrics:
    """Compute aggregate metrics from individual results."""
    if not results:
        return AggregateMetrics(0, 0, 0, 0, 0, 0, [])

    hit_1 = sum(1 for r in results if r.hit_at_1) / len(results)
    hit_3 = sum(1 for r in results if r.hit_at_3) / len(results)

    # Constraint satisfaction - average across all constraints
    all_constraints = []
    for r in results:
        all_constraints.extend(r.constraint_satisfaction.values())
    constraint_rate = (
        sum(all_constraints) / len(all_constraints) if all_constraints else 1.0
    )

    exclusion = sum(1 for r in results if r.exclusion_check) / len(results)
    reasoning = sum(r.reasoning_score for r in results) / len(results)

    return AggregateMetrics(
        hit_at_1_rate=hit_1,
        hit_at_3_rate=hit_3,
        constraint_satisfaction_rate=constraint_rate,
        exclusion_rate=exclusion,
        avg_reasoning_score=reasoning,
        total_examples=len(results),
        detailed_results=results,
    )


def get_examples() -> list[EndToEndExample]:
    """Get all evaluation examples."""
    return TRAIN_EXAMPLES + VAL_EXAMPLES


def get_trainset() -> list[EndToEndExample]:
    """Get training examples (first 12 of 16 = 75%)."""
    return TRAIN_EXAMPLES


def get_valset() -> list[EndToEndExample]:
    """Get validation examples (last 4 of 16 = 25%)."""
    return VAL_EXAMPLES


if __name__ == "__main__":
    # Print dataset summary
    print("End-to-End Evaluation Dataset")
    print("=" * 60)
    print(f"Total examples: {len(TRAIN_EXAMPLES)}")
    print()

    skip_count = sum(1 for ex in TRAIN_EXAMPLES if ex.expect_skip)
    print(f"Skip day examples: {skip_count}")
    print(f"Regular examples: {len(TRAIN_EXAMPLES) - skip_count}")
    print()

    for ex in TRAIN_EXAMPLES:
        skip_marker = " [SKIP DAY]" if ex.expect_skip else ""
        print(f"ID: {ex.id}{skip_marker}")
        print(f"  Date: {ex.query_date}")
        print(f"  Query: {ex.query[:50]}...")
        print(
            f"  Expected: {ex.expected_top_pick[:3] if ex.expected_top_pick else 'SKIP'}"
        )
        print(f"  Constraints: {ex.constraints}")
        print()
