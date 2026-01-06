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
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 1: Parse & Enrich Query                   │
│  - Extract: location, date, skill, pass type    │
│  - Geocode user location if needed              │
│  - Identify constraints (max drive, snowboard)  │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 2: Filter Mountains from DB               │
│  - Haversine filter for approximate radius      │
│  - Filter: snowboard-friendly, pass type, etc.  │
│  → Tool: SQLite query                           │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 3: Get Conditions for Candidates          │
│  - Weather forecast (temp, wind, visibility)    │
│  - Snow depth and recent snowfall               │
│  - (Optional) Lift status via Liftie            │
│  → Tool: Open-Meteo API                         │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 4: Calculate Drive Times                  │
│  - Get actual drive time for top candidates     │
│  → Tool: OpenRouteService API                   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 5: Score & Rank                           │
│  - Composite score with weighted factors        │
│  - Fresh snow, weather, terrain fit, logistics  │
│  → Tool: Python scoring function                │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STEP 6: Generate Recommendation                │
│  - Top 1-3 picks with explanations              │
│  - Tradeoff analysis                            │
└─────────────────────────────────────────────────┘
```

### DSPy Modules

```python
class ParseSkiQuery(dspy.Signature):
    """Extract structured parameters from natural language ski query."""
    query: str = dspy.InputField()
    location: str = dspy.OutputField(desc="User's starting location")
    target_date: str = dspy.OutputField(desc="Date or date range")
    max_drive_hours: float = dspy.OutputField()
    skill_level: str = dspy.OutputField(desc="beginner/intermediate/advanced/expert")
    pass_type: str = dspy.OutputField(desc="epic/ikon/indy/none")
    activity: str = dspy.OutputField(desc="ski or snowboard")
    preferences: str = dspy.OutputField(desc="Any other stated preferences")

class RankMountains(dspy.Signature):
    """Rank candidate mountains given conditions and user preferences."""
    candidates: str = dspy.InputField(desc="JSON of mountains with conditions")
    user_preferences: str = dspy.InputField()
    rankings: str = dspy.OutputField(desc="Ordered list with scores and reasoning")

class GenerateRecommendation(dspy.Signature):
    """Generate final recommendation with explanation."""
    top_picks: str = dspy.InputField()
    user_query: str = dspy.InputField()
    recommendation: str = dspy.OutputField(desc="Natural language recommendation")
```

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
    terrain_parks INTEGER DEFAULT 0,
    glades_count INTEGER DEFAULT 0,
    bowls_count INTEGER DEFAULT 0,

    -- Lift types (for cold day recommendations)
    has_gondola BOOLEAN DEFAULT FALSE,
    has_heated_chairlift BOOLEAN DEFAULT FALSE,  -- bubble chairs

    -- Logistics
    avg_weekend_ticket_price INTEGER,  -- USD
    night_skiing BOOLEAN DEFAULT FALSE,

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
| `query_mountains` | DB Query | Filter mountains by location, pass type, terrain |
| `get_weather_forecast` | API Call | Fetch Open-Meteo forecast for coordinates |
| `get_snow_conditions` | API Call | Fetch snow depth/snowfall from Open-Meteo |
| `calculate_drive_time` | API Call | Get drive duration from OpenRouteService |
| `score_mountain` | Python Function | Compute composite score from all factors |

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
