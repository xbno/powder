# Powder — Live Demo Script

## **TODOs**

- **Re-branch `pre-gepa` from current `main`** — main has changed, need to re-strip the optimized JSONs
- **Test pre-gepa produces visibly bad output** on both demo queries (Feb 17, Jan 8)
- **Test main produces correct output** on both demo queries
- **Practice the `git checkout` flow** — branch switching should be smooth live
- **Dry run 1-2x end-to-end** with timing (~8 min demo target)

---

## Setup

```bash
cd ~/ml/powder
source .venv/bin/activate
```

---

## Demo Part 1: Single Signature Before/After (~3 min)

The AssessConditions signature looks at all mountains' weather and decides:
is today worth skiing? This is the prompt the engineer kept patching by hand.

### Step 1 — Before Optimization

Run with the original hand-written prompt:

```bash
git checkout pre-gepa
python -m powder --date 2025-02-17 --pipeline "Best powder with Ikon pass?"
```

Feb 17 was a clear powder day — Sugarloaf had 5.7" while the average was 1.2".
With the hand-written prompt, scores are off. The system is too generous with
mediocre mountains and the rankings don't match reality.

### Step 2 — After Optimization

Same query, same data, same model, same code. Only the prompt changed:

```bash
git checkout main
python -m powder --date 2025-02-17 --pipeline "Best powder with Ikon pass?"
```

Now the correct mountain wins, scores are calibrated, and the tradeoffs are honest.
The only thing that changed between these two runs is the prompt instructions inside
the AssessConditions and ScoreMountain signatures.

### Step 3 — The Diff

What exactly did the optimizer add to the prompt?

```bash
git diff pre-gepa main -- anyscale_presentation/prompts/assess_conditions.md
```

Everything in green was written by GEPA, not a human. Here's what it discovered:

**Bug fix — "stay_home" broke the pipeline:**
The original prompt listed `stay_home` as a valid day quality. But the downstream
pipeline only accepts `['fair', 'poor', 'good', 'excellent']`. When the LLM output
`stay_home` on bitter cold days (-15°F, 4" fresh, 20mph wind), parsing failed silently.
GEPA added: `"stay_home" is NOT a valid day_quality value. Use 'poor' instead.`

**Temperature edge case — 38-40°F with no snow:**
On the icy day eval (Gunstock at 38°F, Waterville at 40°F, both 0" fresh snow),
the hand-written prompt rated this "fair." It's not — warm temps with no fresh
snow means slushy, waterlogged conditions actively destroying the base.
GEPA added: `38-40°F with zero fresh snow = poor.`

**Small mountain bias — Nashoba over Killington:**
On powder days (14" at Stowe), the hand-written prompt gave Nashoba Valley inflated
scores despite 240ft vertical, 17 trails, and no glades. An advanced powder chaser
should never be sent there on a big snow day. GEPA learned to penalize small mountains
and added: `small mountains like 240 ft vertical limit exploration.`

5 iterations, ~$15. The engineer had been patching this prompt for weeks.

---

## Demo Part 2: Full Pipeline + Hard Cases (~5 min)

That was one signature. The app has four, wired together into a pipeline:

```text
ParseSkiQuery → search_mountains → get_conditions / get_drive_time
  → AssessConditions → ScoreMountain (×N) → check_crowd_level → GenerateRec
```

Each signature is independently optimizable. The tools (database, weather API,
routing) are regular functions shared across everything.

### Step 4a — Powder Day (Full Pipeline)

```bash
python -m powder --date 2025-02-17 --pipeline "Best powder with Ikon pass?"
```

Walk through each stage in the output:

- **PARSED QUERY** — extracted `ikon` pass and `powder_chase` vibe from plain English
- **DAY ASSESSMENT** — looked at every mountain's conditions, rated the day quality
- **MOUNTAIN SCORES** — each mountain scored individually with fresh snow, temp, drive time
- **RECOMMENDATION** — final pick with alternatives and caveats

### Step 4b — Skip Day (The Hard Test)

January 8th, 2025 was brutally cold with almost no fresh snow. This is the hardest
thing to get right — LLMs naturally want to be helpful and recommend *something*.

```bash
python -m powder --date 2025-01-08 --pipeline "Worth skiing today?"
```

The system says "don't go." Day quality is `poor`, all scores are below 55.
AssessConditions creates shared context that cascades through the whole pipeline —
when it says "poor day," every downstream score respects that.

Teaching an LLM to say "skip today" is what the hand-written prompt never got right.
GEPA figured it out from the labeled examples.

---

## Key Numbers

- **41.7% → 93.8% Hit@1** — same model, same code, same data, only prompts changed
- **47 labeled examples** across 4 signatures + 16 end-to-end tests
- **All deterministic metrics** — no LLM-as-judge
- **~$15** in optimizer cost over 5 iterations
