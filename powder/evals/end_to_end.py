"""
End-to-end evaluation dataset and metrics for the full ski recommendation pipeline.

This is the KEY evaluation for the assignment - it measures:
1. Hit@1 - Did we recommend the right mountain as top pick?
2. Hit@3 - Is the right mountain in our top 3?
3. Constraint Satisfaction - Did we respect all hard constraints?
4. Reasoning Accuracy - Are the facts in our recommendation correct?

All metrics are DETERMINISTIC (no LLM scoring).
"""

import json
from datetime import date
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EndToEndExample:
    """
    A complete evaluation example with:
    - Input query and context
    - Mocked conditions for reproducibility
    - Ground truth for evaluation
    """

    id: str
    query: str
    query_date: date
    user_location: dict  # {name, lat, lon}

    # Mocked conditions for each mountain (for reproducible eval)
    # Maps mountain name -> conditions dict
    conditions_snapshot: dict[str, dict]

    # Ground truth
    expected_top_pick: list[str]  # Acceptable top picks
    expected_in_top_3: list[str]  # Should appear in top 3
    expected_excluded: list[str] = field(default_factory=list)  # Should NOT appear

    # Constraints that must be satisfied
    constraints: dict = field(default_factory=dict)
    # e.g., {"pass_type": "ikon", "max_drive_hours": 3.0, "needs_terrain_parks": True}

    # Optional: expected reasoning keywords
    reasoning_keywords: list[str] = field(default_factory=list)


# --- Evaluation Dataset ---

BOSTON = {"name": "Boston, MA", "lat": 42.3601, "lon": -71.0589}
NYC = {"name": "New York, NY", "lat": 40.7128, "lon": -74.0060}


# Standard condition snapshots for reproducibility
POWDER_CONDITIONS = {
    "Stowe": {
        "fresh_snow_24h_in": 14,
        "snow_depth_in": 48,
        "temp_f": 18,
        "wind_mph": 12,
        "visibility_mi": 10,
    },
    "Killington": {
        "fresh_snow_24h_in": 10,
        "snow_depth_in": 42,
        "temp_f": 20,
        "wind_mph": 15,
        "visibility_mi": 8,
    },
    "Sugarbush": {
        "fresh_snow_24h_in": 12,
        "snow_depth_in": 45,
        "temp_f": 19,
        "wind_mph": 10,
        "visibility_mi": 10,
    },
    "Jay Peak": {
        "fresh_snow_24h_in": 16,
        "snow_depth_in": 55,
        "temp_f": 15,
        "wind_mph": 18,
        "visibility_mi": 6,
    },
    "Okemo": {
        "fresh_snow_24h_in": 8,
        "snow_depth_in": 38,
        "temp_f": 22,
        "wind_mph": 8,
        "visibility_mi": 10,
    },
    "Mount Snow": {
        "fresh_snow_24h_in": 6,
        "snow_depth_in": 35,
        "temp_f": 24,
        "wind_mph": 10,
        "visibility_mi": 10,
    },
    "Stratton": {
        "fresh_snow_24h_in": 9,
        "snow_depth_in": 40,
        "temp_f": 21,
        "wind_mph": 12,
        "visibility_mi": 10,
    },
}

ICY_CONDITIONS = {
    "Killington": {
        "fresh_snow_24h_in": 0,
        "snow_depth_in": 28,
        "temp_f": 38,
        "wind_mph": 5,
        "visibility_mi": 10,
    },
    "Okemo": {
        "fresh_snow_24h_in": 0,
        "snow_depth_in": 30,
        "temp_f": 40,
        "wind_mph": 8,
        "visibility_mi": 10,
    },
    "Stowe": {
        "fresh_snow_24h_in": 0,
        "snow_depth_in": 32,
        "temp_f": 36,
        "wind_mph": 10,
        "visibility_mi": 10,
    },
    "Sugarbush": {
        "fresh_snow_24h_in": 0,
        "snow_depth_in": 26,
        "temp_f": 39,
        "wind_mph": 6,
        "visibility_mi": 10,
    },
}


