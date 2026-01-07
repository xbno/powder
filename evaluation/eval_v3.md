(.venv) ➜  powder git:(main) ✗ python -m powder.evals.runner --mode both
/Users/xbno/.local/share/uv/python/cpython-3.10.17-macos-aarch64-none/lib/python3.10/runpy.py:126: RuntimeWarning: 'powder.evals.runner' found in sys.modules after import of package 'powder.evals', but prior to execution of 'powder.evals.runner'; this may result in unpredictable behaviour
  warn(RuntimeWarning(msg))

🎿 Powder Evaluation Suite
Model: anthropic/claude-haiku-4-5-20251001
Mode: both
Time: 2026-01-07T11:17:15.899763

============================================================
Evaluating: ParseSkiQuery
============================================================

  Average: 97.4% (12/12 passed)

============================================================
Evaluating: AssessConditions
============================================================
  [✗] Example 4: 0.75
      Query/Input: {'all_candidates': '[{"name": "Sugarloaf", "state": "ME", "conditions": {"fresh_...

  Average: 93.8% (3/4 passed)

============================================================
Evaluating: ScoreMountain
============================================================
  [✗] Example 2: 0.70
      Query/Input: {'mountain': '{"name": "Killington", "state": "VT", "lat": 43.6045, "lon": -72.8...

  Average: 92.5% (7/8 passed)

============================================================
Evaluating: GenerateRecommendation
============================================================

  Average: 100.0% (7/7 passed)

============================================================
Evaluating: End-to-End Pipeline
============================================================
2026/01/07 11:17:16 WARNING dspy.primitives.base_module: There is a mismatch of dspy version between saved model and current environment. You saved with `dspy==3.0.4`, but now you have `dspy==3.1.0`. This might cause errors or performance downgrade on the loaded model, please consider loading the model in the same environment as the saving environment.
2026/01/07 11:17:16 WARNING dspy.primitives.base_module: There is a mismatch of dspy version between saved model and current environment. You saved with `dspy==3.0.4`, but now you have `dspy==3.1.0`. This might cause errors or performance downgrade on the loaded model, please consider loading the model in the same environment as the saving environment.
2026/01/07 11:17:16 WARNING dspy.primitives.base_module: There is a mismatch of dspy version between saved model and current environment. You saved with `dspy==3.0.4`, but now you have `dspy==3.1.0`. This might cause errors or performance downgrade on the loaded model, please consider loading the model in the same environment as the saving environment.

  [powder_ikon_boston] Best powder day within 3 hours, I have Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 2/2

  [powder_epic_boston] Where should I ski today? Epic pass, don't mind dr...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [park_day_boston] Looking for the best terrain park, intermediate sn...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [beginner_family] Taking my kids for their first ski lesson, need gr...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 1/1
    Predicted: **Stowe Mountain Resort** is your best choice for your kids'...
    Expected: ['Okemo', "Smugglers' Notch", 'Stratton', 'Waterville Valley']

  [night_skiing] Any mountains with night skiing tonight? Want to g...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [glade_skiing] Looking for tree skiing and glades, Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 2/2

  [short_drive] Quick trip, max 1.5 hour drive from Boston...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Predicted: **Mount Snow** is the pragmatic top pick for your quick 1.5-...
    Expected: ['Nashoba Valley', 'Gunstock']
    Failed constraints: ['max_drive_hours']

  [expert_terrain] Want to hit some double blacks and steep chutes, a...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [icy_day_ikon] Where to ski today with Ikon pass?...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 1/1
    Predicted: **Skip today or ski locally if you must.** This is a poor-qu...
    Expected: ['Killington', 'Sugarbush']

  [no_pass_powder] Best skiing today, willing to buy a day ticket...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Predicted: **Smugglers' Notch** is your best choice today. With 14" of ...
    Expected: ['Jay Peak', 'Stowe']

  [indy_pass] Where can I use my Indy pass? Looking for good ter...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [nyc_powder_day] Best powder today from NYC, have Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  Summary: Hit@1: 66.7% | Hit@3: 75.0% | Constraints: 92.3% | Exclusions: 100.0% | Reasoning: 90.3%

============================================================
Evaluating: End-to-End ReAct Agent (GEPA-Optimized)
============================================================

  [powder_ikon_boston] Best powder day within 3 hours, I have Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/2

  [powder_epic_boston] Where should I ski today? Epic pass, don't mind dr...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 0/1
    Response: **Top Recommendation #1: Okemo Mountain Resort, VT**
- **Distance & Drive Time**...
    Expected: ['Stowe']

  [park_day_boston] Looking for the best terrain park, intermediate sn...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [beginner_family] Taking my kids for their first ski lesson, need gr...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [night_skiing] Any mountains with night skiing tonight? Want to g...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [glade_skiing] Looking for tree skiing and glades, Ikon pass...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 0/2
    Response: **1. KILLINGTON, VT** (Top Pick for Maximum Glade Terrain)
- **Distance & Drive ...
    Expected: ['Jay Peak']

  [short_drive] Quick trip, max 1.5 hour drive from Boston...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [expert_terrain] Want to hit some double blacks and steep chutes, a...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [icy_day_ikon] Where to ski today with Ikon pass?...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Response: **1. STRATTON MOUNTAIN, Bondville, VT** ⭐ TOP PICK FOR TODAY
- **Distance & Driv...
    Expected: ['Killington', 'Sugarbush']

  [no_pass_powder] Best skiing today, willing to buy a day ticket...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [indy_pass] Where can I use my Indy pass? Looking for good ter...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [nyc_powder_day] Best powder today from NYC, have Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  Summary: Hit@1: 75.0% | Hit@3: 91.7% | Constraints: 0.0% | Exclusions: 100.0% | Reasoning: 77.8%

============================================================
EVALUATION SUMMARY
============================================================

Signature Metrics (avg score):
  ParseSkiQuery             97.4% ███████████████████
  AssessConditions          93.8% ██████████████████
  ScoreMountain             92.5% ██████████████████
  GenerateRecommendation    100.0% ████████████████████

End-to-End Pipeline Metrics:
  Hit@1:                   66.7%
  Hit@3:                   75.0%
  Constraint Satisfaction: 92.3%
  Exclusion Check:         100.0%

End-to-End ReAct Metrics (GEPA-Optimized):
  Hit@1:                   75.0%
  Hit@3:                   91.7%
  Constraint Satisfaction: 0.0%
  Exclusion Check:         100.0%

--- Pipeline vs ReAct Comparison ---
  Metric                      Pipeline      ReAct
  ---------------------------------------------
  Hit@1                          66.7%      75.0%
  Hit@3                          75.0%      91.7%
  Constraint Satisfaction        92.3%       0.0%

Note: ReAct improved from 50% → 75% Hit@1 after GEPA optimization with enable_tool_optimization=True.
Constraint Satisfaction is 0% for ReAct because the metric cannot parse constraints from unstructured text.