import pytest

from sentinel.memory import record_action, log_event, ApprovalRequired


class _Row:
    def __getitem__(self, i):
        return 1


class _Cursor:
    def __init__(self, row=None):
        self.row = row
    def fetchone(self):
        return self.row
    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, has_approval=False):
        self.executes = []
        self._has_approval = has_approval
    def execute(self, sql, params=None):
        self.executes.append((sql, params))
        if "RETURNING id" in sql:
            return _Cursor(_Row())
        return _Cursor(_Row() if self._has_approval and "approval" in sql else None)
    def commit(self):
        pass


def test_destructive_without_approval_raises():
    c = _FakeConn(has_approval=False)
    with pytest.raises(ApprovalRequired):
        record_action(c, "inc-1", {"cmd": "restart"}, destructive=True)


def test_destructive_after_approval_succeeds():
    c = _FakeConn(has_approval=True)
    log_event(c, "inc-1", "human", "approval", {"approved": True})
    record_action(c, "inc-1", {"cmd": "restart"}, destructive=True)
    approvals = [p for s, p in c.executes if "approval" in s]
    assert len(approvals) >= 1  # at least the SELECT approval check ran


def test_non_destructive_no_approval_needed():
    c = _FakeConn(has_approval=False)
    record_action(c, "inc-1", {"cmd": "describe"}, destructive=False)
    # no exception = success


def test_log_event_sanitizes_datetime():
    from datetime import datetime, timezone

    c = _FakeConn()
    now = datetime.now(timezone.utc)
    log_event(c, "inc-1", "agent", "observation", {
        "skills": {"triaging-live-sql-activity": {"queries": [{"rows": [{"start": now}]}]}},
    })
    detail = c.executes[-1][1][3]
    assert detail.obj["skills"]["triaging-live-sql-activity"]["queries"][0]["rows"][0]["start"] == str(now)


def test_store_knowledge_sanitizes_uuid_metadata():
    from uuid import uuid4

    from sentinel.memory import store_knowledge

    c = _FakeConn()
    kid = uuid4()
    store_knowledge(
        c,
        source="postmortem",
        title="t",
        content="c",
        embedding=[0.1] * 4,
        metadata={"incident_id": kid},
    )
    meta = c.executes[-1][1][3]
    assert meta.obj["incident_id"] == str(kid)


def test_store_knowledge():
    from sentinel.memory import store_knowledge
    c = _FakeConn(has_approval=False)
    kid = store_knowledge(c, source="postmortem", title="Test",
                          content="Content", embedding=[0.1, 0.2, 0.3],
                          metadata={"incident_id": "inc-1"})
    assert kid == "1"
    assert any("INSERT INTO knowledge" in s for s, _ in c.executes)
    insert_sql = next(s for s, _ in c.executes if "INSERT INTO knowledge" in s)
    assert "RETURNING id" in insert_sql


def test_start_agent_run():
    from sentinel.memory import start_agent_run
    c = _FakeConn()
    run_id = start_agent_run(c, incident_id="inc-1")
    assert run_id == "1"
    assert any("INSERT INTO agent_runs" in s for s, _ in c.executes)


def test_end_agent_run():
    from sentinel.memory import end_agent_run
    c = _FakeConn()
    end_agent_run(c, "run-1", status="done")
    assert any("UPDATE agent_runs" in s for s, _ in c.executes)


def test_log_tool_call_records_latency_and_ok():
    from sentinel.memory import log_tool_call
    c = _FakeConn()
    log_tool_call(c, "run-1", "diagnose", {"signal": "test"}, {"ok": True}, True, 42)
    inserts = [(s, p) for s, p in c.executes if "INSERT INTO tool_calls" in s]
    assert len(inserts) == 1
    assert inserts[0][1][0] == "run-1"
    assert inserts[0][1][1] == "diagnose"
    assert inserts[0][1][4] is True
    assert inserts[0][1][5] == 42


def test_log_tool_call_skips_when_run_id_none():
    from sentinel.memory import log_tool_call
    c = _FakeConn()
    log_tool_call(c, None, "diagnose", {}, {}, True, 0)
    assert not any("INSERT INTO tool_calls" in s for s, _ in c.executes)


def test_timed_tool_success(monkeypatch):
    from sentinel.memory import timed_tool, log_tool_call
    c = _FakeConn()
    calls = []
    monkeypatch.setattr("sentinel.memory.log_tool_call", lambda *a: calls.append(a))
    result = timed_tool(c, "run-1", "ping", {"input": "x"}, lambda: "pong")
    assert result == "pong"
    assert len(calls) == 1
    _, run_id, tool, args, result_val, ok, latency = calls[0]
    assert run_id == "run-1"
    assert tool == "ping"
    assert ok is True
    assert result_val == "pong"
    assert isinstance(latency, int)


def test_timed_tool_failure(monkeypatch):
    from sentinel.memory import timed_tool
    c = _FakeConn()
    calls = []
    monkeypatch.setattr("sentinel.memory.log_tool_call", lambda *a: calls.append(a))
    with pytest.raises(RuntimeError, match="boom"):
        timed_tool(c, "run-1", "fail", {}, lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert len(calls) == 1
    _, _, _, _, _, ok, _ = calls[0]
    assert ok is False


def test_timed_tool_skips_when_run_id_none(monkeypatch):
    from sentinel.memory import timed_tool
    c = _FakeConn()
    calls = []
    monkeypatch.setattr("sentinel.memory.log_tool_call", lambda *a: calls.append(a))
    result = timed_tool(c, None, "ping", {}, lambda: "pong")
    assert result == "pong"
    assert len(calls) == 0


def test_log_tool_call_sanitizes_datetime(monkeypatch):
    from datetime import datetime, timezone
    from sentinel.memory import log_tool_call
    c = _FakeConn()
    now = datetime.now(timezone.utc)
    log_tool_call(c, "run-1", "diagnose", {"ts": now}, {"rows": [{"ts": now}]}, True, 10)
    assert any("INSERT INTO tool_calls" in s for s, _ in c.executes)
