# GEPA Optimization: Pipeline Signatures Before/After

This document shows how GEPA transformed the Pipeline's 4 signatures.

## Summary

| Signature | Change Level | Key Addition |
|-----------|--------------|--------------|
| ParseSkiQuery | Minimal | None (Pydantic handles structure) |
| AssessConditions | **Major** | Output constraints, temperature interpretation, ranking logic |
| ScoreMountain | **Major** | Scoring calibration, automatic penalties, contextual boosts |
| GenerateRecommendation | Minimal | None (already had skip-day guidance) |

**Pattern**: The "judgment" signatures (Assess, Score) got heavy optimization. The "structural" signatures (Parse, Generate) stayed mostly the same.

---

## 1. ParseSkiQuery

### BEFORE (Original in `signatures.py`)

```text
Extract structured constraints from natural language ski query.

Separates HARD FILTERS (used to exclude mountains from DB) from
SOFT PREFERENCES (used to score/rank candidates).
```

### AFTER (GEPA-Optimized)

```text
Extract structured constraints from natural language ski query.

Separates HARD FILTERS (used to exclude mountains from DB) from
SOFT PREFERENCES (used to score/rank candidates).
```

**No change** - The Pydantic model (`ParsedQuery`) already enforces structure. GEPA found no improvement opportunities.

---

## 2. AssessConditions

### BEFORE (Original in `signatures.py`)

```text
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
```

### AFTER (GEPA-Optimized)

```text
[Original content preserved, plus:]

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
```

**Key additions:**

| Addition | Why GEPA Added It |
|----------|-------------------|
| Output constraints | LLM was outputting "stay_home" which broke downstream parsing |
| Temperature interpretation | 38-40°F edge cases were being misclassified |
| Ranking logic | LLM wasn't consistently picking the actual best mountain |
| Context narrative checklist | Outputs were missing critical hazard warnings |

---

## 3. ScoreMountain

### BEFORE (Original in `signatures.py`)

```text
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
```

### AFTER (GEPA-Optimized)

```text
Score a single mountain ski day given conditions, preferences, and day context.

TASK OVERVIEW:
You are scoring ski/snowboard mountains to help a user decide whether to ski a
particular mountain on a particular day. The score reflects how good that specific
mountain is on that specific day, accounting for snow conditions, weather, terrain
match, drive time, and contextual factors.

INPUT FORMAT:
- mountain: Object with name, location, terrain details (vertical drop, trail count,
  terrain distribution), terrain parks, glades availability, lift types, snowmaking %,
  conditions (fresh snow, base depth, temp, wind, visibility, weather), and drive time
- user_preferences: Skill level, activity type (ski/snowboard), vibe/goal (casual,
  powder_chase, park_day, etc.), and specific needs (terrain parks, glades)
- day_context: Overall day quality assessment, best available mountains, and
  contextual notes

OUTPUT FORMAT:
- score: Single numeric score (0-100)
- key_pros: 2-3 bullet points of genuine advantages
- key_cons: 2-3 bullet points of real drawbacks
- tradeoff_note: One sentence synthesizing the decision (what you're gaining vs losing)

SCORING CALIBRATION (BE HARSH - most days are not 70+):
- 85-100: Exceptional - significant fresh snow (6"+ typically), ideal temps, perfectly
  matches user preferences/terrain needs
- 70-84: Good day - meaningful fresh snow (4-6") OR excellent groomed conditions with
  good temps, solid match to preferences
- 55-69: Acceptable - skiable but not exciting (2-4" fresh or good snow with drawbacks),
  mediocre match to preferences
- 40-54: Marginal - only go if desperate to ski, poor conditions or significant drawbacks
- 0-39: Skip it - dangerous cold, no snow, fundamentally unsuitable

AUTOMATIC PENALTIES (applied before final score):
- Temps <10°F: Cap score at 60 max (brutal conditions override everything)
- Temps <0°F: Cap score at 40 max (dangerous, strongly recommend staying home)
- Fresh snow <1": -15 points (you're skiing old, tracked snow)
- Wind >25mph: -10 points (miserable lift rides, terrain closures, poor experience)
- Drive time >3 hours with poor/marginal conditions: Cap score at 50 (not worth the effort)

CONTEXTUAL BOOSTS (apply when applicable):
- Glades on windy days (wind >20mph): Glades provide tree protection and often preserve
  snow quality in storms
- Gondolas/enclosed lifts on cold days (temp <15°F): Protected lift rides are valuable
  in brutal cold
- Terrain parks on warm/soft conditions: Parks provide consistent, well-maintained
  surfaces when natural snow is poor
- Strong snowmaking (>90%) on marginal conditions: Extends skiable terrain and provides
  reliable base

DECISION LOGIC:
1. Check automatic penalty conditions first (temps, wind, fresh snow thresholds)
2. Apply base score based on fresh snow and temperature combination
3. Adjust for terrain match with user preferences (e.g., glade-loving skier with glades
   available = boost; park-focused user on powder day with no parks = neutral/penalty)
4. Apply contextual boosts/penalties (wind + glades = good; long drive + poor conditions = bad)
5. Consider vertical drop and trail variety for replay value (small mountains like 240 ft
   vertical limit exploration)
6. Weight day context: If this is a rare excellent snow day everywhere, settling for a
   mediocre mountain is worse than on a poor snow day

TONE & MESSAGING:
- Be honest about tradeoffs: Acknowledge what the user is sacrificing (e.g., "settling
  for half the powder," "limiting yourself to tree skiing")
- Justify short drives with "proximity value" language but don't overweight convenience
- Reference comparative context: If day_context mentions better snow elsewhere,
  acknowledge the deficit
- Validate user preferences: Match recommendations to their stated activity/vibe
- Avoid false positives: A 65-score day is not "good" even if it has some positive aspects
```

