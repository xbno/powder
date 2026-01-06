"""DSPy signatures for ski recommendation agent."""

import dspy


class ParseSkiQuery(dspy.Signature):
    """Extract structured constraints from natural language ski query.

    Separates HARD FILTERS (used to exclude mountains from DB) from
    SOFT PREFERENCES (used to score/rank candidates).
    """

    query: str = dspy.InputField()
    user_context: str = dspy.InputField(desc="Current date, location defaults")

    # Hard filters (drive DB query) - flattened from all group members
    target_date: str = dspy.OutputField(
        desc="YYYY-MM-DD, 'today', 'tomorrow', or 'unspecified' if no date mentioned"
    )
    max_drive_hours: float | None = dspy.OutputField(desc="Max drive time, null if not specified")
    pass_type: str | None = dspy.OutputField(desc="epic/ikon/indy or null")
    needs_terrain_parks: bool = dspy.OutputField(
        desc="True if mentions park, jumps, rails, boxes, halfpipe, pipe, features, freestyle"
    )
    needs_glades: bool = dspy.OutputField(
        desc="True if mentions glades, trees, tree skiing, woods, forest"
    )
    needs_beginner_terrain: bool = dspy.OutputField(
        desc="True if mentions beginner, first-timer, learning, never skied, bunny hill, magic carpet"
    )
    needs_expert_terrain: bool = dspy.OutputField(
        desc="True if mentions double blacks, expert, extreme, steeps, cliffs, chutes"
    )
    needs_night_skiing: bool = dspy.OutputField(
        desc="True if mentions night skiing, evening, after work, lights"
    )

    # Soft preferences (affect scoring)
    skill_level: str | None = dspy.OutputField(desc="beginner/intermediate/advanced/expert or null")
    activity: str | None = dspy.OutputField(desc="ski/snowboard/either or null")
    vibe: str | None = dspy.OutputField(desc="powder_chase/casual/park_day/learning/family_day or null")


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
