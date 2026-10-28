# Features

Three agent behaviors that were not in the product before, and a replay on the case page so a demo can walk through them. The audit list, the boolean dry-run, and the destructive-only approval were already here. These sit on top of that loop.

## Similar-incident explanations

**Idea.** Vector recall returned a title and a distance. It did not say why that lesson belonged to this alert.

**Why it matters.** An on-call engineer, and a hackathon judge, should be able to disagree with the memory. A shared word plus a distance band is a reason. "No shared keywords, kept as a neighbor" is also a reason. The agent does not pretend a near vector is an analogy when the words do not overlap.

**What was built.** `explain_matches` in `src/sentinel/recall.py`. Keyword overlap (words of four or more characters, SQL glue ignored) plus a distance band: near under 0.15, related under 0.35, otherwise loose. The first audit observation stores `recalled` beside `recalled_titles`. The case page shows them under "Why these cases."

**Demo.** Fire the runaway-query alert. Open the case. Read the why line on each recalled title. In replay, stop on the beat that starts with "Recalled."

## Blast radius and cost before apply

**Idea.** Dry-run echoed the command. "Destructive" was a boolean, so a scatter that moves ranges on every node could run on its own.

**Why it matters.** The failure mode worth showing is the change that looks safe and is not. Sentinel prices every step before it applies anything, and holds the step when the blast radius is high, the estimate is over $50 a month, the dry-run failed, or the step is marked destructive.

**What was built.** `estimate_impact` and `needs_approval` in `src/sentinel/impact.py`. The agent always dry-runs first, logs the estimate on the case, and skips the apply when the gate holds. Approval walks held steps in plan order, so a second hold stays visible after you approve the first. The prices are a static rate card, not a Cockroach invoice. The ceiling is noted in the module: swap in live RU counts from `diagnose()` when that payload is trustworthy.

Held even when `destructive` is false:

- `scatter_range`: cluster scope, about $42/month, high risk. Held for the blast radius, not the dollar cap.
- `enable_random_uuids`: changes how new primary keys are generated.
- `reprovision_node`: about $90/month, over the $50 auto-apply cap.

`cancel_query` and `recommend_index` stay automatic. Their estimates still show, at $0.

The fake planner classifies the alert text first. A recalled latency runbook no longer hides a hot-range alert.

**Demo.** Fire the hot-range alert (home page on Next.js, or "Fire hot-range alert" on the FastAPI home page). The case lists both steps as waiting, with scope, dollars, and the reason. Approve `scatter_range`, then approve `enable_random_uuids`. Fire the runaway-query alert to see the same panel say "Clear to apply" and then actually apply.

## Runbook from the case that just closed

**Idea.** Postmortems are prose. The seeded runbooks are static. Nothing turned this incident's real steps into the next procedure.

**Why it matters.** The following recall can hit a runbook that says what already ran, what is still held, what to check, and how to undo it.

**What was built.** `build_runbook` and `save_runbook` in `src/sentinel/runbook.py`. The markdown is stored in `knowledge` with `source=runbook` and `metadata.generated=true`, and the steps are logged on the case. The case page renders them under "Runbook." Applied steps and held steps are labeled differently.

**Demo.** After either alert settles, read the runbook on the case. The runaway query marks its steps Applied. The hot-range case marks them Held until you approve.

## Replay the night

**Idea.** The audit timeline was a list. Replay is those same events, one narrated beat at a time, with the current row highlighted.

**Why it matters.** It is the thing you press in a demo. Remember, price, hold or apply, file.

**What was built.** `replay_beats` in `src/sentinel/replay.py`. `GET /api/incidents/{id}` includes `replay`. Play, Back, and Next are on the Next.js case page and on the FastAPI incident page. The highlight index matches the audit row.

**Demo.** Open a settled case. Press Play. The sentence and the highlighted row move together. Back and Next step one beat without waiting.

## Run it

Agent:

```bash
PYTHONPATH=src:. .venv/bin/uvicorn sentinel.server:app --reload
```

Next.js:

```bash
cd web && npm install && npm run dev
```

Open http://localhost:3000 or http://127.0.0.1:8000. Both home pages can fire the runaway query and the hot-range alert.

Tests:

```bash
PYTHONPATH=src:. .venv/bin/pytest tests -q
cd web && npm run check && npm run build
```
