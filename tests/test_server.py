from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from sentinel.server import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_index():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_list_incidents_empty(monkeypatch):
    monkeypatch.setattr("sentinel.server.execute", lambda fn: [])
    resp = client.get("/api/incidents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_incidents(monkeypatch):
    monkeypatch.setattr(
        "sentinel.server.execute",
        lambda fn: [
            {
                "id": "abc-123",
                "title": "P99 latency spike",
                "severity": "P1",
                "status": "open",
                "created_at": "2026-07-22T12:00:00+00:00",
            }
        ],
    )
    resp = client.get("/api/incidents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "P99 latency spike"


def test_get_incident_not_found(monkeypatch):
    monkeypatch.setattr("sentinel.server.execute", lambda fn: None)
    resp = client.get("/api/incidents/nonexistent")
    assert resp.status_code == 404


def test_get_incident(monkeypatch):
    monkeypatch.setattr(
        "sentinel.server.execute",
        lambda fn: {
            "id": "abc-123",
            "title": "Test",
            "severity": "P1",
            "status": "open",
            "hypothesis": None,
            "resolution": None,
            "created_at": "2026-07-22T12:00:00+00:00",
            "updated_at": None,
            "events": [],
        },
    )
    resp = client.get("/api/incidents/abc-123")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test"


def test_approve_calls_log_event(monkeypatch):
    events = []

    def fake_log_event(conn, incident_id, actor, kind, detail):
        events.append((actor, kind, detail))

    def fake_record_action(conn, incident_id, action, *, destructive=False, actor="agent"):
        pass

    monkeypatch.setattr("sentinel.server.log_event", fake_log_event)
    monkeypatch.setattr("sentinel.server.record_action", fake_record_action)
    monkeypatch.setattr("sentinel.server.remediate", lambda action, **kw: {"ok": True, "action": action})
    monkeypatch.setattr(
        "sentinel.server.execute",
        lambda fn: fn(_FakeConn("approval")),
    )

    resp = client.post("/api/incidents/abc-123/approve", json={"action": {"type": "restart_node"}})
    assert resp.status_code == 200
    assert resp.json()["approved"] is True
    assert any(a == "user" and k == "approval" for a, k, _ in events)


def test_ingest_alert(monkeypatch):
    calls = []

    def fake_handle_alert(conn, signal):
        calls.append(signal)
        return {"incident_id": "inc-1", "status": "resolved"}

    monkeypatch.setattr("sentinel.server.handle_alert", fake_handle_alert)
    monkeypatch.setattr("sentinel.server.execute", lambda fn: fn(None))

    resp = client.post("/api/alerts", json={"title": "test alert", "severity": "P1"})
    assert resp.status_code == 200
    assert resp.json()["incident_id"] == "inc-1"
    assert len(calls) == 1
    assert calls[0]["title"] == "test alert"


def test_sse_stream(monkeypatch):
    monkeypatch.setattr(
        "sentinel.server.execute",
        lambda fn: [
            {"actor": "agent", "kind": "observation", "detail": {"msg": "hi"}, "created_at": "2026-07-22T12:00:00"}
        ],
    )
    resp = client.get("/api/incidents/abc-123/stream")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert 'observation' in resp.text


class _FakeConn:
    def __init__(self, mode=None):
        self.mode = mode

    def execute(self, sql, params=None):
        if "approval" in sql:
            return _Cursor(_Row([1, '{"awaiting": {"type": "restart_node"}}']))
        return _Cursor(None)

    def commit(self):
        pass


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