EXAMPLES = [
    # 1. Simple powder chase with Ikon pass
    EndToEndExample(
        id="powder_ikon_boston",
        query="Best powder day within 3 hours, I have Ikon pass",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        expected_top_pick=["Jay Peak", "Sugarbush", "Killington"],  # All Ikon
        expected_in_top_3=["Jay Peak", "Sugarbush", "Killington"],
        expected_excluded=["Stowe", "Okemo", "Mount Snow"],  # Epic mountains
        constraints={"pass_type": "ikon", "max_drive_hours": 3.0},
        reasoning_keywords=["powder", "fresh", "ikon"],
    ),
    # 2. Epic pass holder on powder day
    EndToEndExample(
        id="powder_epic_boston",
        query="Where should I ski today? Epic pass, don't mind driving",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        expected_top_pick=["Stowe"],  # Most fresh snow on Epic
        expected_in_top_3=["Stowe", "Okemo", "Mount Snow"],
        expected_excluded=["Jay Peak", "Killington", "Sugarbush"],  # Ikon
        constraints={"pass_type": "epic"},
        reasoning_keywords=["powder", "fresh", "14"],
    ),
    # 3. Terrain park seeker
    EndToEndExample(
        id="park_day_boston",
        query="Looking for the best terrain park, intermediate snowboarder",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Killington and Okemo have superpipes
        expected_top_pick=["Killington", "Okemo", "Mount Snow"],
        expected_in_top_3=["Killington", "Okemo", "Mount Snow"],
        expected_excluded=["Mad River Glen"],  # No parks, no snowboarding
        constraints={"needs_terrain_parks": True},
        reasoning_keywords=["park", "terrain", "features"],
    ),
    # 4. Beginner/family day
    EndToEndExample(
        id="beginner_family",
        query="Taking my kids for their first ski lesson, need great learning area",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Okemo, Smugglers, Stratton, Waterville have excellent learning areas
        expected_top_pick=["Okemo", "Smugglers' Notch", "Stratton", "Waterville Valley"],
        expected_in_top_3=["Okemo", "Smugglers' Notch", "Stratton", "Waterville Valley", "Bretton Woods"],
        expected_excluded=["Mad River Glen"],  # Basic learning area
        constraints={"needs_beginner_terrain": True},
        reasoning_keywords=["beginner", "learning", "family", "lesson"],
    ),
    # 5. Night skiing request
    EndToEndExample(
        id="night_skiing",
        query="Any mountains with night skiing tonight? Want to go after work",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Killington, Nashoba, Gunstock have night skiing
        expected_top_pick=["Nashoba Valley", "Gunstock", "Killington"],
        expected_in_top_3=["Nashoba Valley", "Gunstock", "Killington"],
        expected_excluded=["Stowe", "Sugarbush", "Jay Peak"],  # No night skiing
        constraints={"needs_night_skiing": True},
        reasoning_keywords=["night", "evening", "lights"],
    ),
    # 6. Glade/tree skiing focus
    EndToEndExample(
        id="glade_skiing",
        query="Looking for tree skiing and glades, Ikon pass",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Jay Peak is famous for glades, Ikon pass
        expected_top_pick=["Jay Peak"],
        expected_in_top_3=["Jay Peak", "Sugarbush", "Killington"],
        expected_excluded=["Nashoba Valley"],  # No glades
        constraints={"pass_type": "ikon", "needs_glades": True},
        reasoning_keywords=["glades", "trees", "woods"],
    ),
    # 7. Short drive preference
    EndToEndExample(
        id="short_drive",
        query="Quick trip, max 1.5 hour drive from Boston",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Only Nashoba and Gunstock are within 1.5 hours
        expected_top_pick=["Nashoba Valley", "Gunstock"],
        expected_in_top_3=["Nashoba Valley", "Gunstock", "Waterville Valley"],
        expected_excluded=["Jay Peak", "Stowe", "Sugarbush"],  # Too far
        constraints={"max_drive_hours": 1.5},
        reasoning_keywords=["close", "quick", "drive"],
    ),
    # 8. Expert terrain
    EndToEndExample(
        id="expert_terrain",
        query="Want to hit some double blacks and steep chutes, advanced skier",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Jay Peak, Killington, Sugarbush, Stowe have double blacks
        expected_top_pick=["Jay Peak", "Killington", "Stowe", "Smugglers' Notch"],
        expected_in_top_3=["Jay Peak", "Killington", "Stowe", "Sugarbush", "Smugglers' Notch"],
        expected_excluded=["Nashoba Valley", "Gunstock", "Okemo"],  # No double blacks
        constraints={"needs_expert_terrain": True},
        reasoning_keywords=["expert", "steep", "black", "challenging"],
    ),
    # 9. Icy day - should still give reasonable recommendation
    EndToEndExample(
        id="icy_day_ikon",
        query="Where to ski today with Ikon pass?",
        query_date=date(2025, 1, 20),
        user_location=BOSTON,
        conditions_snapshot=ICY_CONDITIONS,
        expected_top_pick=["Killington", "Sugarbush"],  # Best options on bad day
        expected_in_top_3=["Killington", "Sugarbush"],
        expected_excluded=["Stowe", "Okemo"],  # Epic
        constraints={"pass_type": "ikon"},
        reasoning_keywords=["conditions", "grooming", "snowmaking"],
    ),
    # 10. No pass specified - should consider all options
    EndToEndExample(
        id="no_pass_powder",
        query="Best skiing today, willing to buy a day ticket",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Jay Peak has most fresh snow overall
        expected_top_pick=["Jay Peak", "Stowe"],  # Best snow
        expected_in_top_3=["Jay Peak", "Stowe", "Sugarbush", "Killington"],
        expected_excluded=[],  # All mountains fair game
        constraints={},  # No pass constraint
        reasoning_keywords=["powder", "fresh", "snow"],
    ),
    # 11. Indy pass holder
    EndToEndExample(
        id="indy_pass",
        query="Where can I use my Indy pass? Looking for good terrain",
        query_date=date(2025, 1, 15),
        user_location=BOSTON,
        conditions_snapshot=POWDER_CONDITIONS,
        # Indy mountains: Nashoba, Gunstock, Waterville, Mad River Glen, Smugglers
        expected_top_pick=["Smugglers' Notch", "Mad River Glen", "Waterville Valley"],
        expected_in_top_3=["Smugglers' Notch", "Mad River Glen", "Waterville Valley", "Gunstock"],
        expected_excluded=["Stowe", "Killington", "Sugarbush", "Jay Peak"],  # Not Indy
        constraints={"pass_type": "indy"},
        reasoning_keywords=["indy"],
    ),
    # 12. NYC user - different distances
    EndToEndExample(
        id="nyc_powder_day",
        query="Best powder today from NYC, have Ikon pass",
        query_date=date(2025, 1, 15),
        user_location=NYC,
        conditions_snapshot=POWDER_CONDITIONS,
        # From NYC: Killington and Stratton are closer than Jay Peak
        expected_top_pick=["Killington", "Stratton", "Sugarbush"],
        expected_in_top_3=["Killington", "Stratton", "Sugarbush"],
        expected_excluded=["Stowe", "Okemo"],  # Epic
        constraints={"pass_type": "ikon"},
        reasoning_keywords=["powder", "fresh"],
    ),
]


