# Presentation Notes

## 1. Why skiing

- Snowboard instructor at Nashoba in high school
- Grew up skiing with family - VT, NH, Maine
- Now I'm lazy - only want to go on good days
- No more suffering through -30°F days at Tremblant for one run
- Building what I actually want: "is today worth the drive?"
- Building what my buddy would want: "wheres the powder?"

## 2. What data do you need

- **Weather**: fresh snow, temp, wind - determines if it's worth going
- **Mountain metadata**: terrain, pass types, blacks vs greens, glades, vertical - for matching preferences
- **Driving time**: need user location, a 5hr drive for mediocre snow isn't worth it
- Same query from Boston vs NYC gives different answers (Maine is closer to Boston)

## 3. Backtest data vs mocking

- Mocking works for signature unit tests (fixed inputs)
- Mocking breaks for ReAct - you don't know which mountains it'll query
- Solution: fetch real weather for entire 2024-2025 season (136 days × 31 mountains)
- Stored in `fixtures/by_date.json` - any date can be replayed deterministically

## 4. Finding good eval examples

- `find_interesting_days.py` analyzes historic data
- Looks for: powder days (high variance), skip days (brutal cold), ambiguous days (similar everywhere)
- Example: Feb 17 Sugarloaf had 5.7" while avg was 1.2" - clear winner

## 5. Tooling for adding mountains

- Slash command `.claude/commands/add_mountain.md` - Claude researches and populates metadata
- `seed_missing_mountains.py` - batch add mountains
- `validate_mountain.py` - check schema consistency
- `fetch_historic.py` - pull Dec 1 - Apr 15 weather for all mountains

## 6. Pipeline stages - the why

**Inputs**: query + date (for weather) + location (for distance)

**Stage 1 - ParseSkiQuery**
- Extract structured filters from natural language
- Hard filters (pass_type) → DB query
- Soft prefs (vibe) → scoring

**Stage 2 - AssessConditions** ← this is the key one
- Look at ALL candidates, assess "is today worth it?"
- Without this you can't tell "great day at X" from "X is best of bad options"
- Enables skip-day detection - can say "poor" and downstream knows not to force a rec

**Stage 3 - ScoreMountain**
- Score each candidate using day assessment context
- Scores give absolute quality (all <50 = skip day)
- GEPA had to teach it to be harsh (most days are 40-65, not 70+)

**Stage 4 - GenerateRecommendation**
- Take scores, produce final output
- This is the ranker but also considers crowds, frames appropriately
- Can recommend "skip today" if scores are low

## 7. Tools

- `search_mountains` - DB query with filters
- `get_mountain_conditions` - weather API per mountain
- `get_driving_time` - routing API
- `check_crowd_level` - holiday detection

Tools are straightforward - intelligence is in the signatures

## 8. Evaluation

- **Hit@1**: right mountain recommended (fuzzy - top pick can match ANY mountain in expected list)
- **Hit@3**: right mountain in top 3
- **Constraint Satisfaction**: respected pass type, drive time
- **Skip Detection**: said "don't go" on bad days (keyword match)
- All deterministic - no LLM-as-judge
- Kept scoring generous intentionally - lots of room for interpretation in ski recs

## 9. GEPA results

- 41.7% → 93.8% Hit@1
- What it learned:
  - "stay_home" broke parsing (not a valid output)
  - 38-40°F with no fresh = poor (was being called fair)
  - Don't overweight proximity (Nashoba kept beating Killington)
  - Check multiple mountains (ReAct was lazy)

## 10. GEPA experience

- Wanted to try it after reading the paper - super easy to implement with DSPy
- **Only as good as your examples** - if you have leaks or incorrect values, you'll craft wonky criteria
- Spent ~$15 over probably 5 iterations, threw a few out after fixing bugs in examples
- Focused strictly on Hit@1 and Hit@3 as the optimization target
- The optimized prompts are surprisingly readable - you can see exactly what it learned

## 11. Pipeline vs ReAct

- Pipeline: 93.8% accurate, explainable, each sig optimizes independently
- ReAct: 87.5% accurate, flexible, single signature harder to tune
- Pipeline wins on reliability, ReAct wins on novel queries
- **Speed**: ReAct is actually faster - doesn't exhaustively check every mountain
  - Pipeline: always scores all candidates (10 LLM calls for 7 mountains)
  - ReAct: checks 2-4 mountains then decides (4-8 LLM calls total)

## 12. Demo commands

```bash
python -m powder --date 2025-02-17 "Best powder with Ikon pass?"  # powder day
python -m powder --date 2025-01-08 "Worth skiing today?"          # skip day
make eval                                                          # run evals
```

## 13. Would be nice to add

- **Weather forecast data** - currently using actual measured weather (historic or current day)
  - Forecast data is different from measurements - predictions vs observations
  - Would unlock "where should I ski this weekend?" queries
  - Open-Meteo has forecast API, just haven't wired it up
- Lift status (Liftie API) - real-time open/closed/hold
- Trail grooming reports - which trails were groomed overnight
- Snow quality inference - rain→freeze = icy, warm afternoon = slushy
