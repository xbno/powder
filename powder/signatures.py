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

    BE HARSH. Skiing in bad conditions is miserable and not worth the time/money.

    Day quality calibration:
    - stay_home: Dangerous cold (<0°F), rain, ice storms, or zero fresh snow with icy base
    - poor: Brutal cold (0-10°F) with <2" fresh snow, or warm (>40°F) with no fresh snow
    - fair: Cold but skiable (10-25°F) with some fresh snow (2-4"), or decent base conditions
    - good: Good temps (15-32°F) with meaningful fresh snow (4-8") or excellent groomed conditions
    - excellent: Prime temps (18-28°F) with significant fresh snow (8"+) and low wind

    Key factors that DOWNGRADE a day:
    - Sub-10°F temps make skiing miserable (exposed skin, frozen gear, short sessions)
    - <2" fresh snow means you're skiing yesterday's conditions
    - High winds (>25mph) close upper terrain and make lifts brutal
    - Rain or temps >40°F destroy snow quality rapidly
    """

    all_candidates: str = dspy.InputField(desc="JSON of all candidates with conditions")
    user_preferences: str = dspy.InputField(desc="Parsed preferences from query")

    day_quality: str = dspy.OutputField(
        desc="excellent/good/fair/poor/stay_home - BE HARSH, don't sugarcoat bad days"
    )
    best_available: str = dspy.OutputField(
        desc="Key fact: e.g. 'Stowe has 15\" fresh, everyone else <5\"' - or 'Nothing good, best is X with only Y'"
    )
    day_context: str = dspy.OutputField(
        desc="Notable factors: wind, temp, visibility patterns. Call out if temps are dangerously cold or conditions are poor everywhere."
    )


class ScoreMountain(dspy.Signature):
    """Score a single mountain given conditions, preferences, and day context.

    Applies contextual boosts (e.g., glades on windy days, gondola on cold days).

    Score calibration (BE HARSH - most days are not 70+):
    - 85-100: Exceptional - significant fresh snow, ideal temps, matches preferences perfectly
    - 70-84: Good day - meaningful fresh snow OR excellent groomed with good temps
    - 55-69: Acceptable - skiable but not exciting, or good snow with significant drawbacks
    - 40-54: Marginal - only go if you're desperate to ski, conditions are poor
    - 0-39: Skip it - dangerous cold, no snow, or fundamentally unsuitable

    Automatic penalties:
    - Temps <10°F: Cap score at 60 max (brutal conditions regardless of snow)
    - Temps <0°F: Cap score at 40 max (dangerous, stay home)
    - Fresh snow <1": -15 points (you're skiing old snow)
    - Wind >25mph: -10 points (miserable lift rides, closed terrain)
    - Drive >3hrs with poor conditions: Cap at 50 (not worth the drive)
    """

    mountain: str = dspy.InputField(desc="Mountain data with current conditions")
    user_preferences: str = dspy.InputField(desc="Parsed preferences from query")
    day_context: str = dspy.InputField(desc="Overall day quality and mode")

    score: float = dspy.OutputField(
        desc="0-100 appeal score - BE HARSH, most mountains on most days deserve 40-65"
    )
    key_pros: str = dspy.OutputField(desc="Top 2-3 reasons to go here - be honest if there aren't many")
    key_cons: str = dspy.OutputField(desc="Top 1-2 drawbacks - don't minimize bad conditions")
    tradeoff_note: str = dspy.OutputField(
        desc="Notable tradeoff, e.g. 'best snow but longest drive' or 'closest option but conditions are poor'"
    )


class GenerateRecommendation(dspy.Signature):
    """Generate final recommendation with tradeoff analysis.

    Uses day context to frame appropriately (chase powder vs minimize hassle).

    BE WILLING TO SAY "DON'T GO":
    - If day_quality is "poor" or "stay_home", lead with that assessment
    - If all scores are <50, recommend waiting for better conditions
    - If temps are dangerous (<0°F), prioritize safety over skiing
    - Don't force a recommendation when conditions are genuinely bad

    The user is better served by honest "skip today" advice than a lukewarm
    recommendation that wastes their time and money on a miserable day.
    """

    query: str = dspy.InputField(desc="Original user query")
    day_assessment: str = dspy.InputField(desc="Overall conditions and mode")
    scored_candidates: str = dspy.InputField(desc="Mountains with scores and tradeoffs")
    crowd_context: str = dspy.InputField(desc="Holiday/vacation week info")

    top_pick: str = dspy.OutputField(
        desc="Primary recommendation with reasoning - or 'Skip today' if conditions warrant"
    )
    alternatives: str = dspy.OutputField(
        desc="1-2 alternatives with tradeoff explanation - or 'Wait for better conditions'"
    )
    caveat: str = dspy.OutputField(
        desc="Important caveat - if recommending a skip day, explain when conditions might improve"
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
