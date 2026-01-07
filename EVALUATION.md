# Powder Evaluation Results

Baseline evaluation of the ski recommendation agent using deterministic metrics (no LLM-as-judge).

## Model & Configuration

- **Model**: Claude Haiku (claude-haiku-4-5-20251001)
- **Mountains**: 30 Northeast US resorts
- **Eval Examples**: 39 labeled examples across 4 signatures + 12 end-to-end
- **Date**: January 2026

## Signature-Level Performance

Individual DSPy signatures perform well in isolation:

| Signature | Score | Examples |
|-----------|-------|----------|
| ParseSkiQuery | 98.3% | 12/12 |
| AssessConditions | 93.8% | 3/4 |
| ScoreMountain | 92.5% | 7/8 |
| GenerateRecommendation | 100% | 7/7 |

The LLM correctly:
- Parses natural language queries into structured filters
- Assesses weather conditions and day quality
- Scores mountains based on conditions and preferences
- Generates coherent recommendations with reasoning

## End-to-End Performance

### Pipeline vs ReAct Comparison

| Metric | Pipeline | ReAct |
|--------|----------|-------|
| **Hit@1** | 41.7% | 50.0% |
| **Hit@3** | 41.7% | 66.7% |
| **Constraint Satisfaction** | 53.8% | 0.0%* |
| **Exclusion Check** | 100% | 100% |

*ReAct constraint metric is a measurement artifact - the unstructured output isn't being parsed correctly.

### Key Finding

The gap between signature-level (93-100%) and end-to-end (42-67%) performance indicates integration issues, not component issues. The pieces work; the wiring needs improvement.

## Error Analysis

### Pipeline: "No Mountains Found" Bug

6 of 12 examples returned "No mountains found matching your criteria":

| Example | Filter Issue |
|---------|--------------|
| park_day_boston | terrain_parks filter |
| beginner_family | beginner_terrain filter |
| night_skiing | night_skiing filter |
| short_drive | max_drive_hours filter |
| expert_terrain | expert_terrain filter |
| no_pass_powder | no pass type filter |

**Root Cause**: Database query combines filters with AND logic, becoming too restrictive. Individual filters may also have bugs (e.g., distance calculation, boolean field matching).

### ReAct: Proximity Bias

ReAct avoids the "No mountains found" issue by flexibly choosing which tools to call. However, it tends to prioritize proximity over snow conditions:

- `powder_ikon_boston`: Picked Stratton (closer) over Jay Peak (more snow)
- `beginner_family`: Picked Nashoba Valley (closest) over better learning mountains
- `no_pass_powder`: Picked Wachusett (closest) over powder destinations

**Root Cause**: Without explicit scoring logic, ReAct optimizes for the most obvious factor (distance) rather than balancing multiple criteria.

### Successful Cases

Both approaches succeeded on:
- `glade_skiing` (Pipeline) - Ikon + glades filter worked
- `indy_pass` - Pass type filter worked
- `nyc_powder_day` - Different origin city worked

## Recommendations

### High Priority

1. **Fix Pipeline DB Query Filters**
   - Debug why filter combinations return empty results
   - Test each filter in isolation vs combination
   - Consider OR logic for some filter types

2. **Review Ground Truth**
   - Some expected answers may be too narrow
   - Add multiple acceptable answers for subjective queries

### Medium Priority

3. **Fix ReAct Constraint Measurement**
   - Parse pass type mentions from unstructured text
   - Extract drive time claims for validation

4. **Add Scoring to ReAct**
   - Give ReAct a scoring tool to compare mountains systematically
   - Reduce proximity bias

### Future Work

5. **DSPy Optimization**
   - Use GEPA or MIPROv2 to optimize signatures
   - Train/dev split: 30 train / 9 dev examples
   - Target: Improve Hit@1 from 42% to 70%+

6. **Historic Backtesting**
   - Use real weather fixtures (136 days × 30 mountains)
   - Find interesting days for additional eval examples
   - Test against known powder days, cold days, etc.

## Raw Results

### Pipeline Detailed Results

```
[powder_ikon_boston]  ✓ Hit@1  ✓ Hit@3  Constraints: 1/2
[powder_epic_boston]  ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
[park_day_boston]     ✗ Hit@1  ✗ Hit@3  "No mountains found"
[beginner_family]     ✗ Hit@1  ✗ Hit@3  "No mountains found"
[night_skiing]        ✗ Hit@1  ✗ Hit@3  "No mountains found"
[glade_skiing]        ✓ Hit@1  ✓ Hit@3  Constraints: 2/2
[short_drive]         ✗ Hit@1  ✗ Hit@3  "No mountains found"
[expert_terrain]      ✗ Hit@1  ✗ Hit@3  "No mountains found"
[icy_day_ikon]        ✗ Hit@1  ✗ Hit@3  Picked Stratton (expected Killington/Sugarbush)
[no_pass_powder]      ✗ Hit@1  ✗ Hit@3  "No mountains found"
[indy_pass]           ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
[nyc_powder_day]      ✓ Hit@1  ✓ Hit@3  Constraints: 1/1
```

### ReAct Detailed Results

```
[powder_ikon_boston]  ✗ Hit@1  ✗ Hit@3  Picked Stratton (expected Jay Peak)
[powder_epic_boston]  ✗ Hit@1  ✓ Hit@3  Picked Okemo (expected Stowe)
[park_day_boston]     ✓ Hit@1  ✓ Hit@3  Found terrain parks
[beginner_family]     ✗ Hit@1  ✗ Hit@3  Picked Nashoba (expected Okemo/Smugglers')
[night_skiing]        ✓ Hit@1  ✓ Hit@3  Found night skiing
[glade_skiing]        ✗ Hit@1  ✓ Hit@3  Picked Killington (expected Jay Peak)
[short_drive]         ✓ Hit@1  ✓ Hit@3  Found close mountains
[expert_terrain]      ✓ Hit@1  ✓ Hit@3  Found expert terrain
[icy_day_ikon]        ✗ Hit@1  ✗ Hit@3  Picked Stratton (expected Killington)
[no_pass_powder]      ✗ Hit@1  ✗ Hit@3  Picked Wachusett (expected Jay Peak)
[indy_pass]           ✓ Hit@1  ✓ Hit@3  Found Indy pass mountains
[nyc_powder_day]      ✓ Hit@1  ✓ Hit@3  Correct from NYC
```

## Conclusion

The baseline reveals a classic integration gap: components work well individually (93%+) but struggle when combined (42-67%). The Pipeline approach is more constrained and predictable but fails when filters are too strict. The ReAct approach is more flexible but makes suboptimal choices without explicit scoring guidance.

Priority fix: Debug the database query filters to eliminate "No mountains found" failures, which would likely improve Pipeline Hit@1 from 42% to 70%+.
