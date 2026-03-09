# ScoreMountain — Prompt Instructions

Score a single mountain given conditions, preferences, and day context.

Applies contextual boosts (e.g., glades on windy days, gondola on cold days).

Score calibration (BE HARSH - most days are not 70+):
- 85-100: Exceptional - significant fresh snow, ideal temps, matches preferences perfectly
- 70-84: Good day - meaningful fresh snow OR excellent groomed with good temps
- 55-69: Acceptable - skiable but not exciting, or good snow with significant drawbacks
- 40-54: Marginal - only go if desperate to ski, conditions are poor
- 0-39: Skip it - dangerous cold, no snow, or fundamentally unsuitable

Automatic penalties:
- Temps <10°F: Cap score at 60 max (brutal conditions regardless of snow)
- Temps <0°F: Cap score at 40 max (dangerous, stay home)
- Fresh snow <1": -15 points (you're skiing old snow)
- Wind >25mph: -10 points (miserable lift rides, closed terrain)
- Drive >3hrs with poor conditions: Cap at 50 (not worth the drive)
