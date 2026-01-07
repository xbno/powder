"""Explicit multi-step ski recommendation pipeline using DSPy signatures."""

import json
import dspy
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from powder.signatures import (
    ParseSkiQuery,
    ParsedQuery,
    AssessConditions,
    ScoreMountain,
    GenerateRecommendation,
)
from powder.tools.database import get_engine, query_mountains
from powder.tools.weather import get_conditions
from powder.tools.routing import get_drive_time, estimate_max_distance_km
from powder.tools.crowds import get_crowd_context


class SkiPipeline(dspy.Module):
    """
    Explicit multi-step pipeline for ski recommendations.

    Unlike ReAct, this runs a deterministic sequence:
    1. Parse query -> structured filters + preferences
    2. Search DB with filters -> candidate mountains
    3. Fetch conditions for each candidate
    4. Assess overall day quality
    5. Score each mountain
    6. Generate final recommendation

    Benefits:
    - Predictable execution order
    - Each signature can be optimized independently with GEPA
    - Easier debugging and evaluation
    """

    def __init__(self, db_path: Path | None = None):
        super().__init__()

        # Initialize predictors for each signature
        self.parse_query = dspy.Predict(ParseSkiQuery)
        self.assess_conditions = dspy.Predict(AssessConditions)
        self.score_mountain = dspy.Predict(ScoreMountain)
        self.generate_recommendation = dspy.Predict(GenerateRecommendation)

        # Database path
        self.db_path = db_path or Path(__file__).parent / "data" / "mountains.db"

    def _resolve_date(self, target_date: str, current_date: date) -> date:
        """Resolve target_date string to actual date."""
        if target_date == "today":
            return current_date
        elif target_date == "tomorrow":
            return current_date + timedelta(days=1)
        elif target_date == "unspecified":
            return current_date  # Default to today
        else:
            try:
                return date.fromisoformat(target_date)
            except ValueError:
                return current_date

    def _search_mountains(
        self,
        parsed: ParsedQuery,
        user_lat: float,
        user_lon: float,
    ) -> list[dict]:
        """Search database for candidate mountains based on parsed filters."""
        max_drive_hours = parsed.max_drive_hours or 3.0
        max_distance_km = estimate_max_distance_km(max_drive_hours)

        engine = get_engine(self.db_path)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Pydantic validators already coerce 'null' -> None
            results = query_mountains(
                session,
                lat=user_lat,
                lon=user_lon,
                max_distance_km=max_distance_km,
                pass_type=parsed.pass_type,
                needs_terrain_parks=parsed.needs_terrain_parks or None,
                needs_glades=parsed.needs_glades or None,
                needs_night_skiing=parsed.needs_night_skiing or None,
                needs_beginner_terrain=parsed.needs_beginner_terrain or None,
                needs_expert_terrain=parsed.needs_expert_terrain or None,
            )
            return results
        finally:
            session.close()

    def _enrich_with_conditions(
        self,
        candidates: list[dict],
        target_date: date,
    ) -> list[dict]:
        """Add weather conditions to each candidate."""
        enriched = []
        for mountain in candidates:
            conditions = get_conditions(mountain["lat"], mountain["lon"], target_date)
            enriched.append({**mountain, "conditions": conditions})
        return enriched

    def _enrich_with_drive_times(
        self,
        candidates: list[dict],
        user_lat: float,
        user_lon: float,
    ) -> list[dict]:
        """Add actual drive times to each candidate."""
        enriched = []
        for mountain in candidates:
            try:
                drive_info = get_drive_time(
                    user_lat, user_lon, mountain["lat"], mountain["lon"]
                )
            except Exception:
                # Fallback to estimate based on haversine distance
                drive_info = {
                    "duration_minutes": mountain.get("distance_km", 100) * 0.75,
                    "distance_km": mountain.get("distance_km", 100),
                    "error": "routing_api_failed",
                }
            enriched.append({**mountain, "drive_time": drive_info})
        return enriched

    def forward(
        self,
        query: str,
        current_date: date | None = None,
        user_location: dict | None = None,
    ) -> dspy.Prediction:
        """
        Run the full recommendation pipeline.

        Args:
            query: Natural language ski query
            current_date: Override current date (default: today)
            user_location: Dict with 'name', 'lat', 'lon' (default: Boston)

        Returns:
            Prediction with top_pick, alternatives, caveat, and intermediate results
        """
        # Defaults
        current_date = current_date or date.today()
        user_location = user_location or {
            "name": "Boston, MA",
            "lat": 42.3601,
            "lon": -71.0589,
        }

        # Build user context for parsing
        user_context = (
            f"Today's date: {current_date.isoformat()}\n"
            f"Tomorrow's date: {(current_date + timedelta(days=1)).isoformat()}\n"
            f"User's location: {user_location['name']} "
            f"({user_location['lat']}, {user_location['lon']})"
        )

        # Step 1: Parse query -> returns ParsedQuery Pydantic model
        result = self.parse_query(query=query, user_context=user_context)
        parsed = result.parsed  # ParsedQuery with proper types

        # Resolve target date
        target_date = self._resolve_date(parsed.target_date, current_date)

        # Step 2: Search for candidate mountains
        candidates = self._search_mountains(
            parsed, user_location["lat"], user_location["lon"]
        )

        if not candidates:
            return dspy.Prediction(
                top_pick="No mountains found matching your criteria.",
                alternatives="Try relaxing your filters (drive time, pass type, etc.)",
                caveat="",
                parsed=parsed,
                candidates=[],
                scores=[],
            )

        # Step 3: Enrich with conditions and drive times
        candidates = self._enrich_with_conditions(candidates, target_date)
        candidates = self._enrich_with_drive_times(
            candidates, user_location["lat"], user_location["lon"]
        )

        # Step 4: Assess overall day conditions
        user_prefs = json.dumps({
            "skill_level": parsed.skill_level,
            "activity": parsed.activity,
            "vibe": parsed.vibe,
            "needs_terrain_parks": parsed.needs_terrain_parks,
            "needs_glades": parsed.needs_glades,
            "needs_beginner_terrain": parsed.needs_beginner_terrain,
            "needs_expert_terrain": parsed.needs_expert_terrain,
        })

        day_assessment = self.assess_conditions(
            all_candidates=json.dumps(candidates),
            user_preferences=user_prefs,
        )

        day_context = (
            f"Day quality: {day_assessment.day_quality}\n"
            f"Best available: {day_assessment.best_available}\n"
            f"Context: {day_assessment.day_context}"
        )

        # Step 5: Score each mountain
        scored = []
        for mountain in candidates:
            score_result = self.score_mountain(
                mountain=json.dumps(mountain),
                user_preferences=user_prefs,
                day_context=day_context,
            )
            scored.append({
                "mountain": mountain,
                "score": score_result.score,
                "key_pros": score_result.key_pros,
                "key_cons": score_result.key_cons,
                "tradeoff_note": score_result.tradeoff_note,
            })

        # Sort by score descending
        scored.sort(key=lambda x: float(x["score"]), reverse=True)

        # Step 6: Get crowd context for top candidates
        crowd_info = get_crowd_context(target_date, scored[0]["mountain"]["state"])

        # Step 7: Generate final recommendation
        recommendation = self.generate_recommendation(
            query=query,
            day_assessment=day_context,
            scored_candidates=json.dumps(scored[:5]),  # Top 5
            crowd_context=json.dumps(crowd_info),
        )

        return dspy.Prediction(
            top_pick=recommendation.top_pick,
            alternatives=recommendation.alternatives,
            caveat=recommendation.caveat,
            # Intermediate results for evaluation/debugging
            parsed=parsed,
            candidates=candidates,
            day_assessment=day_assessment,
            scores=scored,
            crowd_info=crowd_info,
        )


def recommend(
    query: str,
    current_date: date | None = None,
    user_location: dict | None = None,
) -> dict:
    """
    Get ski recommendations using the explicit pipeline.

    Args:
        query: Natural language query
        current_date: Override current date
        user_location: Override location dict

    Returns:
        Dict with top_pick, alternatives, caveat
    """
    pipeline = SkiPipeline()
    result = pipeline(query, current_date, user_location)

    return {
        "top_pick": result.top_pick,
        "alternatives": result.alternatives,
        "caveat": result.caveat,
    }
