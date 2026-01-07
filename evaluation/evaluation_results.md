# Powder Evaluation Results

Evaluation of the ski recommendation agent using deterministic metrics (no LLM-as-judge).

## Model & Configuration

- **Model**: Claude Haiku (claude-haiku-4-5-20251001)
- **Mountains**: 30 Northeast US resorts
- **Eval Examples**: 39 labeled examples across 4 signatures + 12 end-to-end
- **Optimization**: GEPA (Reflective Prompt Evolution) with `enable_tool_optimization=True`
- **Date**: January 2026

## Summary: GEPA Optimization Results

| Component | Baseline | After GEPA | Improvement |
|-----------|----------|------------|-------------|
| Pipeline Hit@1 | 58.3% | **66.7%** | +8.4% |
| Pipeline Hit@3 | 75.0% | **75.0%** | - |
| ReAct Hit@1 | 50.0% | **75.0%** | +25.0% |
| ReAct Hit@3 | 66.7% | **91.7%** | +25.0% |

**Key Finding**: GEPA tool optimization dramatically improved ReAct performance. By jointly optimizing the agent instructions AND tool descriptions, ReAct went from underperforming Pipeline to outperforming it on Hit@1 and Hit@3.

## Signature-Level Performance

Individual DSPy signatures after GEPA optimization:

| Signature | Baseline | Optimized | Change |
|-----------|----------|-----------|--------|
| ParseSkiQuery | 97.4% | 97.4% | - (already optimal) |
| AssessConditions | 93.8% | 100% | +6.2% |
| ScoreMountain | 92.5% | 96.3% | +3.8% |
| GenerateRecommendation | 100% | 100% | - (already optimal) |

## End-to-End Performance (v3 - GEPA Optimized)

### Pipeline vs ReAct Comparison

| Metric | Pipeline | ReAct (Optimized) |
|--------|----------|-------------------|
| **Hit@1** | 66.7% | **75.0%** |
| **Hit@3** | 75.0% | **91.7%** |
| **Constraint Satisfaction** | 92.3% | 0.0%* |
| **Exclusion Check** | 100% | 100% |

*ReAct constraint metric is 0% because the metric cannot parse constraints from unstructured text, not because ReAct violates constraints.

## GEPA Optimization Details

### What GEPA Optimized

1. **Signature Instructions**: Detailed scoring frameworks with explicit calibration rules
2. **Tool Descriptions**: Domain-specific guidance for ski queries (e.g., "prioritize mountains with 'excellent' learning_area_quality over proximity")
3. **Tool Argument Descriptions**: Better defaults and usage hints

### ScoreMountain Optimized Prompt

GEPA generated a detailed scoring framework:
- Fresh snow weighting: 14"+ = +25 points, 8-13" = +20, 4-7" = +10
- Temperature preservation: Cold temps (<25°F) = +5, warm (>35°F) = -10
- Pass incompatibility: -15 to -20 points
- Drive time penalties: <90 min = 0, 90-150 = -5, 150-200 = -10, >200 = -15
- Explicit score calibration: 85+ exceptional, 75-84 very good, 65-74 solid, <50 poor fit

### ReAct Tool Optimization

With `enable_tool_optimization=True`, GEPA optimized tool descriptions to include:
- Priority ordering: terrain/feature match > pass type > conditions > drive time
- Domain knowledge: "Stratton, Okemo, Smugglers' Notch, Waterville Valley have 'excellent' learning_area_quality"
- Anti-proximity bias: "Avoid recommending the closest mountain if a slightly farther option significantly better matches the user's stated preferences"

## Error Analysis

### Pipeline Remaining Failures (4/12)

| Example | Issue |
|---------|-------|
| beginner_family | Picked Stowe over Okemo/Stratton (excellent learning areas) |
| short_drive | Picked Mount Snow despite 1.5h max constraint |
| icy_day_ikon | Recommended skipping the day entirely |
| no_pass_powder | Picked Smugglers' over Jay Peak (more snow) |

### ReAct Remaining Failures (3/12)

| Example | Issue |
|---------|-------|
| powder_epic_boston | Picked Okemo (Hit@3 ✓) instead of Stowe |
| glade_skiing | Picked Killington (Hit@3 ✓) instead of Jay Peak |
| icy_day_ikon | Picked Stratton instead of Killington/Sugarbush |

## Evolution of Results

### v1 → v2: Pydantic Fix
- Pipeline: 41.7% → 58.3% Hit@1 (+16.6%)
- Fixed `pass_type='null'` string bug with Pydantic models

### v2 → v3: GEPA Optimization
- Pipeline: 58.3% → 66.7% Hit@1 (+8.4%)
- ReAct: 50.0% → 75.0% Hit@1 (+25.0%)
- ReAct: 66.7% → 91.7% Hit@3 (+25.0%)

## Raw Results (v3)

### Pipeline Detailed Results

```
[powder_ikon_boston]  ✓ Hit@1  ✓ Hit@3  Constraints: 2/2
[powder_epic_boston]  ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
[park_day_boston]     ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
[beginner_family]     ✗ Hit@1  ✓ Hit@3  Picked Stowe (expected Okemo/Stratton)
[night_skiing]        ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
[glade_skiing]        ✓ Hit@1  ✓ Hit@3  Constraints: 2/2
[short_drive]         ✗ Hit@1  ✗ Hit@3  Picked Mount Snow (violated 1.5h constraint)
[expert_terrain]      ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
[icy_day_ikon]        ✗ Hit@1  ✗ Hit@3  Recommended skipping
[no_pass_powder]      ✗ Hit@1  ✗ Hit@3  Picked Smugglers' (expected Jay Peak)
[indy_pass]           ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
[nyc_powder_day]      ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
```

### ReAct Detailed Results (GEPA-Optimized)

```
[powder_ikon_boston]  ✓ Hit@1  ✓ Hit@3  ← FIXED by GEPA
[powder_epic_boston]  ✗ Hit@1  ✓ Hit@3  Picked Okemo (expected Stowe)
[park_day_boston]     ✓ Hit@1  ✓ Hit@3
[beginner_family]     ✓ Hit@1  ✓ Hit@3  ← FIXED by GEPA (was picking Nashoba)
[night_skiing]        ✓ Hit@1  ✓ Hit@3
[glade_skiing]        ✗ Hit@1  ✓ Hit@3  Picked Killington (expected Jay Peak)
[short_drive]         ✓ Hit@1  ✓ Hit@3
[expert_terrain]      ✓ Hit@1  ✓ Hit@3
[icy_day_ikon]        ✗ Hit@1  ✗ Hit@3  Picked Stratton (expected Killington)
[no_pass_powder]      ✓ Hit@1  ✓ Hit@3  ← FIXED by GEPA (was picking Wachusett)
[indy_pass]           ✓ Hit@1  ✓ Hit@3
[nyc_powder_day]      ✓ Hit@1  ✓ Hit@3
```

## Conclusion

GEPA optimization significantly improved both approaches:

| Metric | Pipeline | ReAct (Optimized) | Winner |
|--------|----------|-------------------|--------|
| Hit@1 | 66.7% | **75.0%** | ReAct |
| Hit@3 | 75.0% | **91.7%** | ReAct |
| Constraints | **92.3%** | 0.0%* | Pipeline |

The tool optimization feature (`enable_tool_optimization=True`) was critical for ReAct - it allowed GEPA to add domain-specific guidance to tool descriptions, reducing the proximity bias that previously hurt ReAct performance.

Pipeline remains better for constraint satisfaction because it has explicit filtering logic, while ReAct's unstructured output makes constraint verification harder to measure.
