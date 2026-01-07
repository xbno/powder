# Add Mountain

Add $ARGUMENTS[1] ski mountain to the database.

## Instructions

When the user invokes this skill, do the following for the mountain provided $ARGUMENTS[1].

1. **Search for mountain data** - Use web search to find basic info about the mountain:
   - Location (lat/lon, state)
   - Vertical drop
   - Number of trails and lifts
   - Terrain breakdown (green/blue/black/double black percentages)
   - Pass types (epic, ikon, indy)
   - Terrain parks and glades availability
   - Lift types (gondola, highspeed, fixed, bubble, tram)
   - Night skiing availability
   - Ticket prices (weekday/weekend)
   - Snowmaking percentage
   - Beginner facilities (magic carpet, ski school, learning area quality)

2. **Fill in the mountain json** - Print out the json for the mountain for review and to pass to the validation below

3. **Validate the json** - Use `.venv/bin/python -m powder.tools.validate_mountain '{"name": "...", "state": "VT", ...}'` to confirm valid

4. **Append to JSONL** - Add the mountain to `powder/data/mountains.jsonl` as a single JSON line

5. **Reseed database** - Run `make seed-db` to update the database

## Required Fields

```json
{
  "name": "Mountain Name",
  "state": "VT",
  "lat": 43.123,
  "lon": -72.456,
  "vertical_drop": 2000,
  "num_trails": 100,
  "num_lifts": 10,
  "green_pct": 20,
  "blue_pct": 40,
  "black_pct": 30,
  "double_black_pct": 10,
  "terrain_parks": "easy,intermediate,hard",
  "glades": "intermediate,hard",
  "pass_types": "epic",
  "allows_snowboarding": true,
  "lift_types": "gondola,highspeed,fixed",
  "has_night_skiing": false,
  "avg_weekday_price": 120,
  "avg_weekend_price": 150,
  "snowmaking_pct": 80,
  "has_magic_carpet": true,
  "has_ski_school": true,
  "learning_area_quality": "good"
}
```

## Validation

Before appending to the JSONL file, validate the data using:

```bash
python -m powder.tools.validate_mountain '{"name": "...", "state": "VT", ...}'
```

This validates:
- Required fields (name, state, lat, lon)
- State is one of: VT, NH, ME, MA, NY, CT, RI
- Coordinates are within valid ranges
- Percentages are 0-100 and terrain percentages sum to ~100
- Pass types, terrain parks, glades, lift types are valid values
- Learning area quality is: excellent, good, or basic

## Notes

- `terrain_parks` and `glades` can be null if not available
- `pass_types` can be comma-separated: "epic,ikon" or "indy"
- `lift_types` options: gondola, bubble, highspeed, fixed, tram
- `learning_area_quality` options: excellent, good, basic
