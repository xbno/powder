"""
GEPA optimization for Powder signatures.

Runs GEPA to optimize prompts for each signature using our eval datasets.

Usage:
    python -m powder.evals.optimize --signature parse_query
    python -m powder.evals.optimize --signature all

Environment variables:
    POWDER_BASE_LM: Model for base inference (default: anthropic/claude-haiku-4-5-20251001)
    POWDER_REFLECTION_LM: Model for GEPA reflection (default: anthropic/claude-haiku-4-5-20251001)
"""

import argparse
import json
import os
from pathlib import Path

import dspy
from dspy import GEPA
from dspy.teleprompt.gepa.gepa import ScoreWithFeedback

from powder.signatures import ParseSkiQuery, ParsedQuery, ScoreMountain, AssessConditions
from powder.evals import parse_query, score_mountain, assess_conditions, generate_recommendation

# Default models (can be overridden via env vars)
DEFAULT_BASE_LM = "anthropic/claude-haiku-4-5-20251001"
DEFAULT_REFLECTION_LM = "anthropic/claude-haiku-4-5-20251001"


def make_gepa_metric(base_metric, signature_name: str):
    """Wrap a base metric to return ScoreWithFeedback for GEPA."""

    def gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
        score = base_metric(gold, pred, trace)

        # Generate feedback based on what went wrong
        feedback_parts = []

        if signature_name == "ParseSkiQuery":
            parsed = pred.parsed
            # Check each field and provide specific feedback
            if hasattr(gold, "expected_pass_type"):
                if parsed.pass_type != gold.expected_pass_type:
                    feedback_parts.append(
                        f"pass_type should be '{gold.expected_pass_type}' but got '{parsed.pass_type}'"
                    )
            if hasattr(gold, "expected_needs_terrain_parks"):
                if parsed.needs_terrain_parks != gold.expected_needs_terrain_parks:
                    feedback_parts.append(
                        f"needs_terrain_parks should be {gold.expected_needs_terrain_parks}"
                    )
            if hasattr(gold, "expected_vibe"):
                if parsed.vibe != gold.expected_vibe:
                    feedback_parts.append(
                        f"vibe should be '{gold.expected_vibe}' but got '{parsed.vibe}'"
                    )
            if hasattr(gold, "expected_max_drive_hours"):
                if parsed.max_drive_hours != gold.expected_max_drive_hours:
                    feedback_parts.append(
                        f"max_drive_hours should be {gold.expected_max_drive_hours} but got {parsed.max_drive_hours}"
                    )

        if score >= 1.0:
            feedback = "Perfect! All fields extracted correctly."
        elif feedback_parts:
            feedback = "Issues: " + "; ".join(feedback_parts)
        else:
            feedback = f"Score: {score:.2f} - some fields were incorrect"

        return ScoreWithFeedback(score=score, feedback=feedback)

    return gepa_metric


def optimize_parse_query(
    max_calls: int = 50,
    output_dir: Path = None,
):
    """Optimize ParseSkiQuery signature with GEPA."""
    print("\n" + "=" * 60)
    print("Optimizing: ParseSkiQuery")
    print("=" * 60)

    # Get LMs from env vars or defaults
    base_lm = os.environ.get("POWDER_BASE_LM", DEFAULT_BASE_LM)
    reflection_lm = os.environ.get("POWDER_REFLECTION_LM", DEFAULT_REFLECTION_LM)

    print(f"Base LM: {base_lm}")
    print(f"Reflection LM: {reflection_lm}")

    # Configure DSPy
    dspy.configure(lm=dspy.LM(base_lm))

    # Get training data
    trainset = parse_query.get_trainset()
    print(f"Training examples: {len(trainset)}")

    # Create student module
    student = dspy.Predict(ParseSkiQuery)

    # Create GEPA metric with feedback
    metric = make_gepa_metric(parse_query.get_metric(), "ParseSkiQuery")

    # Run GEPA
    print(f"\nRunning GEPA (max_metric_calls={max_calls})...")
    optimizer = GEPA(
        metric=metric,
        max_metric_calls=max_calls,
        track_stats=True,
        reflection_lm=dspy.LM(reflection_lm, temperature=1.0),
    )

    optimized = optimizer.compile(
        student,
        trainset=trainset,
    )

    # Save optimized module
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "optimized"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "parse_query.json"
    optimized.save(output_path)
    print(f"\nSaved optimized module to: {output_path}")

    # Evaluate improvement
    print("\n--- Evaluation ---")
    base_score = 0
    opt_score = 0

    base_student = dspy.Predict(ParseSkiQuery)

    for ex in trainset:
        # Base
        base_pred = base_student(query=ex.query, user_context=ex.user_context)
        base_score += parse_query.parse_query_metric(ex, base_pred)

        # Optimized
        opt_pred = optimized(query=ex.query, user_context=ex.user_context)
        opt_score += parse_query.parse_query_metric(ex, opt_pred)

    base_avg = base_score / len(trainset)
    opt_avg = opt_score / len(trainset)

    print(f"Baseline:  {base_avg:.1%}")
    print(f"Optimized: {opt_avg:.1%}")
    print(f"Change:    {(opt_avg - base_avg):+.1%}")

    return optimized


