"""
Evaluation runner - runs all evals and produces aggregate metrics.

This is the main entry point for evaluation. Run with:
    python -m powder.evals.runner

Or via make:
    make eval
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import dspy

from powder.evals import parse_query, score_mountain, generate_recommendation, assess_conditions
from powder.evals.end_to_end import (
    EXAMPLES as E2E_EXAMPLES,
    EndToEndExample,
    EvalResult,
    calculate_hit_at_1,
    calculate_hit_at_3,
    calculate_constraint_satisfaction,
    calculate_exclusion_check,
    calculate_reasoning_keywords,
    compute_aggregate_metrics,
)
from powder.evals.backtest import mock_weather_api, mock_routing_api, run_react_with_mocks
from powder.pipeline import SkiPipeline
from powder.signatures import (
    ParseSkiQuery,
    AssessConditions,
    ScoreMountain,
    GenerateRecommendation,
)


def run_signature_eval(
    name: str,
    examples: list,
    predictor: dspy.Module,
    metric_fn: callable,
    verbose: bool = False,
) -> dict:
    """
    Run evaluation for a single signature.

    Returns dict with scores and details.
    """
    print(f"\n{'=' * 60}")
    print(f"Evaluating: {name}")
    print(f"{'=' * 60}")

    scores = []
    failures = []

    for i, example in enumerate(examples):
        try:
            # Get input field names from example
            input_fields = example.inputs().keys()
            inputs = {k: getattr(example, k) for k in input_fields}

            pred = predictor(**inputs)
            score = metric_fn(example, pred)
            scores.append(score)

            if verbose or score < 0.8:
                status = "✓" if score >= 0.8 else "✗"
                print(f"  [{status}] Example {i + 1}: {score:.2f}")
                if score < 0.8:
                    # Show what went wrong
                    print(f"      Query/Input: {str(inputs)[:80]}...")

        except Exception as e:
            scores.append(0.0)
            failures.append({"example": i + 1, "error": str(e)})
            print(f"  [!] Example {i + 1}: ERROR - {e}")

    avg_score = sum(scores) / len(scores) if scores else 0.0
    print(f"\n  Average: {avg_score:.1%} ({sum(1 for s in scores if s >= 0.8)}/{len(scores)} passed)")

    return {
        "name": name,
        "avg_score": avg_score,
        "scores": scores,
        "failures": failures,
        "total": len(examples),
        "passed": sum(1 for s in scores if s >= 0.8),
    }


def run_end_to_end_eval(
    examples: list[EndToEndExample],
    verbose: bool = False,
) -> dict:
    """
    Run end-to-end pipeline evaluation.

    This tests the full SkiPipeline against labeled examples.
    """
    print(f"\n{'=' * 60}")
    print("Evaluating: End-to-End Pipeline")
    print(f"{'=' * 60}")

    pipeline = SkiPipeline()
    results = []

    for example in examples:
        print(f"\n  [{example.id}] {example.query[:50]}...")

        try:
            # Run pipeline with mocked APIs for reproducibility
            with mock_weather_api(example.conditions_snapshot), mock_routing_api():
                result = pipeline(
                    query=example.query,
                    current_date=example.query_date,
                    user_location=example.user_location,
                )

            # Extract predictions
            top_pick = result.top_pick
            # Get top 3 from scored candidates
            top_3 = [s["mountain"]["name"] for s in result.scores[:3]] if result.scores else []

            # Calculate metrics
            hit_1 = calculate_hit_at_1(example, top_pick)
            hit_3 = calculate_hit_at_3(example, top_3)

            # Build candidates list for constraint check
            candidates = [s["mountain"] for s in result.scores] if result.scores else []
            constraints = calculate_constraint_satisfaction(example, top_pick, candidates)

            exclusion = calculate_exclusion_check(example, top_pick)

            full_text = f"{top_pick} {result.alternatives} {result.caveat}"
            reasoning = calculate_reasoning_keywords(example, full_text)

            eval_result = EvalResult(
                example_id=example.id,
                hit_at_1=hit_1,
                hit_at_3=hit_3,
                constraint_satisfaction=constraints,
                exclusion_check=exclusion,
                reasoning_score=reasoning,
                predicted_top_pick=top_pick[:100] if top_pick else "",
                predicted_top_3=top_3,
            )
            results.append(eval_result)

            # Print result
            status = "✓" if hit_1 else "✗"
            print(f"    Hit@1: {status} | Hit@3: {'✓' if hit_3 else '✗'} | "
                  f"Constraints: {sum(constraints.values())}/{len(constraints) or 1}")

            if verbose or not hit_1:
                print(f"    Predicted: {top_pick[:60]}...")
                print(f"    Expected: {example.expected_top_pick}")
                if constraints and not all(constraints.values()):
                    failed = [k for k, v in constraints.items() if not v]
                    print(f"    Failed constraints: {failed}")

        except Exception as e:
            print(f"    ERROR: {e}")
            results.append(EvalResult(
                example_id=example.id,
                hit_at_1=False,
                hit_at_3=False,
                constraint_satisfaction={},
                exclusion_check=False,
                reasoning_score=0.0,
                predicted_top_pick=f"ERROR: {e}",
                predicted_top_3=[],
            ))

    # Compute aggregates
    metrics = compute_aggregate_metrics(results)

    print(f"\n  Summary: {metrics}")

    return {
        "name": "End-to-End Pipeline",
        "metrics": metrics.to_dict(),
        "detailed_results": [
            {
                "id": r.example_id,
                "hit_at_1": r.hit_at_1,
                "hit_at_3": r.hit_at_3,
                "constraints": r.constraint_satisfaction,
                "predicted": r.predicted_top_pick[:50],
            }
            for r in results
        ],
    }


def run_react_eval(
    examples: list[EndToEndExample],
    verbose: bool = False,
) -> dict:
    """
    Run end-to-end ReAct agent evaluation.

    This tests the ReAct agent against the same labeled examples as Pipeline.
    Note: ReAct returns unstructured text, so Hit@1/Hit@3 checks for mountain
    name mentions in the recommendation string.
    """
    print(f"\n{'=' * 60}")
    print("Evaluating: End-to-End ReAct Agent")
    print(f"{'=' * 60}")

    results = []

    for example in examples:
        print(f"\n  [{example.id}] {example.query[:50]}...")

        try:
            # Run ReAct agent with mocked APIs
            result = run_react_with_mocks(
                query=example.query,
                query_date=example.query_date,
                user_location=example.user_location,
                conditions=example.conditions_snapshot,
            )

            recommendation = result["recommendation"]

            # For ReAct, we check if expected mountains are mentioned in response
            # since it returns unstructured text
            hit_1 = calculate_hit_at_1(example, recommendation)

            # For Hit@3, check if any expected mountains are mentioned
            # (ReAct doesn't give us an ordered list, so we check mentions)
            hit_3 = any(
                mtn.lower() in recommendation.lower()
                for mtn in example.expected_in_top_3
            ) if example.expected_in_top_3 else hit_1

            # Constraint check - verify pass type and other filters are respected
            constraints = calculate_constraint_satisfaction(example, recommendation, [])

            exclusion = calculate_exclusion_check(example, recommendation)
            reasoning = calculate_reasoning_keywords(example, recommendation)

            eval_result = EvalResult(
                example_id=example.id,
                hit_at_1=hit_1,
                hit_at_3=hit_3,
                constraint_satisfaction=constraints,
                exclusion_check=exclusion,
                reasoning_score=reasoning,
                predicted_top_pick=recommendation[:100] if recommendation else "",
                predicted_top_3=[],  # ReAct doesn't give ordered list
            )
            results.append(eval_result)

            # Print result
            status = "✓" if hit_1 else "✗"
            print(f"    Hit@1: {status} | Hit@3: {'✓' if hit_3 else '✗'} | "
                  f"Constraints: {sum(constraints.values())}/{len(constraints) or 1}")

            if verbose or not hit_1:
                print(f"    Response: {recommendation[:80]}...")
                print(f"    Expected: {example.expected_top_pick}")

        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            if verbose:
                traceback.print_exc()
            results.append(EvalResult(
                example_id=example.id,
                hit_at_1=False,
                hit_at_3=False,
                constraint_satisfaction={},
                exclusion_check=False,
                reasoning_score=0.0,
                predicted_top_pick=f"ERROR: {e}",
                predicted_top_3=[],
            ))

    # Compute aggregates
    metrics = compute_aggregate_metrics(results)

    print(f"\n  Summary: {metrics}")

    return {
        "name": "End-to-End ReAct",
        "metrics": metrics.to_dict(),
        "detailed_results": [
            {
                "id": r.example_id,
                "hit_at_1": r.hit_at_1,
                "hit_at_3": r.hit_at_3,
                "constraints": r.constraint_satisfaction,
                "predicted": r.predicted_top_pick[:50],
            }
            for r in results
        ],
    }


def run_all_evals(
    model: str = "anthropic/claude-haiku-4-5-20251001",
    verbose: bool = False,
    mode: str = "pipeline",
) -> dict:
    """
    Run all evaluations and return comprehensive results.

    Args:
        model: LLM model to use
        verbose: Show detailed output
        mode: "pipeline", "react", or "both"
    """
    print(f"\n🎿 Powder Evaluation Suite")
    print(f"Model: {model}")
    print(f"Mode: {mode}")
    print(f"Time: {datetime.now().isoformat()}")

    # Configure DSPy
    dspy.configure(lm=dspy.LM(model))

    results = {
        "model": model,
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "signatures": {},
        "end_to_end_pipeline": None,
        "end_to_end_react": None,
    }

    # 1. ParseSkiQuery
    parse_result = run_signature_eval(
        name="ParseSkiQuery",
        examples=parse_query.get_trainset(),
        predictor=dspy.Predict(ParseSkiQuery),
        metric_fn=parse_query.get_metric(),
        verbose=verbose,
    )
    results["signatures"]["ParseSkiQuery"] = parse_result

    # 2. AssessConditions
    assess_result = run_signature_eval(
        name="AssessConditions",
        examples=assess_conditions.get_trainset(),
        predictor=dspy.Predict(AssessConditions),
        metric_fn=assess_conditions.get_metric(),
        verbose=verbose,
    )
    results["signatures"]["AssessConditions"] = assess_result

    # 3. ScoreMountain
    score_result = run_signature_eval(
        name="ScoreMountain",
        examples=score_mountain.get_trainset(),
        predictor=dspy.Predict(ScoreMountain),
        metric_fn=score_mountain.get_metric(),
        verbose=verbose,
    )
    results["signatures"]["ScoreMountain"] = score_result

    # 4. GenerateRecommendation
    gen_result = run_signature_eval(
        name="GenerateRecommendation",
        examples=generate_recommendation.get_trainset(),
        predictor=dspy.Predict(GenerateRecommendation),
        metric_fn=generate_recommendation.get_metric(),
        verbose=verbose,
    )
    results["signatures"]["GenerateRecommendation"] = gen_result

    # 5. End-to-End Pipeline
    if mode in ("pipeline", "both"):
        e2e_pipeline = run_end_to_end_eval(E2E_EXAMPLES, verbose=verbose)
        results["end_to_end_pipeline"] = e2e_pipeline

    # 6. End-to-End ReAct
    if mode in ("react", "both"):
        e2e_react = run_react_eval(E2E_EXAMPLES, verbose=verbose)
        results["end_to_end_react"] = e2e_react

    # Summary
    print(f"\n{'=' * 60}")
    print("EVALUATION SUMMARY")
    print(f"{'=' * 60}")

    print("\nSignature Metrics (avg score):")
    for name, data in results["signatures"].items():
        bar = "█" * int(data["avg_score"] * 20)
        print(f"  {name:25} {data['avg_score']:5.1%} {bar}")

    if results["end_to_end_pipeline"]:
        print("\nEnd-to-End Pipeline Metrics:")
        e2e = results["end_to_end_pipeline"]["metrics"]
        print(f"  Hit@1:                   {e2e['hit_at_1']}")
        print(f"  Hit@3:                   {e2e['hit_at_3']}")
        print(f"  Constraint Satisfaction: {e2e['constraint_satisfaction']}")
        print(f"  Exclusion Check:         {e2e['exclusion_check']}")

    if results["end_to_end_react"]:
        print("\nEnd-to-End ReAct Metrics:")
        e2e = results["end_to_end_react"]["metrics"]
        print(f"  Hit@1:                   {e2e['hit_at_1']}")
        print(f"  Hit@3:                   {e2e['hit_at_3']}")
        print(f"  Constraint Satisfaction: {e2e['constraint_satisfaction']}")
        print(f"  Exclusion Check:         {e2e['exclusion_check']}")

    # Comparison if both ran
    if results["end_to_end_pipeline"] and results["end_to_end_react"]:
        print("\n--- Pipeline vs ReAct Comparison ---")
        p = results["end_to_end_pipeline"]["metrics"]
        r = results["end_to_end_react"]["metrics"]
        print(f"  {'Metric':<25} {'Pipeline':>10} {'ReAct':>10}")
        print(f"  {'-'*45}")
        print(f"  {'Hit@1':<25} {p['hit_at_1']:>10} {r['hit_at_1']:>10}")
        print(f"  {'Hit@3':<25} {p['hit_at_3']:>10} {r['hit_at_3']:>10}")
        print(f"  {'Constraint Satisfaction':<25} {p['constraint_satisfaction']:>10} {r['constraint_satisfaction']:>10}")

    return results


def save_results(results: dict, output_path: Path | None = None):
    """Save evaluation results to JSON file."""
    if output_path is None:
        output_path = Path(__file__).parent.parent.parent / "eval_results.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Powder evaluation suite")
    parser.add_argument(
        "--model",
        default="anthropic/claude-haiku-4-5-20251001",
        help="Model to evaluate (default: claude-haiku)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output for all examples",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output path for results JSON",
    )
    parser.add_argument(
        "--mode",
        choices=["pipeline", "react", "both"],
        default="pipeline",
        help="Which end-to-end agent to evaluate (default: pipeline)",
    )
    parser.add_argument(
        "--signatures-only",
        action="store_true",
        help="Only run signature evals, skip end-to-end",
    )

    args = parser.parse_args()

    # Check for API key
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    results = run_all_evals(model=args.model, verbose=args.verbose, mode=args.mode)

    if args.output:
        save_results(results, args.output)


if __name__ == "__main__":
    main()
