# DSPy Presentation — Anyscale Panel Round

**Format:** 20 min total. 6 slides, demo in the middle. Framed as a customer story.

---

## Slide 1: Title + Agenda (30s)

**"DSPy: Programmatic LLM Optimization"**

Agenda:
1. An app with LLM quality problems
2. Why hand-tuning prompts couldn't fix it
3. DSPy + GEPA — a programmatic alternative
4. Live demo — before and after
5. What this means for your LLM stack

> "I'll keep slides light and spend most of our time in live code. Jump in with questions anytime."

---

## Slide 2: The App + The Problem (2.5 min)

**"We Built an App. It Worked... Mostly."**

> "A team built an app that recommends ski mountains. User asks 'best powder day with my Ikon pass?', the system checks real weather for 31 mountains, filters by pass type, scores each one, and gives a ranked recommendation. Four LLM calls, each with a hand-written prompt. They ship it. It works... mostly."

What went wrong:

1. **Users complain** — system recommends a 240-foot bunny hill over Killington on a powder day. Prompt didn't encode "bigger mountains are better for powder."
2. **Engineer patches** — adds vertical drop logic. Now 38°F with no snow gets rated "fair" instead of "poor."
3. **Whack-a-mole** — every fix breaks something else. No regression suite. Prompt is now 800 words.
4. **Model update** — switch providers, half the tuned phrasing stops working. Discovered in production.
5. **Engineer leaves** — nobody knows why line 47 says what it says.

Why this doesn't scale:
- No eval to catch regressions
- Expert feedback is slow and lossy
- Model changes silently shift behavior
- 10 features × 3 providers × quarterly updates = 30+ manual tuning loops/year

---

## Slide 3: DSPy — The Framework (2 min)

**"What If You Didn't Have to Write the Prompts?"**

LangChain/LlamaIndex let you chain LLM calls and plug in tools — but you still hand-write every prompt. DSPy keeps the composability but replaces hand-written prompts with something you can optimize programmatically.

Three building blocks:
- **Signature** — declare inputs and outputs. "Weather data in, day quality out." DSPy generates the prompt. This is what other frameworks make you write by hand.
- **Tool** — regular functions the LLM can call. Database, weather API, routing. Build once, reuse everywhere.
- **Module** — wire signatures and tools into a pipeline (you control the flow) or a ReAct agent (LLM controls the flow). Same parts, different architecture.

Plus: **Optimizer** — give it labeled examples, it finds better prompts. This is what no other framework does.

The shift: prompt engineering goes from vibes to a measurable practice. But your examples are everything — bad labels → bad prompts.

---

## Slide 4: GEPA — How the Optimizer Works (2 min)

**"How Do You Actually Optimize the Prompts?"**

GEPA (Genetic Evolution of Prompts and Assertions) — the optimizer that worked best for this app:

1. Start with a seed prompt + labeled examples with golden answers
2. Generate a batch of revised prompts
3. Eval each against the golden examples
4. Rank by performance
5. Keep top winners as seeds for next generation
6. Repeat

Key insight: the optimizer discovers edge cases you'd never think to write instructions for.

**Scaling note:** Step 3 — evaluating N prompt candidates across hundreds of examples — is embarrassingly parallel. Each candidate × example pair is independent. This is a perfect fit for Ray: fan out evaluations across workers, collect scores, feed winners into the next generation.

**"But I don't have labeled data yet":** Cold-start with a stronger model — use GPT-4o or Claude to generate initial golden answers, review them manually, use those as your seed examples.

**The production flywheel:** Today when a bug surfaces in prod, what happens? Someone copies it into a Jira ticket. An engineer eventually opens the prompt, manually tweaks it, maybe reruns the eval suite. If you're lucky the bug gets added to the evals — usually it doesn't. With DSPy, that bug becomes a labeled example that goes straight into the training set: the bad output is the hard negative, the correct output is the golden answer. Re-run the optimizer and every prompt in the system improves against it. The training set grows organically from production feedback instead of rotting in Jira tickets.

> "Let me show you what that looks like. Remember the ski app with the broken prompts? Here's what happens when we let the optimizer fix it."

---

## Demo Part 1: Single Signature Before/After (3 min)

The AssessConditions prompt looks at all mountains' weather and decides: is today worth skiing? This is the prompt the engineer kept patching.

1. **Pre-GEPA** — run with hand-written prompt. Scores are off, wrong mountains ranked high.
2. **Post-GEPA** — same query, same data, same model, same code. Only the prompt changed. Correct mountain wins, scores are calibrated.
3. **Show the diff** — everything in green was written by the optimizer:
   - Found a parsing bug ("stay_home" is not a valid output)
   - Found temperature edge cases (38-40°F with no snow = poor)
   - Added ranking logic the engineer never thought of
   - 5 iterations, ~$15

---

## Slide 5: Full Pipeline + Two Architectures (2 min)

**"Now Scale That Across 4 Signatures"**

That was one prompt. The app has four, wired together:

ParseSkiQuery → search mountains → get conditions/drive times → AssessConditions → ScoreMountain (×N) → GenerateRecommendation

Each signature independently optimizable. Tools are shared. You can also wire the same parts into a ReAct agent — LLM decides the execution order instead of you. Pipeline got 93.8%, ReAct got 87.5%. Same parts, different tradeoffs.

> "Let me show you the full pipeline."

---

## Demo Part 2: Full Pipeline + Hard Cases (5 min)

1. **Powder day** — full pipeline on Feb 17. Walk through each stage: parsed query → day assessment → scores → recommendation.
2. **Skip day** — Jan 8, brutally cold, no snow. The system says "don't go." All scores below 55. This is the hardest thing — LLMs want to recommend *something*. GEPA taught it not to.

> "Teaching an LLM to say 'skip today' is what the hand-written prompt never got right."

---

## Slide 6: Results + Close (2 min)

**41.7% → 93.8% Hit@1.** Same model, same code, same data. Only prompts changed.

The sustainable loop:
- Bad output in prod → add to examples → re-optimize → ship
- Model update → re-optimize against same examples → no rewrite

What this means:
- **Model portability** — re-optimize, don't rewrite
- **Quality at scale** — systematic > human intuition across 10+ features
- **Testability** — CI/CD for prompt quality
- **Agentic workflows** — each step independently optimizable

Next steps:
1. Pick 1-2 LLM features with known quality issues
2. Define eval metrics
3. Run DSPy optimization — measure before/after
4. Scale the pattern

> "What LLM challenges are you running into today?"

---

## Stretch Demos (if time)

**Run evals:**
- `make eval` — show the test suite running with deterministic metrics

---

## Notes

**Time management:**
- Slides 1-4: ~7 min
- Demo part 1: ~3 min
- Slide 5: ~2 min
- Demo part 2: ~5 min
- Slide 6: ~2 min
- Short on time: cut demo part 1, go straight to full pipeline
- Long on time: add stretch demos

**If asked about Anyscale/Ray:**
- GEPA's candidate evaluation is embarrassingly parallel → Ray
- Agentic on Ray: each agent step as a Serve actor, tool calls as tasks
- DSPy optimization is inherently data-driven → fits consumption model

**GEPA experience (for Q&A):**
- ~$15 over 5 iterations
- Only as good as your examples — bad labels → bad prompts
- Judgment signatures (Assess, Score) got heavy optimization; structural ones (Parse, Generate) stayed mostly the same
- Optimized prompts are surprisingly readable
