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