# --- Metrics ---


def calculate_hit_at_1(example: EndToEndExample, prediction_top_pick: str) -> bool:
    """Check if top pick matches any acceptable answer."""
    top_pick_lower = prediction_top_pick.lower()
    return any(mtn.lower() in top_pick_lower for mtn in example.expected_top_pick)


def calculate_hit_at_3(example: EndToEndExample, prediction_top_3: list[str]) -> bool:
    """Check if any acceptable answer is in top 3."""
    top_3_text = " ".join(prediction_top_3).lower()
    return any(mtn.lower() in top_3_text for mtn in example.expected_in_top_3)


def calculate_constraint_satisfaction(
    example: EndToEndExample, prediction_top_pick: str, all_candidates: list[dict]
) -> dict:
    """
    Check if the recommendation satisfies all hard constraints.

    Returns dict with each constraint and whether it was satisfied.
    """
    results = {}

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
    constraint_rate = sum(all_constraints) / len(all_constraints) if all_constraints else 1.0

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
    return EXAMPLES


# --- Mock Conditions Helper ---


class MockConditions:
    """Context manager to mock weather conditions for reproducible evaluation."""

    def __init__(self, conditions_snapshot: dict[str, dict]):
        self.snapshot = conditions_snapshot
        self._original_get_conditions = None

    def __enter__(self):
        from powder.tools import weather

        self._original_get_conditions = weather.get_conditions

        def mock_get_conditions(lat: float, lon: float, target_date):
            # Find closest mountain by coordinates (rough match)
            for name, conditions in self.snapshot.items():
                # Return mocked conditions for any request
                return {
                    "fresh_snow_24h_cm": conditions.get("fresh_snow_24h_in", 0) * 2.54,
                    "fresh_snow_24h_in": conditions.get("fresh_snow_24h_in", 0),
                    "snow_depth_cm": conditions.get("snow_depth_in", 0) * 2.54,
                    "snow_depth_in": conditions.get("snow_depth_in", 0),
                    "temp_c": (conditions.get("temp_f", 32) - 32) * 5 / 9,
                    "temp_f": conditions.get("temp_f", 32),
                    "wind_kph": conditions.get("wind_mph", 0) * 1.6,
                    "wind_mph": conditions.get("wind_mph", 0),
                    "visibility_km": conditions.get("visibility_mi", 10) * 1.6,
                    "visibility_mi": conditions.get("visibility_mi", 10),
                    "weather_code": 0,
                    "weather_description": "Clear",
                }
            return {}

        weather.get_conditions = mock_get_conditions
        return self

    def __exit__(self, *args):
        from powder.tools import weather

        weather.get_conditions = self._original_get_conditions


if __name__ == "__main__":
    # Print dataset summary
    print("End-to-End Evaluation Dataset")
    print("=" * 60)
    print(f"Total examples: {len(EXAMPLES)}")
    print()

    for ex in EXAMPLES:
        print(f"ID: {ex.id}")
        print(f"  Query: {ex.query[:60]}...")
        print(f"  Expected top: {ex.expected_top_pick}")
        print(f"  Constraints: {ex.constraints}")
        print()
