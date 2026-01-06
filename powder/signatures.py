"""DSPy signatures for ski recommendation agent."""

import dspy


class SkiRecommendation(dspy.Signature):
    """Given a user's ski/snowboard query and context, recommend the best mountain(s) to visit.

    Consider factors like:
    - Fresh snow and conditions at each mountain
    - Drive time from user's location
    - User's skill level and terrain preferences
    - Pass type (Epic, Ikon, Indy) if mentioned
    - Weather conditions (temperature, wind, visibility)
    """

    # Inputs
    query: str = dspy.InputField(
        desc="User's natural language query about where to ski/snowboard"
    )
    user_context: str = dspy.InputField(
        desc="Context like current date, location, and any user preferences"
    )

    # Outputs
    recommendation: str = dspy.OutputField(
        desc="Top 1-3 mountain recommendations with reasoning for each. Include snow conditions, drive time, and why it's a good fit."
    )
