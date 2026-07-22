# Sentinel — Progress

Aligned with `PLAN.md`. Last updated: 2026-07-22. Repo HEAD: `250ace0`.

## Week 1 — Day 1 (Cockroach Cloud)

- [x] CockroachDB Cloud Basic cluster on AWS Mumbai (`kooky-efreet`)
- [x] `infra/schema.sql` applied (incidents, events, knowledge VECTOR(1024), agent_runs, tool_calls, cosine vector index)
- [x] `infra/apply_schema.py` helper
- [x] Read-only SQL user `sentinel_read` with SELECT grants
- [x] Local `.env` with `DATABASE_URL` (not committed)

## Week 1 — Day 3 (memory + recall)

- [x] `src/sentinel/config.py`, `db.py` (40001 retry), `embeddings.py` (fake + Bedrock Titan path), `memory.py` (state machine, audit, approval-before-destructive, `vector_recall`)
- [x] `infra/seed_runbooks.py` — 21 knowledge entries (incl. 3 demo postmortems); seeded on Cloud with fake embeddings
- [x] Offline tests green (16 passed)
- [x] `tests/test_recall.py` passes against live Cloud when `DATABASE_URL` is set (skips when unset)
- [x] Minimal `README.md` (Cloud setup / seed / recall)

## Scaffold / hygiene

- [x] `docker-compose.yml` (optional local CRDB — not used for Cloud path)
- [x] `.gitignore` ignores `.env` and orchestrator briefs
- [x] Public GitHub `main` pushed

## Week 1 — Day 2 (AWS) — partial

- [x] AWS account on Free Tier / Free Plan (~$100 credits)
- [x] Zero-spend budget template created
- [x] Bedrock working region `us-east-1` (in `.env`)
- [ ] Anthropic Claude model access (use-case form blocked) → fake LLM until unlocked
- [ ] Titan live embeddings + `EMBEDDINGS_BACKEND=bedrock`
- [ ] IAM access keys / `aws configure` for local Bedrock calls
- [ ] S3 bucket

## Week 1 — Day 4

- [x] `src/sentinel/llm.py` — Bedrock Claude wrapper **plus** fake LLM backend (default until Claude unlocks)
- [x] `src/sentinel/agent.py` — skeleton loop: open incident → embed/recall → reason → status transitions + audit
- [x] One scripted incident end-to-end (fake LLM OK)
- [x] Small runnable check / test for the loop

## Week 1 — Day 5

- [ ] Configure Cockroach Managed MCP (Cloud Console — needs human)
- [x] `tools/mcp_read.py` (read-only) using `sentinel_read` — SQL-via-psycopg stand-in for Managed MCP
- [x] Wire `diagnose(signal)` into `handle_alert` — runs after `set_status(diagnosing)`, feeds `live` key into `llm.plan`
- [ ] Wire into Cursor MCP (see note below)

> **Managed MCP status**: Cockroach Cloud Managed MCP registration requires Cloud Console access (human). The read path ships as a psycopg connection using `sentinel_read` credentials, guarded against mutating SQL. When Managed MCP becomes available, swap `tools/mcp_read.py` to use the MCP client — the `read_only_query` / `diagnose` surface stays the same.

## Week 2

- [x] `tools/ccloud.py` (allow-listed `cluster list` / `cluster info`; wired into agent as `control_plane` observation)
- [ ] `ccloud auth login` / service-account setup — needs human (Cloud Console)
- [x] Agent Skills integration (curated SQL, wired into agent investigate step, 4 skills)
- [x] Remediation Lambda (dry-run + allow-list) — local mode default; not deployed to AWS yet
- [x] Postmortem learning loop — `store_knowledge` in `memory.py`, `postmortem(ctx)` in `llm.py`, `write_postmortem` module wired into `handle_alert` resolve path; stores embedding in `knowledge` table; S3 artifact deferred
- [x] `tool_calls` logging wrapped via `timed_tool` helper for diagnose, control_plane, run_skills, llm.plan, remediate, write_postmortem; `start_agent_run` / `end_agent_run` in `memory.py`; soft-fail never breaks loop

## Week 3

- [ ] FastAPI UI (feed, SSE trace, audit, approval)
- [ ] Lambda ingest
- [ ] Deploy agent + UI (ECS Fargate / App Runner) → public demo URL

## Week 4

- [ ] Resilience / failover demo script
- [ ] README + architecture + tool/AWS writeup
- [ ] License visible in GitHub About
- [ ] <3 min demo video
- [ ] Submit by ~Aug 15 (deadline Aug 18)

## P0 / P1 / P2 cut-lines

- [ ] **P0** — schema + vector recall + Bedrock reasoning + one scripted incident + local UI (+ MCP)
- [ ] **P1** — ccloud + skills + postmortem loop + audit UI + live AWS URL
- [ ] **P2** — failover demo, approval gate, S3 artifacts, Lambda ingest/executor split

## Current working defaults

- [x] `EMBEDDINGS_BACKEND=fake`
- [x] LLM: fake until Claude is granted on Bedrock
- [x] Memory / DB: Cockroach Cloud via `DATABASE_URL`