def optimize_score_mountain(
    max_calls: int = 50,
    output_dir: Path = None,
):
    """Optimize ScoreMountain signature with GEPA."""
    print("\n" + "=" * 60)
    print("Optimizing: ScoreMountain")
    print("=" * 60)

    # Get LMs from env vars or defaults
    base_lm = os.environ.get("POWDER_BASE_LM", DEFAULT_BASE_LM)
    reflection_lm = os.environ.get("POWDER_REFLECTION_LM", DEFAULT_REFLECTION_LM)

    print(f"Base LM: {base_lm}")
    print(f"Reflection LM: {reflection_lm}")

    # Configure DSPy
    dspy.configure(lm=dspy.LM(base_lm))

    # Get training data
    trainset = score_mountain.get_trainset()
    print(f"Training examples: {len(trainset)}")

    # Create student module
    student = dspy.Predict(ScoreMountain)

    # Create GEPA metric with feedback
    def gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
        base_score = score_mountain.score_mountain_metric(gold, pred, trace)

        feedback_parts = []
        # Check score range
        try:
            score_val = float(pred.score)
            if score_val < 0 or score_val > 100:
                feedback_parts.append(f"Score {score_val} out of valid 0-100 range")
        except (ValueError, TypeError):
            feedback_parts.append(f"Score '{pred.score}' is not a valid number")

        # Check if expected score direction is correct
        if hasattr(gold, "expected_score_above"):
            try:
                if float(pred.score) < gold.expected_score_above:
                    feedback_parts.append(
                        f"Score should be above {gold.expected_score_above} for these conditions"
                    )
            except (ValueError, TypeError):
                pass

        if hasattr(gold, "expected_score_below"):
            try:
                if float(pred.score) > gold.expected_score_below:
                    feedback_parts.append(
                        f"Score should be below {gold.expected_score_below} for these conditions"
                    )
            except (ValueError, TypeError):
                pass

        if base_score >= 1.0:
            feedback = "Perfect! Score and reasoning are well-calibrated."
        elif feedback_parts:
            feedback = "Issues: " + "; ".join(feedback_parts)
        else:
            feedback = f"Score: {base_score:.2f} - check score calibration and reasoning"

        return ScoreWithFeedback(score=base_score, feedback=feedback)

    # Run GEPA
    print(f"\nRunning GEPA (max_metric_calls={max_calls})...")
    optimizer = GEPA(
        metric=gepa_metric,
        max_metric_calls=max_calls,
        track_stats=True,
        reflection_lm=dspy.LM(reflection_lm, temperature=1.0),
    )

    optimized = optimizer.compile(
        student,
        trainset=trainset,
    )

    # Save optimized module
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "optimized"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "score_mountain.json"
    optimized.save(output_path)
    print(f"\nSaved optimized module to: {output_path}")

    # Evaluate improvement
    print("\n--- Evaluation ---")
    base_score = 0
    opt_score = 0

    base_student = dspy.Predict(ScoreMountain)

    for ex in trainset:
        # Base
        base_pred = base_student(
            mountain=ex.mountain,
            user_preferences=ex.user_preferences,
            day_context=ex.day_context,
        )
        base_score += score_mountain.score_mountain_metric(ex, base_pred)

        # Optimized
        opt_pred = optimized(
            mountain=ex.mountain,
            user_preferences=ex.user_preferences,
            day_context=ex.day_context,
        )
        opt_score += score_mountain.score_mountain_metric(ex, opt_pred)

    base_avg = base_score / len(trainset)
    opt_avg = opt_score / len(trainset)

    print(f"Baseline:  {base_avg:.1%}")
    print(f"Optimized: {opt_avg:.1%}")
    print(f"Change:    {(opt_avg - base_avg):+.1%}")

    return optimized


