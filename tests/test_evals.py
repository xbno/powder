"""Tests for evaluation framework - ensures datasets and metrics work correctly."""

import json
import pytest
import dspy

from powder.evals import (
    parse_query,
    score_mountain,
    generate_recommendation,
    assess_conditions,
    end_to_end,
)


class TestParseQueryEval:
    """Tests for ParseSkiQuery evaluation."""

    def test_dataset_loads(self):
        """Eval dataset loads without errors."""
        examples = parse_query.get_trainset()
        assert len(examples) >= 10  # At least 10 examples

    def test_examples_have_required_fields(self):
        """Each example has query and user_context inputs."""
        for ex in parse_query.EXAMPLES:
            assert hasattr(ex, "query")
            assert hasattr(ex, "user_context")

    def test_metric_scores_perfect_prediction(self):
        """Metric returns 1.0 for perfect prediction."""
        example = parse_query.POWDER_CHASE

        # Create a mock prediction matching expected values
        class MockPred:
            target_date = "today"
            max_drive_hours = 3.0
            pass_type = "ikon"
            needs_terrain_parks = False
            needs_glades = False
            needs_beginner_terrain = False
            needs_expert_terrain = False
            needs_night_skiing = False
            vibe = "powder_chase"

        score = parse_query.parse_query_metric(example, MockPred())
        assert score == 1.0

    def test_metric_penalizes_wrong_values(self):
        """Metric returns < 1.0 for incorrect predictions."""
        example = parse_query.POWDER_CHASE

        class WrongPred:
            target_date = "today"
            max_drive_hours = 5.0  # Wrong
            pass_type = "epic"  # Wrong
            needs_terrain_parks = True  # Wrong
            needs_glades = False
            needs_beginner_terrain = False
            needs_expert_terrain = False
            needs_night_skiing = False
            vibe = "casual"  # Wrong

        score = parse_query.parse_query_metric(example, WrongPred())
        assert score < 1.0


class TestScoreMountainEval:
    """Tests for ScoreMountain evaluation."""

    def test_dataset_loads(self):
        """Eval dataset loads without errors."""
        examples = score_mountain.get_trainset()
        assert len(examples) >= 5

    def test_examples_have_json_inputs(self):
        """Each example has valid JSON inputs."""
        for ex in score_mountain.EXAMPLES:
            # Should be valid JSON
            mountain = json.loads(ex.mountain)
            prefs = json.loads(ex.user_preferences)
            assert "name" in mountain
            assert isinstance(prefs, dict)

    def test_metric_validates_score_range(self):
        """Metric checks that score is 0-100."""
        example = score_mountain.STOWE_POWDER_DAY

        class ValidPred:
            score = 85
            key_pros = "Fresh powder, great glades"
            key_cons = "Long drive"
            tradeoff_note = "Best snow but furthest"

        class InvalidPred:
            score = 150  # Invalid
            key_pros = "Fresh powder"
            key_cons = "Long drive"
            tradeoff_note = "Best snow"

        valid_score = score_mountain.score_mountain_metric(example, ValidPred())
        invalid_score = score_mountain.score_mountain_metric(example, InvalidPred())

        assert valid_score > invalid_score


class TestGenerateRecommendationEval:
    """Tests for GenerateRecommendation evaluation."""

    def test_dataset_loads(self):
        """Eval dataset loads without errors."""
        examples = generate_recommendation.get_trainset()
        assert len(examples) >= 5

    def test_metric_checks_top_pick(self):
        """Metric verifies top pick matches expected."""
        example = generate_recommendation.CLEAR_WINNER

        class CorrectPred:
            top_pick = "I recommend Stowe for the best powder conditions."
            alternatives = "Sugarbush is a good backup option."
            caveat = "Expect crowds on the weekend."

        class WrongPred:
            top_pick = "I recommend Mount Snow."
            alternatives = "Nothing else is good."
            caveat = ""

        correct_score = generate_recommendation.generate_recommendation_metric(
            example, CorrectPred()
        )
        wrong_score = generate_recommendation.generate_recommendation_metric(
            example, WrongPred()
        )

        assert correct_score > wrong_score


class TestAssessConditionsEval:
    """Tests for AssessConditions evaluation."""

    def test_dataset_loads(self):
        """Eval dataset loads without errors."""
        examples = assess_conditions.get_trainset()
        assert len(examples) >= 4

    def test_metric_checks_validity(self):
        """Metric validates day_quality is valid enum."""
        example = assess_conditions.POWDER_DAY

        class ValidPred:
            day_quality = "excellent"
            best_available = "Stowe has 14 inches of fresh powder"
            day_context = "Cold temps preserving the snow"

        class InvalidPred:
            day_quality = "super_duper"  # Invalid enum
            best_available = "Unknown mountain"
            day_context = "No context"

        valid_score = assess_conditions.assess_conditions_metric(example, ValidPred())
        invalid_score = assess_conditions.assess_conditions_metric(example, InvalidPred())

        assert valid_score > invalid_score


