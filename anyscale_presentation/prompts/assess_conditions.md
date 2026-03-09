# AssessConditions — Prompt Instructions

Assess overall ski conditions across all candidates for the target date.

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

CRITICAL CONSTRAINTS on day_quality output:
- Only valid outputs are: ['fair', 'poor', 'good', 'excellent']
- "stay_home" is NOT a valid day_quality value
- If conditions are truly bad/unrideable, use 'poor' instead of 'stay_home'
- 'poor' is harsh enough to communicate "don't go" while maintaining valid output format

Temperature interpretation:
- 38-40°F with zero fresh snow = poor (slushy, waterlogged conditions, base deteriorating)
- Cold temps alone without fresh snow may still warrant 'poor' or 'fair' depending on base quality
- Warm temps (>40°F) with no fresh snow is especially bad because it's actively destroying the base

Ranking logic:
- Always identify best_available mountain by comparing fresh snow depth, temperature, and wind conditions
- Fresh snow depth is the primary differentiator when available
- Wind is a secondary but critical factor - high winds (>25mph) can override good snow amounts
- For powder-focused users, heavily weight fresh snow and wind conditions
- For casual users, temperature comfort and groomed conditions matter more

Context narrative should:
- Explain the day's overall character and why you chose that day_quality rating
- Call out specific hazards or limitations (wind closing terrain, temps destroying snow, etc.)
- Address how conditions match user preferences/skill level
- Give clear guidance on whether this is a "go" day or skip day
- Mention if some mountains are playable while others aren't due to specific conditions
