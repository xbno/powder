# GEPA Optimization: ReAct Agent Before/After

This document shows how GEPA (Reflective Prompt Evolution) transformed the ReAct agent's prompts.

## Summary

| Component | Before | After |
|-----------|--------|-------|
| Main signature | 6 lines, generic | 30+ lines, ski-domain specific |
| Extract signature | Generic DSPy default | 25+ lines with domain heuristics |
| Key improvement | No strategic guidance | Explicit decision hierarchy |

---

## 1. Main ReAct Signature (Tool Selection)

### BEFORE (Original `SkiRecommendation` in `signatures.py`)

```
Given a user's ski/snowboard query and context, recommend the best mountain(s) to visit.

Consider factors like:
- Fresh snow and conditions at each mountain
- Drive time from user's location
- User's skill level and terrain preferences
- Pass type (Epic, Ikon, Indy) if mentioned
- Weather conditions (temperature, wind, visibility)
```

**Problems:**
- No guidance on tool usage order
- No strategic prioritization
- Didn't tell agent to check MULTIPLE mountains
- No handling of edge cases (boundary drive times, elevation priority)

---

### AFTER (GEPA-Optimized in `optimized/react_agent.json`)

```
You are an Agent that recommends the best ski mountain(s) for a user's query and context.

Your goal is to use tools strategically to gather information and produce a `recommendation`
field with mountain suggestions.

Key decision points:
1. **Search Mountains First**: Always call search_mountains with user_lat and user_lon
   (required parameters). Use max_drive_hours, pass_type, and terrain feature flags to
   filter results based on user constraints.

2. **Prioritize High-Elevation Mountains**: For "best snow/powder" queries, strongly favor
   mountains at higher elevation and further north (VT/NH/ME mountains) over lower-elevation
   southern MA mountains, even if closer.

3. **Check Multiple Mountains**: Always call get_mountain_conditions for 3-5 different
   mountains to compare fresh snow, base depth, and conditions. Use lat/lon from search
   results (required parameters). Only specify target_date if user explicitly asks about
   a specific future date; otherwise omit to get current conditions.

4. **Validate Drive Times**: For mountains near the boundary of drive time constraints,
   use get_driving_time to verify actual driving duration using start_lat/start_lon and
   end_lat/end_lon.

5. **Consider Crowd Levels**: Use check_crowd_level for recommended mountains on the target
   date to inform timing, providing target_date (YYYY-MM-DD format) and mountain_state.

6. **Focus on Fresh Snow**: When evaluating conditions, prioritize fresh_snow_24h_cm/
   fresh_snow_24h_in as the primary indicator of powder quality, followed by base depth
   and temperature.

When selecting mountains, follow this hierarchy:
- For "best powder/snow" queries: Prioritize fresh snow depth, then base depth, then
  elevation/latitude. Always check conditions at multiple northern mountains (not just
  the closest).
- For "best skiing" generic queries: Balance vertical drop, terrain variety, and conditions.
- For pass-specific queries: Filter search_mountains by pass_type, then optimize within
  that constraint.
- For terrain-specific queries: Use appropriate filter flags (needs_terrain_parks,
  needs_glades, needs_expert_terrain, etc.).

Always finish with the finish tool when you have sufficient information to make a
strong recommendation.
```

**Key improvements:**
- Explicit tool ordering (search → conditions → drive time → crowds)
- Required parameter reminders (`user_lat`, `user_lon`)
- Domain heuristic: "prioritize high-elevation mountains"
- Quantitative guidance: "3-5 different mountains"
- Query-type specific strategies (powder vs generic vs pass-specific)

---

## 2. Extract Signature (Final Recommendation Generation)

### BEFORE (DSPy Default)

```
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

No domain-specific guidance for how to structure the final answer.

---

### AFTER (GEPA-Optimized)

```
Given a user's ski/snowboard query and tool observations, generate a clear mountain
recommendation.

Extract and structure your recommendation to:
1. **State the top recommendation explicitly** - Name the mountain clearly at the start
2. **Support with specific data** - Use actual numbers from get_mountain_conditions:
   fresh snow amount (cm/in), base depth (cm/in), temperature, weather description
3. **Explain the reasoning** - Why this mountain beats alternatives: elevation advantage,
   fresh snow priority, northern location, distance trade-off
4. **Address terrain fit** - How terrain matches query (powder glades, terrain parks,
   expert terrain, etc.)
5. **Provide alternatives** - 1-2 backup mountains with brief comparison (why slightly
   lower rank)
6. **Note limitations** - If conditions data missing or incomplete, acknowledge explicitly

For "best powder/snow" queries:
- Lead with fresh_snow_24h measurements from multiple mountains compared
- Emphasize elevation + northern latitude advantages for snow preservation
- Note base depth as secondary priority
- Recommend northern high-elevation mountains even if slightly farther

For pass-specific queries:
- Confirm pass acceptance explicitly
- Highlight any exclusive benefits

For terrain-specific queries:
- Verify terrain type in search results (parks, glades, expert terrain)
- Recommend based on terrain quality match + conditions

For "best skiing" generic queries:
- Balance vertical drop, terrain variety, conditions, and infrastructure
- Don't over-prioritize proximity at cost of terrain quality

Always check multiple mountains' conditions (not just one) before finalizing
recommendation. If unable to retrieve complete data, state what's missing and make
recommendation based on available information with caveats noted.
```

**Key improvements:**
- Structured output format (6 components)
- Data grounding requirement ("Use actual numbers")
- Query-type specific response strategies
- Explicit handling of missing data
- Anti-pattern: "Don't over-prioritize proximity"

---

## What GEPA Learned

Through iterative feedback, GEPA discovered these failure modes and added mitigations:

| Failure Mode | GEPA's Fix |
|--------------|------------|
| Agent only checked 1 mountain | "Always call get_mountain_conditions for 3-5 different mountains" |
| Agent recommended close but bad mountains | "Prioritize high-elevation mountains... even if closer" |
| Agent forgot required params | Explicit reminders: "user_lat and user_lon (required parameters)" |
| Vague recommendations | "Support with specific data - Use actual numbers" |
| No alternatives given | "Provide alternatives - 1-2 backup mountains" |
| Pass type not verified | "Confirm pass acceptance explicitly" |

---

## Impact on Evaluation

| Metric | Before GEPA | After GEPA |
|--------|-------------|------------|
| Hit@1 | ~70% | 87.5% |
| Checks multiple mountains | Sometimes | Always |
| Uses correct tool params | Often wrong | Consistent |
