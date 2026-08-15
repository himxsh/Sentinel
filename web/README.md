# Sentinel web demo

Plain-language Next.js UI for the hackathon demo. It talks to the FastAPI agent already in this repo.

## Run

In one terminal, start the agent:

```bash
.venv/bin/uvicorn sentinel.server:app --reload
```

In another:

```bash
cd web
cp .env.example .env.local   # optional; defaults to http://127.0.0.1:8000
npm install
npm run dev
```

Open http://localhost:3000

- `/` fire a demo alert
- `/incidents` case list
- `/incidents/[id]` case, conclusion, audit timeline, approve if needed

The Next server proxies `/api/*` to `SENTINEL_API_URL` (default `http://127.0.0.1:8000`).
