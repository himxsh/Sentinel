import json
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from sentinel.agent import handle_alert
from sentinel.db import execute
from sentinel.memory import log_event, record_action
from sentinel.tools.remediate import remediate

UI_DIR = Path(__file__).resolve().parent / "ui"
STATIC_DIR = UI_DIR / "static"

app = FastAPI(title="Sentinel")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/incidents")
def list_incidents():
    def _q(conn):
        cur = conn.execute(
            "SELECT id, title, severity, status, created_at "
            "FROM incidents ORDER BY created_at DESC LIMIT 50"
        )
        return [
            {
                "id": str(r[0]),
                "title": r[1],
                "severity": r[2],
                "status": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in cur.fetchall()
        ]

    return execute(_q)


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    def _q(conn):
        cur = conn.execute(
            "SELECT id, title, severity, status, hypothesis, resolution, "
            "created_at, updated_at FROM incidents WHERE id = %s",
            (incident_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        incident = {
            "id": str(r[0]),
            "title": r[1],
            "severity": r[2],
            "status": r[3],
            "hypothesis": r[4],
            "resolution": r[5],
            "created_at": r[6].isoformat() if r[6] else None,
            "updated_at": r[7].isoformat() if r[7] else None,
        }
        cur2 = conn.execute(
            "SELECT id, actor, kind, detail, ts FROM incident_events "
            "WHERE incident_id = %s ORDER BY ts ASC",
            (incident_id,),
        )
        incident["events"] = [
            {
                "id": str(e[0]),
                "actor": e[1],
                "kind": e[2],
                "detail": json.loads(e[3]) if isinstance(e[3], str) else e[3],
                "ts": e[4].isoformat() if e[4] else None,
            }
            for e in cur2.fetchall()
        ]
        return incident

    result = execute(_q)
    if result is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return result


@app.post("/api/incidents/{incident_id}/approve")
def approve_action(incident_id: str, body: dict = Body(default={})):
    action = body.get("action", {})

    def _q(conn):
        cur = conn.execute(
            "SELECT id, detail FROM incident_events "
            "WHERE incident_id = %s AND kind = 'approval' "
            "ORDER BY ts DESC LIMIT 1",
            (incident_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("no pending approval for this incident")

        detail = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        awaiting = detail.get("awaiting", {})

        log_event(conn, incident_id, "user", "approval", {"approved": action or awaiting})
        result = remediate(action or awaiting, dry_run=False, approved=True)
        record_action(conn, incident_id, {**(action or awaiting), "result": result}, destructive=True)
        return {"approved": True, "result": result}

    try:
        return execute(_q)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


# ponytail: sync handle_alert inside execute; async would need thread pool
@app.post("/api/alerts")
def ingest_alert(signal: dict = Body(...)):
    def _q(conn):
        return handle_alert(conn, signal)

    return execute(_q)


# ponytail: single-shot SSE — streams last 10 events then closes
@app.get("/api/incidents/{incident_id}/stream")
def stream_events(incident_id: str):
    def _q(conn):
        cur = conn.execute(
            "SELECT actor, kind, detail, ts FROM incident_events "
            "WHERE incident_id = %s ORDER BY ts DESC LIMIT 10",
            (incident_id,),
        )
        return [
            {
                "actor": e[0],
                "kind": e[1],
                "detail": json.loads(e[2]) if isinstance(e[2], str) else e[2],
                "ts": e[3].isoformat() if e[3] else None,
            }
            for e in cur.fetchall()
        ]

    events = execute(_q)

    def _gen():
        yield f"data: {json.dumps(events)}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@app.get("/")
def index():
    return FileResponse(UI_DIR / "index.html")


@app.get("/incidents")
def incidents_page():
    return FileResponse(UI_DIR / "incidents.html")


@app.get("/incidents/{incident_id}")
def incident_page(incident_id: str):
    return FileResponse(UI_DIR / "incident.html")
