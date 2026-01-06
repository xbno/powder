# Powder - Ski Day Recommendation Agent

## Philosophy

**Keep it simple.** This is a POC. No over-engineering, no premature abstraction.

## Overview

An AI agent that answers: **"Where should I ski/snowboard today?"**

**Region focus: Northeast US** (Vermont, New Hampshire, Maine, New York, Massachusetts)

Given a natural language query like *"Where should I snowboard this weekend? I'm intermediate, have an Ikon pass, and don't want to drive more than 2.5hrs from Boston"*, the agent will:

1. Parse the query to extract constraints and preferences
2. Filter candidate mountains from a local database
3. Fetch current/forecasted conditions for candidates
4. Score and rank mountains based on conditions + preferences
5. Return top recommendations with reasoning

---

## Architecture

### Agent Flow

```
User Query + Context (date, location)
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 1: Parse Query → Extract Constraints      │
│                                                 │
│  HARD FILTERS (exclude from DB):                │
│  - max_drive_hours: 2.5                         │
│  - pass_type: "ikon"                            │
│  - required_features: ["terrain_parks"]         │
│  - min_difficulty: "black"                      │
│                                                 │
│  SOFT PREFERENCES (affect scoring):             │
│  - skill_level: "intermediate"                  │
│  - activity: "snowboard"                        │
│  - vibe: "park_day"                             │
│                                                 │
│  → DSPy Module: ParseSkiQuery                   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 2: Prefilter Mountains from DB            │
│                                                 │
│  Apply HARD FILTERS before any API calls:       │
│  - Haversine distance < estimate(max_hours)     │
│  - pass_types LIKE '%ikon%'                     │
│  - terrain_parks IS NOT NULL                    │
│  - black_pct > 0 OR double_black_pct > 0        │
│                                                 │
│  Result: Small candidate set (3-8 mountains)    │
│  → Tool: query_mountains with filters           │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 3: Get Conditions + Drive Times           │
│                                                 │
│  For each candidate:                            │
│  - Weather: temp, wind, visibility              │
│  - Snow: depth, fresh 24h                       │
│  - Actual drive time (not just haversine)       │
│                                                 │
│  → Tools: get_conditions, get_drive_time        │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 4: Assess Overall Conditions              │
│                                                 │
│  Before scoring, check: "Is today good?"        │
│  - day_quality: excellent/good/fair/poor        │
│  - best_available: "15in fresh at Stowe"        │
│  - mode: chase_powder/casual/minimize_hassle    │
│                                                 │
│  This sets the FRAMING for recommendations:     │
│  - "chase_powder" → drive further for snow      │
│  - "minimize_hassle" → stay close, all rough    │
│                                                 │
│  → DSPy Module: AssessConditions                │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 5: Score Each Candidate                   │
│                                                 │
│  Base score from:                               │
│  - Fresh snow (biggest factor)                  │
│  - Weather pleasantness                         │
│  - Terrain fit for skill level                  │
│  - Value (price vs conditions)                  │
│  - Drive time penalty                           │
│                                                 │
│  CONTEXTUAL BOOSTS (agent intelligence):        │
│  - Windy? → boost glades (sheltered)            │
│  - Very cold? → boost gondola/bubble lifts      │
│  - Fresh powder? → boost glades (tree skiing)   │
│  - Warm/slushy? → boost north-facing/high elev  │
│                                                 │
│  Output: score + tradeoff_notes for each        │
│  → DSPy Module: ScoreMountain                   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 6: Generate Recommendation                │
│                                                 │
│  Given:                                         │
│  - Overall conditions assessment                │
│  - Scored candidates with tradeoff notes        │
│  - Original query + preferences                 │
│                                                 │
│  Generate nuanced recommendation:               │
│  - "Stowe has 15in fresh, worth the 3hr drive"  │
│  - "Everything's rough today, stay close"       │
│  - "If you can't swing 3hrs, Okemo is okay"     │
│                                                 │
│  → DSPy Module: GenerateRecommendation          │
└─────────────────────────────────────────────────┘
```

### DSPy Modules

