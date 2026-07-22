from datetime import datetime, timezone

from sentinel.agent import handle_alert


class _Row:
    def __init__(self, values):
        self._values = values
    def __getitem__(self, i):
        return self._values[i]


class _Cursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self._rows = rows or []
    def fetchone(self):
        return self.row
    def fetchall(self):
        return self._rows


_KNOWLEDGE_ROWS = [
    _Row(["u1", "postmortem", "Runaway analytical query exhausted connection pool", "Incident content...", 0.1]),
    _Row(["u2", "runbook", "Identify runaway high-latency queries", "Runbook content...", 0.2]),
]


class _FakeConn:
    def __init__(self):
        self.executes = []
        self.status = "open"
        self.hypothesis = None
        self.resolution = None

    def execute(self, sql, params=None):
        self.executes.append((sql, params))

        if "RETURNING id, status, created_at" in sql:
            return _Cursor(_Row(["inc-test-1", "open", datetime.now(timezone.utc)]))

        if sql.strip().startswith("SELECT status") and "incidents" in sql:
            return _Cursor(_Row([self.status]))

        if "UPDATE incidents SET status" in sql and params:
            self.status = params[0]

        if "FROM knowledge" in sql and "ORDER BY embedding" in sql:
            return _Cursor(None, _KNOWLEDGE_ROWS)

        if "UPDATE incidents SET" in sql and params:
            if "hypothesis" in sql:
                self.hypothesis = params[0]
            if "resolution" in sql:
                self.resolution = params[0] if len(params) > 1 and "hypothesis" not in sql else params[-2]

        return _Cursor(None)

    def commit(self):
        pass


def test_agent_loop_end_to_end(monkeypatch):
    monkeypatch.setattr(
        "sentinel.agent.diagnose",
        lambda signal: {"ping": {"ok": True, "rows": [{"ok": 1}]}},
    )
    monkeypatch.setattr(
        "sentinel.agent.control_plane",
        lambda signal=None: {"ok": True, "data": [{"id": "c1", "name": "test"}]},
    )
    conn = _FakeConn()
    signal = {
        "title": "P99 latency spike on transaction processing",
        "severity": "P1",
        "cluster_ref": "kooky-efreet",
        "details": {"metric": "p99_latency", "value": 30, "unit": "s"},
    }

    result = handle_alert(conn, signal)

    assert result["status"] == "resolved"
    assert result["hypothesis"] is not None
    assert len(result["recalled"]) >= 1

    events_kinds = []
    for sql, params in conn.executes:
        if "INSERT INTO incident_events" in sql:
            events_kinds.append(params[2] if params and len(params) >= 3 else None)

    updates = [p[0] for s, p in conn.executes if "UPDATE incidents SET status" in s and p]
    assert updates == ["diagnosing", "remediating", "resolved"], f"got {updates}"

    assert "observation" in events_kinds, f"no observation event in {events_kinds}"
    assert "decision" in events_kinds, f"no decision event in {events_kinds}"
    assert conn.hypothesis is not None
    assert conn.resolution is not None
