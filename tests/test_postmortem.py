from sentinel.postmortem import write_postmortem


def test_write_postmortem_stores_knowledge(monkeypatch):
    store_calls = []

    monkeypatch.setattr("sentinel.llm.postmortem", lambda ctx: {
        "title": "Postmortem: Test incident",
        "content": "Root cause: something broke",
        "summary": "Fixed the thing",
    })
    monkeypatch.setattr("sentinel.postmortem.embed", lambda t: [0.1] * 1024)
    monkeypatch.setattr("sentinel.postmortem.store_knowledge", lambda conn, **kw: (
        store_calls.append(kw) or "kid-1"
    ))
    monkeypatch.setattr("sentinel.postmortem.log_event", lambda *a, **kw: None)

    result = write_postmortem(None, "inc-1", {"signal": {"title": "Test"}})

    assert result["knowledge_id"] == "kid-1"
    assert result["summary"] == "Fixed the thing"
    assert len(store_calls) == 1
    assert store_calls[0]["source"] == "postmortem"
    assert store_calls[0]["title"] == "Postmortem: Test incident"
    assert store_calls[0]["metadata"]["incident_id"] == "inc-1"
