# Live Demo Script

## Setup (do before presentation)

```bash
cd ~/ml/powder
git checkout main
source .venv/bin/activate
```

---

## Step 1 — Run the optimized pipeline (powder day)

> "Let's start with what the optimized system looks like.
> February 17th was a big powder day in the Northeast."

```bash
.venv/bin/python -m powder --date 2025-02-17 --pipeline "Best powder with Ikon pass?"
```

Walk through the output: parsed query, conditions, scores, final pick.

---

## Step 2 — Run the optimized pipeline (skip day)

> "Now the hard test — what happens when every mountain has terrible conditions?
> January 8th was brutally cold, almost no fresh snow."

```bash
.venv/bin/python -m powder --date 2025-01-08 --pipeline "Worth skiing today?"
```

Point out: the system says "don't go." LLMs naturally want to recommend *something* —
getting them to say "skip today" is the hardest part of the problem.

---

## Step 3 — Switch to the un-optimized branch

> "That was with GEPA-optimized prompts. Let me show you what happens
> with just the hand-written prompts — same code, same model, same data."

```bash
git checkout pre-gepa
```

---

## Step 4 — Run the same queries without optimization

```bash
.venv/bin/python -m powder --date 2025-02-17 --pipeline "Best powder with Ikon pass?"
```

> "Notice the differences — scores are off, ranking may be wrong,
> the system is too generous with mediocre mountains."

```bash
.venv/bin/python -m powder --date 2025-01-08 --pipeline "Worth skiing today?"
```

> "And on the skip day — does it still tell you to stay home,
> or does it try to recommend something anyway?"

---

## Step 5 — Show the diff

> "So what actually changed? Let me show you exactly what
> the optimizer discovered and added to the prompts."

```bash
git diff pre-gepa main -- anyscale_presentation/prompts/assess_conditions.md
```

> "Everything in green was written by GEPA, not a human.
> It found a parsing bug, temperature edge cases, and ranking logic
> that a human might take weeks to discover through user complaints."

```bash
git diff pre-gepa main -- anyscale_presentation/prompts/score_mountain.md
```

> "The scoring prompt went from 19 lines to 71 lines.
> GEPA added input/output specs, contextual boosts, a 6-step decision
> framework, and tone guidance — all from analyzing failures."

---

## Step 6 — Switch back and run evals

```bash
git checkout main
```

```bash
.venv/bin/python -m powder.evals.runner
```

> "This is the eval harness — deterministic metrics, no LLM-as-judge.
> 47 labeled examples across 4 signatures plus 16 end-to-end tests.
> This is what makes it a testable, measurable system instead of prompt vibes."

---

## Talking points between steps

**After Step 2** — "The skip-day detection is powered by the AssessConditions
signature. It creates shared context that cascades through the whole pipeline.
If it says 'poor day,' every downstream score respects that."

**After Step 4** — "Same model, same code, same data. The only difference
is the prompt instructions. That's the whole thesis — prompts are the weights
of your LLM program, and you should optimize them systematically."

**After Step 5** — "A human prompt engineer might eventually find all of these.
But GEPA found them in 5 iterations for about $15. And it found them from
failures in labeled examples — not from gut feel."

**After Step 6** — "This eval suite is what makes DSPy practical in production.
You can run this in CI. When you swap models, you re-optimize and re-eval.
No more 'we changed the prompt and hope it still works.'"
