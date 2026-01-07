# Powder

An AI agent that answers: **"Where should I ski/snowboard today?"**

Given a natural language query, Powder recommends the best Northeast US mountain based on current conditions, your location, pass type, and preferences.

## Features

### Query Understanding

The agent parses natural language queries to extract:

| Filter Type | Examples |
|-------------|----------|
| **Pass type** | "I have an Ikon pass", "Epic pass holder" |
| **Drive time** | "within 2 hours", "max 3 hour drive" |
| **Terrain parks** | "looking for a good park", "rails and jumps" |
| **Glades/trees** | "tree skiing", "want to ski glades" |
| **Beginner terrain** | "teaching my kid", "first time skiing" |
| **Expert terrain** | "double blacks", "steep chutes" |
| **Night skiing** | "after work", "night skiing tonight" |
| **Skill level** | "intermediate snowboarder", "expert skier" |

### Mountains Covered

21+ Northeast US mountains with full metadata:

- **Vermont**: Stowe, Killington, Sugarbush, Jay Peak, Okemo, Mount Snow, Stratton, Mad River Glen, Smugglers' Notch
- **New Hampshire**: Waterville Valley, Gunstock, Attitash, Bretton Woods, Cannon Mountain, Cranmore, Loon Mountain, Mount Sunapee, Wildcat Mountain
- **Maine**: Saddleback, Sugarloaf
- **Massachusetts**: Nashoba Valley

Each mountain includes: coordinates, vertical drop, trail counts, terrain percentages, terrain parks, glades, pass types (Epic/Ikon/Indy), lift types, snowmaking %, learning facilities, pricing.

### Conditions & Context

- **Weather**: Temperature, wind, visibility from Open-Meteo (free API)
- **Snow**: Fresh snowfall (24h), snow depth
- **Drive times**: Actual routing via OpenRouteService
- **Crowds**: Holiday/vacation week detection (Christmas, MLK, February break)

### Architecture

Two agent implementations:

1. **Pipeline** (default) - Explicit 7-step flow with intermediate outputs:
   ```
   Parse Query → Search DB → Get Conditions → Get Drive Times
   → Assess Day Quality → Score Mountains → Generate Recommendation
   ```

2. **ReAct** - Flexible tool-using agent that decides its own steps

## Setup

```bash
make          # Create venv and install dependencies
make seed-db  # Populate the mountain database
make test     # Run tests (fast, no API calls)
```