```python
class ParseSkiQuery(dspy.Signature):
    """Extract structured constraints from natural language ski query.

    Separates HARD FILTERS (used to exclude mountains from DB) from
    SOFT PREFERENCES (used to score/rank candidates).
    """
    query: str = dspy.InputField()
    user_context: str = dspy.InputField(desc="Current date, location defaults")

    # Hard filters (drive DB query) - flattened from all group members
    target_date: str = dspy.OutputField(desc="YYYY-MM-DD, 'today', or 'tomorrow'")
    max_drive_hours: float = dspy.OutputField(desc="Max drive time, null if not specified")
    pass_type: str = dspy.OutputField(desc="epic/ikon/indy or null")
    needs_terrain_parks: bool = dspy.OutputField(desc="True if anyone wants park")
    needs_glades: bool = dspy.OutputField(desc="True if anyone wants tree skiing")
    needs_beginner_terrain: bool = dspy.OutputField(desc="True if anyone is a beginner")
    needs_expert_terrain: bool = dspy.OutputField(desc="True if anyone wants double blacks")

    # Soft preferences (affect scoring)
    skill_level: str = dspy.OutputField(desc="beginner/intermediate/advanced/expert")
    activity: str = dspy.OutputField(desc="ski/snowboard/either")
    vibe: str = dspy.OutputField(desc="powder_chase/casual/park_day/learning/family_day")


class AssessConditions(dspy.Signature):
    """Assess overall ski conditions before scoring individual mountains.

    Determines if today is worth skiing and sets the recommendation mode.
    """
    all_candidates: str = dspy.InputField(desc="JSON of all candidates with conditions")
    user_preferences: str = dspy.InputField(desc="Parsed preferences from query")

    day_quality: str = dspy.OutputField(desc="excellent/good/fair/poor/stay_home")
    best_available: str = dspy.OutputField(desc="Summary of best option available")
    recommendation_mode: str = dspy.OutputField(desc="chase_powder/enjoy_day/minimize_hassle/postpone")
    mode_reasoning: str = dspy.OutputField(desc="Why this mode was chosen")


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
    tradeoff_note: str = dspy.OutputField(desc="Notable tradeoff, e.g. 'best snow but longest drive'")


class GenerateRecommendation(dspy.Signature):
    """Generate final recommendation with tradeoff analysis.

    Uses day context to frame appropriately (chase powder vs minimize hassle).
    """
    query: str = dspy.InputField(desc="Original user query")
    day_assessment: str = dspy.InputField(desc="Overall conditions and mode")
    scored_candidates: str = dspy.InputField(desc="Mountains with scores and tradeoffs")

    top_pick: str = dspy.OutputField(desc="Primary recommendation with reasoning")
    alternatives: str = dspy.OutputField(desc="1-2 alternatives with tradeoff explanation")
    caveat: str = dspy.OutputField(desc="Any important caveat, e.g. 'but tomorrow looks better'")
```

### Prefilter Logic

Hard filters extracted from query that drive the DB query:

| User Says | Filter Applied |
|-----------|----------------|
| "terrain park" | `terrain_parks IS NOT NULL` |
| "glades" / "trees" | `glades IS NOT NULL` |
| "double blacks" / "expert" | `double_black_pct > 0` |
| "black diamonds" / "advanced" | `black_pct > 0` |
| "Ikon pass" | `pass_types LIKE '%ikon%'` |
| "snowboard" | `allows_snowboarding = TRUE` |
| "night skiing" | `has_night_skiing = TRUE` |
| "2 hours max" | `haversine_distance < 240km` |

### Contextual Scoring Boosts

Conditions-based adjustments the agent applies during scoring:

| Condition | Boost |
|-----------|-------|
| High wind (>30 km/h) | Mountains with glades (sheltered) |
| Very cold (<-10°C) | Mountains with gondola/bubble lifts |
| Fresh powder (>15cm) | Mountains with glades (tree skiing) |
| Warm (>0°C) | Higher elevation mountains (better snow) |
| Poor visibility | Mountains with tree runs (easier navigation) |
| Low natural snow | Mountains with high snowmaking % |

### Snowmaking

Critical for Northeast skiing where natural snow is unreliable.

- Add `snowmaking_pct` to schema (0-100, % of terrain with coverage)
- Early season / thin base → boost mountains with good snowmaking
- "Only 2" natural but 90% snowmaking" → still skiable
- Some mountains (e.g., Killington) are known for aggressive snowmaking

### Crowd Calendar

Holidays and school vacation weeks massively impact experience.

**Peak Periods:**
| Period | Dates (approx) | Crowd Level |
|--------|----------------|-------------|
| Christmas-New Year's | Dec 24 - Jan 2 | Extreme |
| MLK Weekend | 3rd Monday of Jan | High |
| MA/NH February Vacation | ~Feb 15-22 | Extreme |
| NY February Vacation | ~Feb 20-27 | Extreme |
| Presidents Day Weekend | 3rd Monday of Feb | High |

**Regional Crowd Logic:**

Vermont mountains (Stowe, Killington, Okemo) get hammered by both NY and Boston crowds.

