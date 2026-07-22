import json

from fastapi import Body, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from sentinel.agent import handle_alert
from sentinel.db import execute
from sentinel.memory import log_event, record_action
from sentinel.tools.remediate import remediate

app = FastAPI(title="Sentinel")


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
    return HTMLResponse(_HTML)


_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sentinel</title>
<style>
  body { font-family: system-ui, monospace; max-width: 960px; margin: 0 auto; padding: 16px; background: #0d1117; color: #c9d1d9; }
  h1, h2 { border-bottom: 1px solid #30363d; padding-bottom: 8px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 8px; border-bottom: 1px solid #21262d; }
  th { color: #8b949e; text-transform: uppercase; font-size: 12px; }
  .severity-P1 { color: #f85149; }
  .severity-P2 { color: #d29922; }
  .severity-P3 { color: #58a6ff; }
  .status { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; background: #21262d; }
  .status-open { border-left: 3px solid #f0883e; }
  .status-diagnosing { border-left: 3px solid #d29922; }
  .status-remediating { border-left: 3px solid #f85149; }
  .status-resolved { border-left: 3px solid #3fb950; }
  .status-failed { border-left: 3px solid #8b949e; }
  button { background: #238636; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
  button:hover { background: #2ea043; }
  button.danger { background: #da3633; }
  button.danger:hover { background: #f85149; }
  #detail { display: none; margin-top: 16px; }
  #detail.visible { display: block; }
  .event { padding: 8px; margin: 4px 0; background: #161b22; border-radius: 6px; font-size: 13px; }
  .event .kind { font-weight: bold; color: #58a6ff; }
  .event pre { white-space: pre-wrap; font-size: 12px; margin: 4px 0; color: #8b949e; }
  #alerts { margin: 16px 0; }
</style>
</head>
<body>
<h1>Sentinel</h1>
<div id="alerts">
  <button id="demoBtn" class="danger">Fire Demo Alert</button>
</div>
<h2>Incidents</h2>
<div id="loading">Loading...</div>
<table id="incidentsTbl"><thead><tr><th>ID</th><th>Title</th><th>Sev</th><th>Status</th><th>Created</th></tr></thead><tbody></tbody></table>
<div id="detail">
  <h2 id="detailTitle"></h2>
  <div id="detailBody"></div>
  <div id="approveArea"></div>
  <h3>Timeline</h3>
  <div id="timeline"></div>
</div>
<script>
const BASE = '';
async function loadIncidents() {
  const r = await fetch(BASE+'/api/incidents');
  const data = await r.json();
  const tbody = document.querySelector('#incidentsTbl tbody');
  tbody.innerHTML = data.map(i => '<tr onclick="showDetail('+JSON.stringify(i.id)+')">'
    +'<td>'+i.id.slice(0,8)+'</td>'
    +'<td>'+esc(i.title)+'</td>'
    +'<td class="severity-'+i.severity+'">'+i.severity+'</td>'
    +'<td><span class="status status-'+i.status+'">'+i.status+'</span></td>'
    +'<td>'+i.created_at.slice(0,10)+'</td></tr>').join('');
  document.getElementById('loading').style.display='none';
}
function esc(s) { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
async function showDetail(id) {
  const r = await fetch(BASE+'/api/incidents/'+id);
  const i = await r.json();
  document.getElementById('detail').className='visible';
  document.getElementById('detailTitle').textContent = i.title;
  let body = '<p><strong>Status:</strong> '+i.status+' | <strong>Severity:</strong> '+i.severity+'</p>';
  if(i.hypothesis) body += '<p><strong>Hypothesis:</strong> '+esc(i.hypothesis)+'</p>';
  if(i.resolution) body += '<p><strong>Resolution:</strong> '+esc(i.resolution)+'</p>';
  document.getElementById('detailBody').innerHTML = body;
  const approveArea = document.getElementById('approveArea');
  const hasApproval = i.events && i.events.some(e => e.kind === 'approval');
  if(hasApproval) {
    approveArea.innerHTML = '<button onclick="approve('+JSON.stringify(id)+')">Approve Destructive Action</button>';
  } else {
    approveArea.innerHTML = '';
  }
  const tl = document.getElementById('timeline');
  tl.innerHTML = (i.events||[]).map(e => '<div class="event">'
    +'<span class="kind">'+esc(e.kind)+'</span> by '+esc(e.actor)
    +' <span class="ts">'+e.ts.slice(0,19)+'</span>'
    +'<pre>'+esc(JSON.stringify(e.detail,null,2))+'</pre></div>').join('');
}
async function approve(id) {
  const r = await fetch(BASE+'/api/incidents/'+id+'/approve', {method:'POST',headers:{'Content-Type':'application/json'}, body:'{}'});
  const data = await r.json();
  if(data.approved) showDetail(id);
  else alert('Approve failed: '+JSON.stringify(data));
}
document.getElementById('demoBtn').onclick = async function(){
  document.getElementById('demoBtn').disabled=true;
  document.getElementById('demoBtn').textContent='Firing...';
  const r = await fetch(BASE+'/api/alerts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    title:'Runaway analytical query exhausting connection pool',
    severity:'P1',
    cluster_ref:'kooky-efreet',
    details:{metric:'connection_pool_usage',value:0.95,unit:'percent',query:'SELECT COUNT(*) FROM large_table CROSS JOIN another_table'}
  })});
  const data = await r.json();
  document.getElementById('demoBtn').disabled=false;
  document.getElementById('demoBtn').textContent='Fire Demo Alert';
  await loadIncidents();
  if(data.incident_id) showDetail(data.incident_id);
};
loadIncidents();
</script>
</body>
</html>
"""
