# Powder Evaluation Results

Evaluation of the ski recommendation pipeline using deterministic metrics (no LLM-as-judge).

## Model & Configuration

- **Model**: Claude Haiku (claude-haiku-4-5-20251001)
- **Mountains**: 30 Northeast US resorts
- **Eval Examples**: 39 labeled examples across 4 signatures + 16 end-to-end
- **Optimization**: GEPA (Reflective Prompt Evolution)
- **Date**: January 2026

## Current Performance (v2b)

### Signature-Level Metrics

| Signature | Score | Status |
|-----------|-------|--------|
| ParseSkiQuery | 97.4% | 12/12 passed |
| AssessConditions | 83.3% | 3/4 passed |
| ScoreMountain | 93.8% | 8/8 passed |
| GenerateRecommendation | 100.0% | 7/7 passed |

### End-to-End Pipeline Metrics

| Metric | v1b | v2b | Change |
|--------|-----|-----|--------|
| **Hit@1** | 87.5% | 87.5% | - |
| **Hit@3** | 87.5% | **93.8%** | +6.3% |
| **Constraint Satisfaction** | 100.0% | 100.0% | - |
| **Exclusion Check** | 100.0% | 100.0% | - |

## End-to-End Detailed Results (v2b)

### Passing Examples (14/16)

| Example | Query | Hit@1 | Hit@3 | Constraints |
|---------|-------|-------|-------|-------------|
| powder_ikon_feb17 | Best powder today? I have an Ikon pass | ✓ | ✓ | 1/1 |
| powder_no_pass_jan02 | Where has the best snow today? | ✓ | ✓ | N/A |
| powder_south_vt_dec10 | Best skiing within 3 hours of Boston? | ✓ | ✓ | 1/1 |
| nyc_powder_mar29 | Best powder today from NYC? | ✓ | ✓ | N/A |
| park_day_jan02 | I want to hit rails and jumps tomorrow | ✓ | ✓ | N/A |
| glades_ikon_feb17 | Looking for tree skiing, have Ikon pass | ✓ | ✓ | 2/2 |
| skip_brutal_cold_jan08 | Worth skiing today? | ✓ | ✓ | N/A |
| skip_rainy_dec11 | Should I ski today? | ✓ | ✓ | N/A |
| skip_spring_slush_mar31 | Where should I ski today? | ✓ | ✓ | N/A |
| powder_epic_mar29 | Epic pass, where's the best snow today? | ✓ | ✓ | 1/1 |
| expert_terrain_mar29 | Want steep chutes and double blacks | ✓ | ✓ | 1/1 |
| ambiguous_feb03 | Best skiing today from Boston? | ✓ | ✓ | N/A |
| skip_prexmas_ice_dec22 | Ikon pass today? | ✓ | ✓ | N/A |
| skip_warm_rain_dec30 | Worth driving to ski today? | ✓ | ✓ | N/A |

### Failing Examples (2/16)

| Example | Query | Issue |
|---------|-------|-------|
| beginner_family_jan29 | Taking my kids for their first ski lesson | Hit@1 ✗, Hit@3 ✓. Picked Nashoba Valley, expected Okemo/Smugglers'/Bretton Woods/Stratton |
| ambiguous_jan29 | Where should I ski today? | Hit@1 ✗, Hit@3 ✗. Recommended skipping, expected Gore/Jiminy/Killington/Stowe |

## Error Analysis

### beginner_family_jan29
- **Predicted**: Nashoba Valley
- **Expected**: Okemo, Smugglers' Notch, Bretton Woods, or Stratton
- **Issue**: Pipeline prioritized proximity over learning area quality. Nashoba is close to Boston but the expected mountains have "excellent" learning_area_quality ratings.

### ambiguous_jan29
- **Predicted**: Skip today (poor conditions)
- **Expected**: Gore Mountain, Jiminy Peak, Killington, or Stowe
- **Issue**: Pipeline was too conservative, recommending skipping when conditions were marginal but skiable. The expected mountains had acceptable conditions for the day.

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

1. **Proximity bias for beginners**: Pipeline picks nearby mountains over those with better learning facilities
2. **Over-conservative skip recommendations**: Pipeline sometimes recommends skipping when conditions are marginal but skiable

## Signature Failure Details

### AssessConditions (83.3%)
- Example 2 failed with score 0.33
- Input involved Gunstock conditions assessment