class TestEndToEndEval:
    """Tests for end-to-end evaluation framework."""

    def test_dataset_loads(self):
        """Eval dataset loads without errors."""
        examples = end_to_end.get_examples()
        assert len(examples) >= 10

    def test_examples_have_required_fields(self):
        """Each example has required fields for evaluation."""
        for ex in end_to_end.EXAMPLES:
            assert ex.id
            assert ex.query
            assert ex.query_date
            assert ex.user_location
            assert ex.expected_top_pick
            assert ex.expected_in_top_3

    def test_hit_at_1_calculation(self):
        """Hit@1 correctly identifies matches."""
        example = end_to_end.EXAMPLES[0]  # powder_ikon_boston

        # Matching prediction
        assert end_to_end.calculate_hit_at_1(example, "Jay Peak is the best choice")
        assert end_to_end.calculate_hit_at_1(example, "Go to Sugarbush for powder")

        # Non-matching (Stowe is Epic, not Ikon)
        assert not end_to_end.calculate_hit_at_1(example, "Stowe has the most snow")

    def test_hit_at_3_calculation(self):
        """Hit@3 correctly checks top 3 list."""
        example = end_to_end.EXAMPLES[0]

        assert end_to_end.calculate_hit_at_3(example, ["Jay Peak", "Stowe", "Okemo"])
        assert end_to_end.calculate_hit_at_3(example, ["Stowe", "Sugarbush", "Okemo"])
        assert not end_to_end.calculate_hit_at_3(example, ["Stowe", "Okemo", "Mount Snow"])

    def test_constraint_satisfaction(self):
        """Constraint satisfaction correctly validates pass type."""
        example = end_to_end.EXAMPLES[0]  # Has pass_type: ikon constraint

        candidates = [
            {"name": "Jay Peak", "pass_types": "ikon"},
            {"name": "Stowe", "pass_types": "epic"},
        ]

        # Jay Peak satisfies ikon constraint
        result = end_to_end.calculate_constraint_satisfaction(
            example, "Jay Peak is great", candidates
        )
        assert result.get("pass_type") == True

        # Stowe violates ikon constraint
        result = end_to_end.calculate_constraint_satisfaction(
            example, "Stowe is great", candidates
        )
        assert result.get("pass_type") == False

    def test_aggregate_metrics(self):
        """Aggregate metrics compute correctly."""
        from powder.evals.end_to_end import EvalResult, compute_aggregate_metrics

        results = [
            EvalResult("ex1", True, True, {"pass": True}, True, 1.0, "Jay Peak", ["Jay Peak"]),
            EvalResult("ex2", False, True, {"pass": True}, True, 0.5, "Stowe", ["Stowe"]),
            EvalResult("ex3", True, True, {"pass": False}, False, 0.8, "Jay Peak", ["Jay Peak"]),
        ]

        metrics = compute_aggregate_metrics(results)

        assert metrics.hit_at_1_rate == pytest.approx(2 / 3)
        assert metrics.hit_at_3_rate == 1.0
        assert metrics.total_examples == 3


class TestEvalDatasetCoverage:
    """Tests to ensure eval dataset has good coverage."""

    def test_parse_query_covers_all_filters(self):
        """ParseSkiQuery dataset tests all filter types."""
        all_queries = " ".join(ex.query for ex in parse_query.EXAMPLES)

        # Should have examples for each filter type
        assert "ikon" in all_queries.lower() or "epic" in all_queries.lower()
        assert "park" in all_queries.lower() or "terrain" in all_queries.lower()
        assert "beginner" in all_queries.lower() or "first time" in all_queries.lower()
        assert "night" in all_queries.lower()
        assert "glades" in all_queries.lower() or "tree" in all_queries.lower()

    def test_end_to_end_covers_pass_types(self):
        """E2E dataset tests all major pass types."""
        pass_types = set()
        for ex in end_to_end.EXAMPLES:
            if "pass_type" in ex.constraints:
                pass_types.add(ex.constraints["pass_type"])

        assert "ikon" in pass_types
        assert "epic" in pass_types
        assert "indy" in pass_types

    def test_end_to_end_covers_user_locations(self):
        """E2E dataset tests multiple user locations."""
        locations = set()
        for ex in end_to_end.EXAMPLES:
            locations.add(ex.user_location["name"])

        assert len(locations) >= 2  # At least Boston and NYC
