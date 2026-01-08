(.venv) ➜  powder git:(main) ✗ make eval
.venv/bin/python -m powder.evals.runner
/Users/xbno/.local/share/uv/python/cpython-3.10.17-macos-aarch64-none/lib/python3.10/runpy.py:126: RuntimeWarning: 'powder.evals.runner' found in sys.modules after import of package 'powder.evals', but prior to execution of 'powder.evals.runner'; this may result in unpredictable behaviour
  warn(RuntimeWarning(msg))

🎿 Powder Evaluation Suite
Model: anthropic/claude-haiku-4-5-20251001
Mode: pipeline
Time: 2026-01-07T19:13:15.521400

============================================================
Evaluating: ParseSkiQuery
============================================================

  Average: 97.4% (12/12 passed)

============================================================
Evaluating: AssessConditions
============================================================
  [✗] Example 2: 0.33
      Query/Input: {'all_candidates': '[{"name": "Gunstock", "state": "NH", "conditions": {"fresh_s...

  Average: 83.3% (3/4 passed)

============================================================
Evaluating: ScoreMountain
============================================================

  Average: 93.8% (8/8 passed)

============================================================
Evaluating: GenerateRecommendation
============================================================

  Average: 100.0% (7/7 passed)

============================================================
Evaluating: End-to-End Pipeline
============================================================

  [powder_ikon_feb17] Best powder today? I have an Ikon pass....
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [powder_no_pass_jan02] Where has the best snow today? Don't care about pa...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [powder_south_vt_dec10] Best skiing within 3 hours of Boston?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [nyc_powder_mar29] Best powder today from NYC?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [park_day_jan02] I want to hit rails and jumps tomorrow...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [glades_ikon_feb17] Looking for tree skiing, have Ikon pass...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 2/2

  [beginner_family_jan29] Taking my kids for their first ski lesson...
    Hit@1: ✗ | Hit@3: ✓ | Constraints: 1/1
    Predicted: **Nashoba Valley** – Go for it, but manage expectations.

Th...
    Expected: ['Okemo', "Smugglers' Notch", 'Bretton Woods', 'Stratton']

  [ambiguous_jan29] Where should I ski today?...
    Hit@1: ✗ | Hit@3: ✗ | Constraints: N/A
    Predicted: **Skip today.** Day quality is poor across the entire region...
    Expected: ['Gore Mountain', 'Jiminy Peak', 'Killington', 'Stowe']

  [skip_brutal_cold_jan08] Worth skiing today?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [skip_rainy_dec11] Should I ski today?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [skip_spring_slush_mar31] Where should I ski today?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [powder_epic_mar29] Epic pass, where's the best snow today?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [expert_terrain_mar29] Want steep chutes and double blacks...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: 1/1

  [ambiguous_feb03] Best skiing today from Boston?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [skip_prexmas_ice_dec22] Ikon pass today?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  [skip_warm_rain_dec30] Worth driving to ski today?...
    Hit@1: ✓ | Hit@3: ✓ | Constraints: N/A

  Summary: Hit@1: 87.5% | Hit@3: 93.8% | Constraints: 100.0% | Exclusions: 100.0% | Reasoning: 80.1%

============================================================
EVALUATION SUMMARY
============================================================

Signature Metrics (avg score):
  ParseSkiQuery             97.4% ███████████████████
  AssessConditions          83.3% ████████████████
  ScoreMountain             93.8% ██████████████████
  GenerateRecommendation    100.0% ████████████████████

End-to-End Pipeline Metrics:
  Hit@1:                   87.5%
  Hit@3:                   93.8%
  Constraint Satisfaction: 100.0%
  Exclusion Check:         100.0%