**Key additions:**

| Addition | Why GEPA Added It |
|----------|-------------------|
| Input/Output format specs | LLM was misinterpreting JSON structure |
| Contextual boosts | Original only had penalties, not positive adjustments |
| 5-step decision logic | Gives explicit reasoning order |
| Tone & messaging | LLM was being too positive about mediocre days |
| "240 ft vertical" note | GEPA learned small mountains (Nashoba) were being overscored |

---

## 4. GenerateRecommendation

### BEFORE (Original in `signatures.py`)

```text
Generate final recommendation with tradeoff analysis.

Uses day context to frame appropriately (chase powder vs minimize hassle).

BE WILLING TO SAY "DON'T GO":
- If day_quality is "poor" or "stay_home", lead with that assessment
- If all scores are <50, recommend waiting for better conditions
- If temps are dangerous (<0°F), prioritize safety over skiing
- Don't force a recommendation when conditions are genuinely bad

The user is better served by honest "skip today" advice than a lukewarm
recommendation that wastes their time and money on a miserable day.
```

### AFTER (GEPA-Optimized)

```text
[Identical to original]
```

**No change** - The original already had strong skip-day guidance. The upstream signatures (Assess, Score) now produce better inputs, so Generate didn't need optimization.

---

## What GEPA Learned (Failure Analysis)

| Failure Mode | Which Signature | GEPA's Fix |
|--------------|-----------------|------------|
| Invalid "stay_home" output | AssessConditions | Added output constraints |
| 38-40°F misclassified as "fair" | AssessConditions | Added temperature interpretation |
| Mediocre mountains scored 70+ | ScoreMountain | Added tone guidance, contextual boosts |
| Nashoba (240ft) recommended over Killington | ScoreMountain | Added vertical drop note |
| Didn't acknowledge better options elsewhere | ScoreMountain | Added "reference comparative context" |
| Boosts only for penalties, not positives | ScoreMountain | Added contextual boosts section |

---

## Impact on Evaluation

| Metric | Before GEPA | After GEPA |
|--------|-------------|------------|
| Hit@1 | 41.7% | **93.8%** |
| Hit@3 | ~60% | **93.8%** |
| Constraint Satisfaction | ~80% | **100%** |
| Skip Detection | Inconsistent | Reliable |

The biggest win was **ScoreMountain** - teaching the LLM to be harsh and not overweight proximity.
