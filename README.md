# Powder

An AI agent that answers: **"Where should I ski/snowboard today?"**

Given a natural language query, Powder recommends the best mountain based on current conditions, your location, pass type, and preferences.

## Setup

```bash
make          # Create venv and install dependencies
make test     # Run tests
make run      # Run the agent
```

Requires [uv](https://github.com/astral-sh/uv) for package management.

## Stack

- **DSPy** - Agent framework
- **Open-Meteo** - Weather/snow data (free, no API key)
- **OpenRouteService** - Drive time calculations
- **SQLite** - Mountain database
