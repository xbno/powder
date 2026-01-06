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
```

## Stack

- **DSPy** - Agent framework
- **Open-Meteo** - Weather/snow data (free, no API key)
- **OpenRouteService** - Drive time calculations
- **SQLite** - Mountain database