Maine mountains (Sunday River, Sugarloaf) are:
- Further from NYC → less affected by NY vacation week
- Still busy during MA/NH vacation but more manageable
- Good "escape the crowds" recommendation during NY break

**Implementation:**

```python
def get_crowd_context(target_date: date, mountain_state: str) -> dict:
    """Assess expected crowds for a date + location."""
    return {
        "is_holiday_weekend": bool,
        "vacation_week": "MA/NH" | "NY" | None,
        "crowd_level": "extreme" | "high" | "moderate" | "normal",
        "crowd_note": str,  # e.g., "NY vacation week - VT will be packed, consider Maine"
    }
```

**Scoring Impact:**
- Holiday/vacation week → penalize high-traffic mountains
- NY vacation + Maine mountain → less penalty (crowds go to VT)
- Weekday during vacation week → still busy but better than weekend

**Recommendation Framing:**
- "Heads up, it's February break - expect crowds everywhere"
- "It's NY vacation week - Maine will be less swamped than Vermont"
- "Consider going Thursday instead of Saturday"

### Snow Quality Inference

**Problem:** Open-Meteo gives weather/snowfall but not actual surface conditions (icy, groomed, etc.)

**Placeholder:** Eventually integrate with a snow report API or scraper. For now, infer from weather patterns:

```python
def infer_snow_quality(recent_weather: list[dict]) -> dict:
    """Infer snow quality from weather patterns."""
    # Patterns to detect:
    # - Rain → freeze overnight = likely icy
    # - Fresh snow + stayed cold = powder
    # - No precip + cold + wind = hardpack/wind-affected
    # - Warm afternoon (>35°F) = slushy/spring conditions
    # - Prolonged cold, no new snow = machine groomed, firm
    return {
        "inferred_quality": "powder" | "packed_powder" | "groomed" | "hardpack" | "icy" | "spring",
        "confidence": "high" | "medium" | "low",
        "reasoning": str,
    }
```

**Scoring Impact:**

| Pattern | Inferred Quality | Score Adjustment |
|---------|------------------|------------------|
| Fresh snow, stayed cold | Powder | +20 |
| No precip, cold, groomed terrain | Packed powder | +5 |
| Rain → freeze overnight | Likely icy | -15 |
| Warm (>35°F) afternoon | Slushy/spring | -5 |
| High wind + no trees | Wind-affected | -10 |

**Recommendation Note:** "Based on weather patterns - check the mountain's snow report for current conditions"

### Family/Group Queries

Support queries where different group members have different needs.

**Example:** "Looking for somewhere I can take my older daughter on blues and easy glades while my wife teaches our younger daughter for the first time"

**Parsed to flattened filters:**
```python
needs_glades=True           # older daughter wants tree skiing
needs_beginner_terrain=True # younger daughter is first-timer
# vibe="family_day"
```

**Schema Fields for Family Support:**
- `has_magic_carpet` - Essential for true beginners
- `has_ski_school` - Lessons available on-site
- `learning_area_quality` - "excellent", "good", "basic"

