(.venv) ➜  powder git:(main) ✗ python -m powder.evals.runner --mode both
/Users/xbno/.local/share/uv/python/cpython-3.10.17-macos-aarch64-none/lib/python3.10/runpy.py:126: RuntimeWarning: 'powder.evals.runner' found in sys.modules after import of package 'powder.evals', but prior to execution of 'powder.evals.runner'; this may result in unpredictable behaviour
  warn(RuntimeWarning(msg))

🎿 Powder Evaluation Suite
Model: anthropic/claude-haiku-4-5-20251001
Mode: both
Time: 2026-01-07T09:53:43.746082

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

  [powder_ikon_boston] Best powder day within 3 hours, I have Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/2

  [powder_epic_boston] Where should I ski today? Epic pass, don't mind dr...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [park_day_boston] Looking for the best terrain park, intermediate sn...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [beginner_family] Taking my kids for their first ski lesson, need gr...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 1/1
    Predicted: **Wachusett Mountain** – Best overall choice for a beginner'...
    Expected: ['Okemo', "Smugglers' Notch", 'Stratton', 'Waterville Valley']

  [night_skiing] Any mountains with night skiing tonight? Want to g...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [glade_skiing] Looking for tree skiing and glades, Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 2/2

  [short_drive] Quick trip, max 1.5 hour drive from Boston...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Predicted: **Stratton Mountain, VT** (2h 48min drive, 107 miles)

Strat...
    Expected: ['Nashoba Valley', 'Gunstock']
    Failed constraints: ['max_drive_hours']

  [expert_terrain] Want to hit some double blacks and steep chutes, a...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [icy_day_ikon] Where to ski today with Ikon pass?...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 1/1
    Predicted: **Loon Mountain, NH** – Best overall choice for MLK weekend....
    Expected: ['Killington', 'Sugarbush']

  [no_pass_powder] Best skiing today, willing to buy a day ticket...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Predicted: **Smugglers' Notch** is your best bet today. With 14 inches ...
    Expected: ['Jay Peak', 'Stowe']

  [indy_pass] Where can I use my Indy pass? Looking for good ter...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [nyc_powder_day] Best powder today from NYC, have Ikon pass...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 1/1
    Predicted: **Jay Peak** is your best powder choice today. With 16" of f...
    Expected: ['Killington', 'Stratton', 'Sugarbush']

  Summary: Hit@1: 58.3% | Hit@3: 75.0% | Constraints: 84.6% | Exclusions: 100.0% | Reasoning: 89.6%

============================================================
Evaluating: End-to-End ReAct Agent
============================================================

  [powder_ikon_boston] Best powder day within 3 hours, I have Ikon pass...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/2
    Response: **Top Recommendation: Stratton Mountain, Vermont**
- **Distance:** 172.5 km (~2....
    Expected: ['Jay Peak', 'Sugarbush', 'Killington']

  [powder_epic_boston] Where should I ski today? Epic pass, don't mind dr...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 0/1
    Response: **1. OKEMO (Ludlow, VT) — TOP CHOICE**
- **Distance**: 111 miles / ~2.5 hours fr...
    Expected: ['Stowe']

  [park_day_boston] Looking for the best terrain park, intermediate sn...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [beginner_family] Taking my kids for their first ski lesson, need gr...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Response: **Top Recommendation: Nashoba Valley (Littleton, MA)**
- **Distance:** 37.8 km /...
    Expected: ['Okemo', "Smugglers' Notch", 'Stratton', 'Waterville Valley']

  [night_skiing] Any mountains with night skiing tonight? Want to g...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [glade_skiing] Looking for tree skiing and glades, Ikon pass...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 0/2
    Response: **1. KILLINGTON, VT** ⭐ TOP PICK
- **Distance**: 199 km (2.5 hours from Boston)
...
    Expected: ['Jay Peak']

  [short_drive] Quick trip, max 1.5 hour drive from Boston...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [expert_terrain] Want to hit some double blacks and steep chutes, a...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [icy_day_ikon] Where to ski today with Ikon pass?...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Response: **Top Recommendation: Stratton, Vermont**
- **Distance/Drive Time**: 172.5 km (~...
    Expected: ['Killington', 'Sugarbush']

  [no_pass_powder] Best skiing today, willing to buy a day ticket...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: 0/1
    Response: **#1 RECOMMENDATION: Wachusett Mountain (MA) - 43 miles, ~1 hour drive**

Wachus...
    Expected: ['Jay Peak', 'Stowe']

  [indy_pass] Where can I use my Indy pass? Looking for good ter...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  [nyc_powder_day] Best powder today from NYC, have Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 0/1

  Summary: Hit@1: 50.0% | Hit@3: 66.7% | Constraints: 0.0% | Exclusions: 100.0% | Reasoning: 70.8%

============================================================
EVALUATION SUMMARY
============================================================

Signature Metrics (avg score):
  ParseSkiQuery             97.4% ███████████████████
  AssessConditions          93.8% ██████████████████
  ScoreMountain             92.5% ██████████████████
  GenerateRecommendation    100.0% ████████████████████

End-to-End Pipeline Metrics:
  Hit@1:                   58.3%
  Hit@3:                   75.0%
  Constraint Satisfaction: 84.6%
  Exclusion Check:         100.0%

End-to-End ReAct Metrics:
  Hit@1:                   50.0%
  Hit@3:                   66.7%
  Constraint Satisfaction: 0.0%
  Exclusion Check:         100.0%

--- Pipeline vs ReAct Comparison ---
  Metric                      Pipeline      ReAct
  ---------------------------------------------
  Hit@1                          58.3%      50.0%
  Hit@3                          75.0%      66.7%
  Constraint Satisfaction        84.6%       0.0%