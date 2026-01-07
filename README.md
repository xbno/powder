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

13 Northeast US mountains with full metadata:

- **Vermont**: Stowe, Killington, Sugarbush, Jay Peak, Okemo, Mount Snow, Stratton, Mad River Glen, Smugglers' Notch
- **New Hampshire**: Waterville Valley, Gunstock, Attitash, Bretton Woods
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

Add API keys to `.env`:

```bash
ANTHROPIC_API_KEY=your_key_here
OPEN_ROUTE_SERVICE_API_KEY=your_key_here  # Get free key at https://openrouteservice.org
```

## Usage

```bash
# Run with a query
.venv/bin/python -m powder.run "Where should I ski tomorrow? I have an Ikon pass."

# Use pipeline mode (default, recommended)
.venv/bin/python -m powder.run "Best powder within 3 hours?" --mode pipeline

# Use ReAct mode
.venv/bin/python -m powder.run "Best powder?" --mode react

# Different model
.venv/bin/python -m powder.run "Best terrain park?" --model anthropic/claude-sonnet-4-20250514
```

## Evaluation

The evaluation framework measures agent performance with **deterministic metrics** (no LLM-as-judge):

### Metrics

| Metric | Description |
|--------|-------------|
| **Hit@1** | Top recommendation matches expected mountain |
| **Hit@3** | Expected mountain appears in top 3 |
| **Constraint Satisfaction** | Respects pass type, drive time, terrain requirements |
| **Parse Accuracy** | Correctly extracts filters from natural language |
| **Grounding** | Reasoning mentions actual mountain data |

### Dataset

39 labeled examples across 4 signatures:

- `ParseSkiQuery` - 12 examples (query → structured filters)
- `AssessConditions` - 4 examples (conditions → day quality)
- `ScoreMountain` - 8 examples (mountain + prefs → score)
- `GenerateRecommendation` - 7 examples (scored list → final pick)
- End-to-end pipeline - 12 examples with full ground truth

### Running Evals

```bash
make eval           # Run full evaluation suite
make eval-verbose   # Show detailed output for failures

# With specific model
.venv/bin/python -m powder.evals.runner --model anthropic/claude-sonnet-4-20250514
```

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
├── run.py              # CLI entry point
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
└── evals/
    ├── runner.py       # Evaluation runner
    ├── parse_query.py  # ParseSkiQuery eval
    ├── assess_conditions.py
    ├── score_mountain.py
    ├── generate_recommendation.py
    └── end_to_end.py   # Full pipeline eval
```

## Stack

- **DSPy** - Agent framework with signatures and optimizers
- **Open-Meteo** - Weather/snow data (free, no API key)
- **OpenRouteService** - Drive time calculations (free tier)
- **SQLite + SQLAlchemy** - Mountain database
