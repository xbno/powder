"""Evaluation datasets and metrics for DSPy optimization."""

from powder.evals.assess_conditions import (
    EXAMPLES as ASSESS_CONDITIONS_EXAMPLES,
    assess_conditions_metric,
    get_trainset as get_assess_conditions_trainset,
)

__all__ = [
    "ASSESS_CONDITIONS_EXAMPLES",
    "assess_conditions_metric",
    "get_assess_conditions_trainset",
]
