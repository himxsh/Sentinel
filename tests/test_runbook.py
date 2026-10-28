from sentinel.runbook import build_runbook, save_runbook


def test_build_runbook_marks_applied_and_held():
    signal = {"title": "Hot range imbalance", "severity": "P1", "cluster_ref": "kooky-efreet"}
    plan = {"hypothesis": "Sequential keys piled onto one range."}
    executed = []
    held = [
        {"cmd": "scatter_range", "impact": {"do": "Scatter the hot range.", "rollback": "Leave it."}},
    ]
    runbook = build_runbook(signal, plan, executed, held)
    assert runbook["title"] == "Runbook: Hot range imbalance"
    assert runbook["steps"][0]["status"] == "held"
    assert "scatter_range" in runbook["markdown"]
    assert "Nothing was applied" in runbook["markdown"]
    assert "Sequential keys" in runbook["markdown"]


def test_save_runbook_stores_generated_knowledge(monkeypatch):
    stored = {}

    monkeypatch.setattr("sentinel.runbook.embed", lambda text: [0.1])
    monkeypatch.setattr(
        "sentinel.runbook.store_knowledge",
        lambda conn, **kw: stored.update(kw) or "kid-rb",
    )
    monkeypatch.setattr("sentinel.runbook.log_event", lambda *a, **k: None)

    result = save_runbook(
        None,
        "inc-1",
        {"title": "Pool exhausted", "severity": "P1"},
        {"hypothesis": "A scan held the pool."},
        [{"cmd": "cancel_query", "impact": {"do": "Cancel it.", "rollback": "Retry."}}],
        [],
    )
    assert result["knowledge_id"] == "kid-rb"
    assert stored["source"] == "runbook"
    assert stored["metadata"]["generated"] is True
    assert stored["metadata"]["incident_id"] == "inc-1"
    assert result["steps"][0]["status"] == "applied"
