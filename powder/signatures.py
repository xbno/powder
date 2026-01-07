"""DSPy signatures for ski recommendation agent."""

import dspy
from pydantic import BaseModel
from typing import Literal


class ParsedQuery(BaseModel):
    """Pydantic model for parsed ski query - Optional types handle null coercion."""

    # Hard filters
    target_date: str
    max_drive_hours: float | None = None
    pass_type: Literal["epic", "ikon", "indy"] | None = None
    needs_terrain_parks: bool = False
    needs_glades: bool = False
    needs_beginner_terrain: bool = False
    needs_expert_terrain: bool = False
    needs_night_skiing: bool = False

    # Soft preferences
    skill_level: Literal["beginner", "intermediate", "advanced", "expert"] | None = None
    activity: Literal["ski", "snowboard", "either"] | None = None
    vibe: Literal["powder_chase", "casual", "park_day", "learning", "family_day"] | None = None


class ParseSkiQuery(dspy.Signature):
    """Extract structured constraints from natural language ski query.

    Separates HARD FILTERS (used to exclude mountains from DB) from
    SOFT PREFERENCES (used to score/rank candidates).
    """

    query: str = dspy.InputField()
    user_context: str = dspy.InputField(desc="Current date, location defaults")

    # Output is a structured Pydantic model
    parsed: ParsedQuery = dspy.OutputField(
        desc="Structured query with filters and preferences"
    )


class AssessConditions(dspy.Signature):
    """Assess overall ski conditions across all candidates for the target date.

    Creates shared context for scoring - prevents redundant per-mountain reasoning.
    """

    all_candidates: str = dspy.InputField(desc="JSON of all candidates with conditions")
    user_preferences: str = dspy.InputField(desc="Parsed preferences from query")

    day_quality: str = dspy.OutputField(desc="excellent/good/fair/poor/stay_home")
    best_available: str = dspy.OutputField(
        desc="Key fact: e.g. 'Stowe has 15\" fresh, everyone else <5\"'"
    )
    day_context: str = dspy.OutputField(
        desc="Notable factors: wind, temp, visibility patterns across region"
    )


class ScoreMountain(dspy.Signature):
    """Score a single mountain given conditions, preferences, and day context.

    Applies contextual boosts (e.g., glades on windy days, gondola on cold days).
    """

    mountain: str = dspy.InputField(desc="Mountain data with current conditions")
    user_preferences: str = dspy.InputField(desc="Parsed preferences from query")
    day_context: str = dspy.InputField(desc="Overall day quality and mode")

    score: float = dspy.OutputField(desc="0-100 appeal score")
    key_pros: str = dspy.OutputField(desc="Top 2-3 reasons to go here")
    key_cons: str = dspy.OutputField(desc="Top 1-2 drawbacks")
    tradeoff_note: str = dspy.OutputField(
        desc="Notable tradeoff, e.g. 'best snow but longest drive'"
    )


class GenerateRecommendation(dspy.Signature):
    """Generate final recommendation with tradeoff analysis.

    Uses day context to frame appropriately (chase powder vs minimize hassle).
    """

    query: str = dspy.InputField(desc="Original user query")
    day_assessment: str = dspy.InputField(desc="Overall conditions and mode")
    scored_candidates: str = dspy.InputField(desc="Mountains with scores and tradeoffs")
    crowd_context: str = dspy.InputField(desc="Holiday/vacation week info")

    top_pick: str = dspy.OutputField(desc="Primary recommendation with reasoning")
    alternatives: str = dspy.OutputField(desc="1-2 alternatives with tradeoff explanation")
    caveat: str = dspy.OutputField(
        desc="Any important caveat, e.g. 'but tomorrow looks better'"
    )


# Legacy signature for basic agent (kept for backwards compatibility)
class SkiRecommendation(dspy.Signature):
    """Given a user's ski/snowboard query and context, recommend the best mountain(s) to visit.

    Consider factors like:
    - Fresh snow and conditions at each mountain
    - Drive time from user's location
    - User's skill level and terrain preferences
    - Pass type (Epic, Ikon, Indy) if mentioned
    - Weather conditions (temperature, wind, visibility)
    """

    query: str = dspy.InputField(
        desc="User's natural language query about where to ski/snowboard"
    )
    user_context: str = dspy.InputField(
        desc="Context like current date, location, and any user preferences"
    )
    recommendation: str = dspy.OutputField(
        desc="Top 1-3 mountain recommendations with reasoning for each. Include snow conditions, drive time, and why it's a good fit."
    )