def optimize_assess_conditions(
    max_calls: int = 50,
    output_dir: Path = None,
):
    """Optimize AssessConditions signature with GEPA."""
    print("\n" + "=" * 60)
    print("Optimizing: AssessConditions")
    print("=" * 60)

    # Get LMs from env vars or defaults
    base_lm = os.environ.get("POWDER_BASE_LM", DEFAULT_BASE_LM)
    reflection_lm = os.environ.get("POWDER_REFLECTION_LM", DEFAULT_REFLECTION_LM)

    print(f"Base LM: {base_lm}")
    print(f"Reflection LM: {reflection_lm}")

    # Configure DSPy
    dspy.configure(lm=dspy.LM(base_lm))

    # Get training data
    trainset = assess_conditions.get_trainset()
    print(f"Training examples: {len(trainset)}")

    # Create student module
    student = dspy.Predict(AssessConditions)

    # Create GEPA metric with feedback
    def gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
        base_score = assess_conditions.assess_conditions_metric(gold, pred, trace)

        feedback_parts = []

        # Check day_quality validity
        valid_qualities = {"excellent", "good", "fair", "poor", "stay_home"}
        if pred.day_quality.lower().strip() not in valid_qualities:
            feedback_parts.append(f"day_quality '{pred.day_quality}' is not valid (use: {valid_qualities})")

        # Check expected day quality
        if hasattr(gold, "expected_day_quality"):
            expected = gold.expected_day_quality
            if isinstance(expected, list):
                if pred.day_quality.lower().strip() not in [e.lower() for e in expected]:
                    feedback_parts.append(
                        f"day_quality should be one of {expected} but got '{pred.day_quality}'"
                    )
            else:
                if pred.day_quality.lower().strip() != expected.lower():
                    feedback_parts.append(
                        f"day_quality should be '{expected}' but got '{pred.day_quality}'"
                    )

        # Check if wind should be mentioned
        if hasattr(gold, "expected_mention_wind") and gold.expected_mention_wind:
            if "wind" not in pred.day_context.lower():
                feedback_parts.append("Should mention wind in day_context for windy conditions")

        # Check if cold should be mentioned
        if hasattr(gold, "expected_mention_cold") and gold.expected_mention_cold:
            cold_words = ["cold", "frigid", "bitter", "freezing", "temperature", "frostbite"]
            if not any(w in pred.day_context.lower() for w in cold_words):
                feedback_parts.append("Should mention cold/temperature in day_context for bitter cold")

        if base_score >= 1.0:
            feedback = "Perfect! Day quality and context are well-calibrated."
        elif feedback_parts:
            feedback = "Issues: " + "; ".join(feedback_parts)
        else:
            feedback = f"Score: {base_score:.2f} - check day quality and context"

        return ScoreWithFeedback(score=base_score, feedback=feedback)

    # Run GEPA
    print(f"\nRunning GEPA (max_metric_calls={max_calls})...")
    optimizer = GEPA(
        metric=gepa_metric,
        max_metric_calls=max_calls,
        track_stats=True,
        reflection_lm=dspy.LM(reflection_lm, temperature=1.0),
    )

    optimized = optimizer.compile(
        student,
        trainset=trainset,
    )

    # Save optimized module
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "optimized"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "assess_conditions.json"
    optimized.save(output_path)
    print(f"\nSaved optimized module to: {output_path}")

    # Evaluate improvement
    print("\n--- Evaluation ---")
    base_score = 0
    opt_score = 0

    base_student = dspy.Predict(AssessConditions)

    for ex in trainset:
        # Base
        base_pred = base_student(
            all_candidates=ex.all_candidates,
            user_preferences=ex.user_preferences,
        )
        base_score += assess_conditions.assess_conditions_metric(ex, base_pred)

        # Optimized
        opt_pred = optimized(
            all_candidates=ex.all_candidates,
            user_preferences=ex.user_preferences,
        )
        opt_score += assess_conditions.assess_conditions_metric(ex, opt_pred)

    base_avg = base_score / len(trainset)
    opt_avg = opt_score / len(trainset)

    print(f"Baseline:  {base_avg:.1%}")
    print(f"Optimized: {opt_avg:.1%}")
    print(f"Change:    {(opt_avg - base_avg):+.1%}")

    return optimized


def main():
    parser = argparse.ArgumentParser(description="Run GEPA optimization")
    parser.add_argument(
        "--signature",
        choices=["parse_query", "score_mountain", "assess_conditions", "all"],
        default="parse_query",
        help="Which signature to optimize",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=50,
        help="Max metric calls for GEPA (default: 50, use 200+ for thorough)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for optimized modules",
    )

    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    if args.signature in ("parse_query", "all"):
        optimize_parse_query(
            max_calls=args.max_calls,
            output_dir=args.output_dir,
        )

    if args.signature in ("score_mountain", "all"):
        optimize_score_mountain(
            max_calls=args.max_calls,
            output_dir=args.output_dir,
        )

    if args.signature in ("assess_conditions", "all"):
        optimize_assess_conditions(
            max_calls=args.max_calls,
            output_dir=args.output_dir,
        )


if __name__ == "__main__":
    main()
