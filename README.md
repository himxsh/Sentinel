# Sentinel

Autonomous database-reliability agent using CockroachDB as persistent memory.

## Architecture (short)

Alert → FastAPI agent loop → CockroachDB memory (incidents + audit events + vector knowledge). Demo UI is static HTML/CSS/JS served by the same FastAPI app (`src/sentinel/ui/`). Fake LLM/embeddings are the default until Bedrock unlocks.

```
Browser  →  /  /incidents  /incidents/{id}  (product UI)
         →  /api/*  /health               (JSON + SSE)
Agent    →  recall → diagnose → plan → remediate → postmortem → knowledge
```

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
