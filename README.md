# Sentinel

Autonomous database-reliability agent using CockroachDB as persistent memory.

## Architecture (short)

Alert → FastAPI agent loop → CockroachDB memory (incidents + audit events + vector knowledge). Demo UI is static HTML/CSS/JS served by the same FastAPI app (`src/sentinel/ui/`). Fake LLM/embeddings are the default until Bedrock unlocks.

```
Browser  →  /  /incidents  /incidents/{id}  (product UI)
         →  /api/*  /health               (JSON + SSE)
Agent    →  recall → diagnose → plan → remediate → postmortem → knowledge
```

```mermaid
flowchart LR
    Alert[Incident alert] --> Agent[FastAPI agent loop<br/>src/sentinel/server.py]
    Agent --> CRDB[(CockroachDB Cloud<br/>incidents · incident_events ·<br/>knowledge VECTOR(1024) · agent_runs · tool_calls)]
    Agent --> Tools[Tools]
    Tools --> Read[read-only SQL path —<br/>Managed MCP stand-in]
    Tools --> CCloud[ccloud CLI<br/>cluster list / cluster info]
    Tools --> Skills[4 curated SQL skills]
    Agent --> PM[Postmortem]
    PM --> S3[(S3<br/>postmortems/)]
    Agent -.-> Bedrock[Bedrock wrappers<br/>code path, not live]
    Agent -.-> Lambda[Lambda handlers<br/>in repo, not deployed]
```

Fake backends are first-class: `EMBEDDINGS_BACKEND=fake` / `LLM_BACKEND=fake` are the defaults and everything (recall, postmortems, tests) runs on them — no AWS needed until Bedrock unlocks.

## CockroachDB tools

- **Distributed Vector Indexing** — live. `knowledge` stores VECTOR(1024) embeddings behind a cosine-distance index; recall runs ANN queries inside CockroachDB (`src/sentinel/memory.py`).
- **Managed MCP (stand-in)** — the read path (`src/sentinel/tools/mcp_read.py`) executes SELECT/SHOW SQL over psycopg as the `sentinel_read` user. It mirrors what Cockroach Managed MCP would expose; a local stand-in until that service is live.
- **ccloud CLI** — `src/sentinel/tools/ccloud.py` runs `cluster list` / `cluster info` for control-plane observations. Command allow-listed; soft-fails if the binary or auth is missing.
- **Agent Skills** — `src/sentinel/tools/skills.py` ships four curated SQL skills inspired by the Agent Skills repo (triaging-live-sql-activity, analyzing-range-distribution, profiling-statement-fingerprints, monitoring-background-jobs — thin runners, not vendored SKILL.md). The agent picks skills from the alert signal and runs their queries on the read path.

## AWS services

- **S3** — postmortem markdown uploads to `sentinel-artifacts-951532862171-us-east-1` under `postmortems/{incident_id}.md` when `S3_BUCKET` is set. Soft-fails: upload errors never break the agent loop.
- **Bedrock** — wrappers for Titan embeddings and Claude LLM exist (`embeddings.py`, `llm.py`) but are NOT live: this account's Bedrock access is blocked until Support unlocks quotas. `fake` backends are the default.
- **Lambda** — remediation handlers exist under `lambdas/` but are not deployed; local remediation (`REMEDIATE_MODE=local`) is the default.
- **Containers** — Dockerfile at repo root; deploy notes in `infra/deploy.md`. Not deployed.

## CockroachDB Cloud setup

1. **Connection string** — set `DATABASE_URL` in `.env` (see `.env.example`). Uses TLS (`sslmode=verify-full`).

2. **Apply schema**
   ```
   .venv/bin/python -m infra.apply_schema
   ```

3. **Read-only SQL user** (for MCP read path)
   ```sql
   CREATE USER IF NOT EXISTS sentinel_read WITH PASSWORD '<password>';
   GRANT SELECT ON TABLE knowledge, incidents, incident_events, agent_runs, tool_calls TO sentinel_read;
   ```
   Credentials go in `SENTINEL_READ_USER` / `SENTINEL_READ_PASSWORD` in `.env`.

4. **Seed knowledge**
   ```
   EMBEDDINGS_BACKEND=fake .venv/bin/python -m infra.seed_runbooks
   ```
   Uses fake deterministic embeddings (no AWS needed). Switch `EMBEDDINGS_BACKEND=bedrock` for real Titan v2.

5. **Vector recall test**
   ```
   DATABASE_URL=... EMBEDDINGS_BACKEND=fake .venv/bin/pytest tests/test_recall.py -v
   ```
   Without `DATABASE_URL`, the test skips automatically.

6. **ccloud CLI** (optional — for control-plane observations)
   - See `infra/ccloud_setup.md` for service-account + API key setup.
   - Set `CCLOUD_BIN` in `.env` if `ccloud` is not on `PATH`.

7. **Run server** (local product UI)
   ```
   .venv/bin/uvicorn sentinel.server:app --reload
   ```
   Then open http://127.0.0.1:8000/
   - `/` — brand + fire demo alert
   - `/incidents` — feed
   - `/incidents/{id}` — detail, audit timeline, live poll + SSE, approve CTA

   Next.js demo (plain-language UI in `web/`):
   ```
   cd web && npm install && npm run dev
   ```
   Open http://localhost:3000. It proxies `/api/*` to the FastAPI agent. See `web/README.md`.

8. **Offline tests** (no DB required)
   ```
   .venv/bin/pytest tests/ -v
   ```

9. **UI smoke** (offline always; live loop when `DATABASE_URL` is set)
   ```
   .venv/bin/python scripts/smoke_ui.py
   DATABASE_URL=... .venv/bin/python scripts/smoke_ui.py   
   ```

10. **Demo incident** (requires `DATABASE_URL`)
    ```
    .venv/bin/python scripts/demo_incident.py
    ```

11. **AWS** — S3 bucket + Bedrock status: `infra/aws_setup.md`. Keep `EMBEDDINGS_BACKEND=fake` / `LLM_BACKEND=fake` until Bedrock quotas are non-zero. Container deploy notes: `infra/deploy.md` (Dockerfile at repo root — do not deploy without credentials).

12. **Resilience check** (requires `DATABASE_URL`; connection-fault fallback for Basic clusters)
    ```
    ./scripts/resilience_demo.sh
    ```
