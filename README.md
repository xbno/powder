# Powder

An AI agent that answers: **"Where should I ski/snowboard today?"**

Given a natural language query, Powder recommends the best mountain based on current conditions, your location, pass type, and preferences.

## Setup

```bash
make          # Create venv and install dependencies
make seed-db  # Create the mountain database
make test     # Run tests
make run      # Run the agent
```

Requires [uv](https://github.com/astral-sh/uv) for package management.

[Request an API key here](https://api.openrouteservice.org/) for OpenRouteService, then add to `.env`:

```bash
OPEN_ROUTE_SERVICE_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
# Run with a query
.venv/bin/python -m powder.run "Where should I ski tomorrow? I have an Ikon pass."

# Run with default query
.venv/bin/python -m powder.run

# Use a different model
.venv/bin/python -m powder.run "Best powder day?" --model anthropic/claude-sonnet-4-20250514
```

Run tests:

```bash
# Run all non-LLM tests (fast, no API key needed)
.venv/bin/python -m pytest -m "not llm"

# Run LLM tests (requires ANTHROPIC_API_KEY)
.venv/bin/python -m pytest -m llm -v -s
```

## Stack

- **DSPy** - Agent framework
- **Open-Meteo** - Weather/snow data (free, no API key)
- **OpenRouteService** - Drive time calculations
- **SQLite** - Mountain database