Requires [uv](https://github.com/astral-sh/uv) for package management.

### Adding More Mountains

Use the seed script to add mountains from the predefined list via Claude:

```bash
# List mountains not yet in the database
python scripts/seed_missing_mountains.py

# Add N mountains using Claude to research and populate data
python scripts/seed_missing_mountains.py --run --num 10

# After adding mountains, re-fetch historic weather data
make fetch-historic
```

Add API keys to `.env`:

```bash
ANTHROPIC_API_KEY=your_key_here
OPEN_ROUTE_SERVICE_API_KEY=your_key_here  # Get free key at https://openrouteservice.org
```

## Usage

```bash
# Run with a query (uses ReAct agent by default)
python -m powder "Where should I ski tomorrow? I have an Ikon pass."

# Use Pipeline instead of ReAct
python -m powder --pipeline "Best powder within 3 hours?"

# Run on historic data (uses fixtures instead of live weather API)
python -m powder --date 2025-02-17 "Best powder day with Ikon pass?"

# Different starting location
python -m powder --location nyc "Epic pass, best terrain?"

# Interactive mode
python -m powder
```

### Historic Sanity Checks

Test the agent on known good/bad days from the 2024-2025 season:

**Powder Days (clear winners):**
| Date | Scenario | Expected | Command |
|------|----------|----------|---------|
| 2025-02-17 | Big dump | Sugarloaf (5.7") | `python -m powder --date 2025-02-17 "Best powder with Ikon?"` |
| 2025-03-29 | Late season storm | Stowe (5.5") | `python -m powder --date 2025-03-29 "Epic pass powder?"` |

**Skip Days (bad conditions):**
| Date | Scenario | Conditions | Command |
|------|----------|------------|---------|
| 2025-01-08 | Brutal cold | -8°F, 0.4" avg | `python -m powder --date 2025-01-08 "Worth skiing today?"` |
| 2024-12-22 | Pre-Xmas ice | -7°F, no fresh | `python -m powder --date 2024-12-22 "Ikon pass today?"` |
| 2025-03-31 | Spring slush | 54°F avg, 69°F max | `python -m powder --date 2025-03-31 "Should I ski today?"` |

**Beautiful Days (multiple good options):**
| Date | Scenario | Conditions | Command |
|------|----------|------------|---------|
| 2025-01-29 | Warm refresh | 1-2" everywhere, 25°F | `python -m powder --date 2025-01-29 "Best skiing today?"` |
| 2025-02-03 | Tie-breaker | 1" avg, pleasant | `python -m powder --date 2025-02-03 "Where should I go?"` |

These dates have known conditions - useful for validating agent behavior on different scenarios.

## Evaluation

The evaluation framework measures agent performance with **deterministic metrics** (no LLM-as-judge).

### Current Results (GEPA-Optimized)

| Metric | Pipeline | ReAct |
|--------|----------|-------|
| **Hit@1** | 66.7% | **75.0%** |
| **Hit@3** | 75.0% | **91.7%** |
| **Constraint Satisfaction** | **92.3%** | 0.0%* |

*ReAct constraint metric is a measurement artifact (can't parse constraints from unstructured text).

ReAct improved from 50% → 75% Hit@1 after GEPA optimization with `enable_tool_optimization=True`.

### Metrics

| Metric | Description |
|--------|-------------|
| **Hit@1** | Top recommendation matches expected mountain |
| **Hit@3** | Expected mountain appears in top 3 |
| **Constraint Satisfaction** | Respects pass type, drive time, terrain requirements |
| **Parse Accuracy** | Correctly extracts filters from natural language |

### Dataset

39 labeled examples across 4 signatures + 12 end-to-end:

- `ParseSkiQuery` - 12 examples (97.4% accuracy)
- `AssessConditions` - 4 examples (100% after GEPA)
- `ScoreMountain` - 8 examples (96.3% after GEPA)
- `GenerateRecommendation` - 7 examples (100% accuracy)
- End-to-end - 12 examples with full ground truth

### Running Evals

```bash
make eval           # Run full evaluation suite
make eval-verbose   # Show detailed output for failures

# Run specific mode
python -m powder.evals.runner --mode react
python -m powder.evals.runner --mode pipeline
python -m powder.evals.runner --mode both
```

### GEPA Optimization

Optimize signatures with GEPA (Reflective Prompt Evolution):

```bash
# Optimize individual signatures
python -m powder.evals.optimize --signature score_mountain --max-calls 50
python -m powder.evals.optimize --signature assess_conditions --max-calls 50

# Optimize ReAct with tool descriptions
python -m powder.evals.optimize --signature react --max-calls 30
```

Optimized prompts are saved to `powder/optimized/` and automatically loaded by the pipeline.

### Historic Weather Data (Backtesting)

Fetch real weather data from the 2024-2025 ski season for reproducible backtesting:

```bash
# Fetch full season (Dec 1 - Apr 15, all mountains × 136 days)
make fetch-historic

# Fetch specific date range
.venv/bin/python -m powder.evals.fetch_historic --start 2025-01-01 --end 2025-01-31

# View summary of fetched data (best powder days, coldest days, etc.)
make backtest-summary
```

This creates fixtures in `powder/evals/fixtures/` that can be used for:
- Creating eval examples from real historic conditions
- Reproducible backtesting without API calls
- Analyzing which days the agent would have recommended correctly

## Testing

```bash
make test       # Fast tests (no API calls)
make test-llm   # LLM tests (requires ANTHROPIC_API_KEY)
make test-all   # All tests
make test-cov   # With coverage report
```

## Project Structure

```
powder/
├── __main__.py         # CLI entry point (python -m powder)
├── pipeline.py         # Explicit multi-step pipeline
├── agent.py            # ReAct-based agent
├── signatures.py       # DSPy signatures
├── tools/
│   ├── database.py     # Mountain DB queries
│   ├── weather.py      # Open-Meteo client
│   ├── routing.py      # Drive time calculations
│   └── crowds.py       # Holiday/vacation detection
├── data/
│   ├── mountains.jsonl # Mountain metadata
│   └── mountains.db    # SQLite database
├── optimized/          # GEPA-optimized prompts (auto-loaded)
│   ├── parse_query.json
│   ├── score_mountain.json
│   ├── assess_conditions.json
│   └── react_agent.json
└── evals/
    ├── runner.py       # Evaluation runner
    ├── optimize.py     # GEPA optimization script
    ├── backtest.py     # Historic data backtesting
    ├── find_interesting_days.py
    └── fixtures/       # Historic weather data (136 days)
```

## Stack

- **DSPy** - Agent framework with signatures and optimizers
- **Open-Meteo** - Weather/snow data (free, no API key)
- **OpenRouteService** - Drive time calculations (free tier)
- **SQLite + SQLAlchemy** - Mountain database
