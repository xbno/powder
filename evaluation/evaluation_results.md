# Powder Evaluation Results

Evaluation of the ski recommendation pipeline using deterministic metrics (no LLM-as-judge).

## Model & Configuration

- **Model**: Claude Haiku (claude-haiku-4-5-20251001)
- **Mountains**: 30 Northeast US resorts
- **Eval Examples**: 39 labeled examples across 4 signatures + 16 end-to-end
- **Optimization**: GEPA (Reflective Prompt Evolution)
- **Date**: January 2026

## Current Performance (Final)

### Signature-Level Metrics

| Signature | Score | Status |
|-----------|-------|--------|
| ParseSkiQuery | 97.4% | 12/12 passed |
| AssessConditions | 100.0% | 4/4 passed |
| ScoreMountain | 93.8% | 8/8 passed |
| GenerateRecommendation | 100.0% | 7/7 passed |

### End-to-End Metrics

| Agent | Hit@1 | Hit@3 | Constraint Satisfaction |
|-------|-------|-------|-------------------------|
| **Pipeline** | **93.8%** | **93.8%** | 100.0% |
| **ReAct** | 87.5% | 87.5% | n/a* |

*ReAct constraint metric is n/a because it returns unstructured text.

## End-to-End Detailed Results (v2b)

### Passing Examples (15/16)

| Example | Query | Hit@1 | Hit@3 | Constraints |
|---------|-------|-------|-------|-------------|
| powder_ikon_feb17 | Best powder today? I have an Ikon pass | ✓ | ✓ | 1/1 |
| powder_no_pass_jan02 | Where has the best snow today? | ✓ | ✓ | N/A |
| powder_south_vt_dec10 | Best skiing within 3 hours of Boston? | ✓ | ✓ | 1/1 |
| nyc_powder_mar29 | Best powder today from NYC? | ✓ | ✓ | N/A |
| park_day_jan02 | I want to hit rails and jumps tomorrow | ✓ | ✓ | N/A |
| glades_ikon_feb17 | Looking for tree skiing, have Ikon pass | ✓ | ✓ | 2/2 |
| beginner_family_jan29 | Taking my kids for their first ski lesson | ✓ | ✓ | 1/1 |
| skip_brutal_cold_jan08 | Worth skiing today? | ✓ | ✓ | N/A |
| skip_rainy_dec11 | Should I ski today? | ✓ | ✓ | N/A |
| skip_spring_slush_mar31 | Where should I ski today? | ✓ | ✓ | N/A |
| powder_epic_mar29 | Epic pass, where's the best snow today? | ✓ | ✓ | 1/1 |
| expert_terrain_mar29 | Want steep chutes and double blacks | ✓ | ✓ | 1/1 |
| ambiguous_feb03 | Best skiing today from Boston? | ✓ | ✓ | N/A |
| skip_prexmas_ice_dec22 | Ikon pass today? | ✓ | ✓ | N/A |
| skip_warm_rain_dec30 | Worth driving to ski today? | ✓ | ✓ | N/A |

### Failing Examples (1/16)

| Example | Query | Issue |
|---------|-------|-------|
| ambiguous_jan29 | Where should I ski today? | Hit@1 ✗, Hit@3 ✗. Pipeline recommended skipping, expected Gore/Jiminy/Killington/Stowe |

## Error Analysis

### ambiguous_jan29
- **Predicted**: Skip today (poor conditions)
- **Expected**: Gore Mountain, Jiminy Peak, Killington, or Stowe
- **Issue**: Pipeline was too conservative, recommending skipping when conditions were marginal but skiable. ReAct correctly recommends a mountain for this query.

## Evolution of Results

### v1b → v2b
- Hit@3: 87.5% → 93.8% (+6.3%)
- Fixed: `ambiguous_feb03` now correctly returns a top-3 pick

### Historical Context (pre-v1b)

Earlier versions had significantly lower performance before GEPA optimization and Pydantic fixes:

| Version | Hit@1 | Hit@3 | Key Change |
|---------|-------|-------|------------|
| v1 | 41.7% | - | Baseline |
| v2 | 58.3% | 75.0% | Pydantic fix (`pass_type='null'` bug) |
| v3 | 66.7% | 75.0% | GEPA optimization |
| v1b | 87.5% | 87.5% | New eval set with historic weather data |
| v2b | 87.5% | 93.8% | Minor improvements |

## Remaining Issues

1. **Over-conservative skip recommendations**: Pipeline sometimes recommends skipping when conditions are marginal but skiable (ReAct handles this better)

## Key Improvements

### GEPA Optimization Impact
- **AssessConditions**: Added "CRITICAL CONSTRAINTS" guidance that `stay_home` is NOT a valid output value
- **ReAct Agent**: Restored detailed instructions for prioritizing fresh snow, checking multiple mountains, and northern latitude preference
- **ScoreMountain**: Improved calibration for scoring powder days vs skip days