**Scoring Boosts:**
- Dedicated learning area separated from main traffic
- Known family-friendly reputation (Smugglers' Notch, Bretton Woods, Okemo)

---

## Data Sources

### 1. Mountain Database (SQLite)

**Challenge:** No single free/public source with comprehensive metadata.

**Approach:**
- Use Skimap.org to get mountain names and coordinates as a starting point
- Manually enrich with metadata for initial dataset (focus on one region)
- Store in local SQLite database

**Schema:**

```sql
CREATE TABLE mountains (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE,

    -- Location
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    state TEXT,
    region TEXT,  -- e.g., "Colorado Front Range", "Vermont", "Tahoe"

    -- Elevation (feet)
    base_elevation INTEGER,
    summit_elevation INTEGER,
    vertical_drop INTEGER,

    -- Basic info
    allows_snowboarding BOOLEAN DEFAULT TRUE,

    -- Pass types (comma-separated or JSON)
    pass_types TEXT,  -- e.g., "epic,indy" or '["epic", "indy"]'

    -- Terrain breakdown
    num_trails INTEGER,
    num_lifts INTEGER,
    green_pct INTEGER,   -- Percentage beginner terrain
    blue_pct INTEGER,    -- Percentage intermediate
    black_pct INTEGER,   -- Percentage advanced
    double_black_pct INTEGER,  -- Percentage expert

    -- Terrain features
    terrain_parks TEXT,      -- comma-separated: "easy,intermediate,hard,superpipe"
    glades TEXT,             -- comma-separated: "easy,intermediate,hard"
    bowls_count INTEGER DEFAULT 0,

    -- Lift types (for cold day recommendations)
    lift_types TEXT,         -- comma-separated: "gondola,bubble,highspeed,fixed,tram"

    -- Snowmaking (critical for Northeast)
    snowmaking_pct INTEGER,  -- 0-100, % of terrain with coverage

    -- Beginner/Family facilities
    has_magic_carpet BOOLEAN DEFAULT FALSE,
    has_ski_school BOOLEAN DEFAULT TRUE,
    learning_area_quality TEXT,  -- "excellent", "good", "basic"

    -- Logistics
    avg_weekday_price INTEGER,   -- USD
    avg_weekend_price INTEGER,   -- USD
    has_night_skiing BOOLEAN DEFAULT FALSE,

    -- Links
    website TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for geo queries
CREATE INDEX idx_mountains_coords ON mountains(lat, lon);
CREATE INDEX idx_mountains_region ON mountains(region);
```

### 2. Weather & Snow Data - Open-Meteo (Free)

**Endpoints:**
- Forecast: `https://api.open-meteo.com/v1/forecast`
- Historical: `https://archive-api.open-meteo.com/v1/archive`

**Relevant parameters:**
- `snow_depth` - Current snow depth (cm)
- `snowfall` - Snowfall in time period (cm)
- `temperature_2m` - Temperature at 2m
- `wind_speed_10m` - Wind speed
- `visibility` - Visibility (meters)
- `weather_code` - WMO weather codes

**Example request (Killington, VT):**
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=43.6045
  &longitude=-72.8201
  &daily=snowfall_sum,snow_depth
  &hourly=temperature_2m,wind_speed_10m,visibility,weather_code
  &timezone=America/New_York
```

**Historical data for backtesting:**
```
GET https://archive-api.open-meteo.com/v1/archive
  ?latitude=43.6045
  &longitude=-72.8201
  &start_date=2024-01-01
  &end_date=2024-03-31
  &daily=snowfall_sum,snow_depth
```

### 3. Distance/Routing - OpenRouteService (Free tier)

**Endpoint:** `https://api.openrouteservice.org/v2/directions/driving-car`

**Rate limits:** 2000 requests/day on free tier (plenty for POC)

**Usage:**
1. Use haversine for initial filtering (fast, no API calls)
2. Use OpenRouteService for actual drive times on top ~10 candidates

### 4. Lift Status - Liftie (Optional, Free)

**Endpoint:** `https://liftie.info/api/resort/{resort_slug}`

Returns current lift status for ~100 North American resorts.

---

## Tools (Agent Capabilities)

The agent will have access to these tools:

| Tool | Type | Description |
|------|------|-------------|
| `search_mountains` | DB Query | Filter by distance, pass, features, difficulty |
| `get_conditions` | API Call | Fetch weather + snow from Open-Meteo |
| `get_drive_time` | API Call | Get actual drive duration from OpenRouteService |

### search_mountains

Prefilters mountains based on parsed query constraints:

```python
def search_mountains(
    max_drive_hours: float = 3.0,
    user_lat: float = 42.3601,
    user_lon: float = -71.0589,
    # Hard filters
    pass_type: str | None = None,           # epic/ikon/indy
    has_terrain_parks: bool | None = None,
    has_glades: bool | None = None,
    has_night_skiing: bool | None = None,
    min_black_pct: int | None = None,       # for "black diamonds"
    min_double_black_pct: int | None = None, # for "expert terrain"
    allows_snowboarding: bool | None = None,
) -> str:
    """Return JSON of mountains matching all filters."""
```

### get_conditions

Fetches weather and snow data for a single mountain:

```python
def get_conditions(lat: float, lon: float, target_date: str) -> str:
    """Return JSON with temp, wind, visibility, snow depth, fresh snow."""
```

### get_drive_time

Gets actual driving time (not haversine estimate):

```python
def get_drive_time(start_lat, start_lon, end_lat, end_lon) -> str:
    """Return JSON with duration_minutes, distance_km, distance_mi."""
```

---

## Evaluation Strategy

### Ground Truth Dataset

Build labeled examples of `(query, conditions, correct_recommendation)`:

```python
{
    "id": "001",
    "query": "Best powder day within 3hrs of Boston, I have Ikon pass",
    "query_date": "2024-02-15",
    "user_location": {"lat": 42.3601, "lon": -71.0589},  # Boston
    "conditions_snapshot": {
        "killington": {"snow_depth": 80, "24hr_snow": 20, ...},
        "stowe": {"snow_depth": 90, "24hr_snow": 8, ...},
        "sugarbush": {"snow_depth": 75, "24hr_snow": 25, ...},
        ...
    },
    "ground_truth": {
        "top_pick": "Sugarbush",
        "acceptable": ["Sugarbush", "Killington"],  # Any of these valid
        "reasoning": "10 inches fresh overnight, Ikon pass accepted, 3hr drive"
    }
}
```

**Sources for ground truth:**
- Personal knowledge of past ski days
- Reddit r/skiing and r/snowboarding trip reports
- Reconstruct from historical weather data

### Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Hit@1** | Top recommendation matches ground truth | > 60% |
| **Hit@3** | Ground truth in top 3 recommendations | > 85% |
| **Constraint Satisfaction** | Recommendations meet all stated constraints | 100% |
| **Snow Ranking Correlation** | Correlation between our ranking and actual snow | > 0.7 |
| **Reasoning Accuracy** | Facts stated in reasoning are correct | > 95% |

### Backtesting Framework

```python
def backtest(agent, eval_set):
    """Run agent against historical conditions."""
    results = []

    for example in eval_set:
        # Mock APIs to return historical data
        with mock_conditions(example["conditions_snapshot"]):
            prediction = agent.run(example["query"])

        results.append({
            "id": example["id"],
            "predicted": prediction.top_pick,
            "ground_truth": example["ground_truth"]["top_pick"],
            "hit_at_1": prediction.top_pick == example["ground_truth"]["top_pick"],
            "hit_at_3": example["ground_truth"]["top_pick"] in prediction.top_3,
            "constraints_met": check_constraints(prediction, example),
        })

    return {
        "hit_at_1": mean([r["hit_at_1"] for r in results]),
        "hit_at_3": mean([r["hit_at_3"] for r in results]),
        "constraint_satisfaction": mean([r["constraints_met"] for r in results]),
        "details": results
    }
```

### Error Analysis Categories

1. **Data Errors** - Stale/incorrect conditions data
2. **Parsing Errors** - Misunderstood user query
3. **Scoring Errors** - Had right data, wrong ranking
4. **Constraint Violations** - Ignored stated requirements
5. **Preference Mismatch** - Technically valid but poor UX

---

## Project Structure

```
powder/
├── README.md
├── PLAN.md
├── pyproject.toml
│
├── powder/
│   ├── __init__.py
│   ├── agent.py              # Main DSPy agent
│   ├── signatures.py         # DSPy signatures
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── database.py       # Mountain DB queries
│   │   ├── weather.py        # Open-Meteo client
│   │   ├── routing.py        # OpenRouteService client
│   │   └── scoring.py        # Scoring function
│   │
│   ├── data/
│   │   ├── mountains.db      # SQLite database
│   │   └── seed_mountains.py # Script to populate DB
│   │
│   └── eval/
│       ├── __init__.py
│       ├── dataset.py        # Evaluation dataset
│       ├── metrics.py        # Metric calculations
│       └── backtest.py       # Backtesting framework
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_agent_development.ipynb
│   └── 03_evaluation.ipynb
│
├── tests/
│   └── ...
│
└── data/
    ├── eval_set.json         # Labeled evaluation examples
    └── conditions_cache/     # Cached historical conditions
```

---

## Implementation Phases

### Phase 1: Data Foundation
- [ ] Create SQLite database with schema
- [ ] Seed database with 20-30 mountains (pick one region)
- [ ] Implement Open-Meteo client
- [ ] Implement OpenRouteService client
- [ ] Test haversine filtering

### Phase 2: Agent Core
- [ ] Define DSPy signatures
- [ ] Implement tools as DSPy-compatible functions
- [ ] Wire up agent pipeline
- [ ] Get basic end-to-end query working

### Phase 3: Evaluation
- [ ] Build evaluation dataset (20-30 examples)
- [ ] Implement metrics (Hit@1, Hit@3, constraint satisfaction)
- [ ] Build backtesting harness
- [ ] Run initial evaluation

### Phase 4: Iteration & Polish
- [ ] Error analysis on failures
- [ ] DSPy optimization with eval set
- [ ] Clean up for demo
- [ ] Write README with setup instructions

---

## Open Questions

- [x] Which region to focus on for v1? **Northeast US** (VT, NH, ME, NY, MA)
- [ ] How to handle mountains without coordinates in source data?
- [ ] Should Liftie integration be included in v1?
- [ ] How many eval examples needed for meaningful metrics?

---

## References

- [Open-Meteo API Docs](https://open-meteo.com/en/docs)
- [OpenRouteService API Docs](https://openrouteservice.org/dev/#/api-docs)
- [Liftie API](https://liftie.info/)
- [DSPy Documentation](https://dspy-docs.vercel.app/)
- [Skimap.org](https://skimap.org/)
