from types import SimpleNamespace

from sentinel.postmortem import write_postmortem


def _base_mocks(monkeypatch):
    monkeypatch.setattr("sentinel.llm.postmortem", lambda ctx: {
        "title": "Postmortem: Test incident",
        "content": "Root cause: something broke",
        "summary": "Fixed the thing",
    })
    monkeypatch.setattr("sentinel.postmortem.embed", lambda t: [0.1] * 1024)
    monkeypatch.setattr("sentinel.postmortem.store_knowledge", lambda conn, **kw: "kid-1")
    monkeypatch.setattr("sentinel.postmortem.log_event", lambda *a, **kw: None)


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


def test_write_postmortem_s3(monkeypatch):
    _base_mocks(monkeypatch)
    put_calls = []
    put_error = []

    class FakeS3:
        def put_object(self, **kw):
            if put_error:
                raise RuntimeError("no creds")
            put_calls.append(kw)

    monkeypatch.setattr("sentinel.postmortem.boto3.client", lambda service, **kw: FakeS3())

    def with_bucket(bucket):
        return lambda: SimpleNamespace(s3_bucket=bucket, aws_region="us-east-1")

    monkeypatch.setattr("sentinel.postmortem.get_settings", with_bucket("sentinel-bucket"))
    result = write_postmortem(None, "inc-1", {"signal": {"title": "Test"}})
    assert result["knowledge_id"] == "kid-1"
    assert len(put_calls) == 1
    assert put_calls[0]["Bucket"] == "sentinel-bucket"
    assert put_calls[0]["Key"] == "postmortems/inc-1.md"
    assert put_calls[0]["ContentType"] == "text/markdown"

    monkeypatch.setattr("sentinel.postmortem.get_settings", with_bucket(""))
    write_postmortem(None, "inc-2", {"signal": {"title": "Test"}})
    assert len(put_calls) == 1

    put_error.append(True)
    monkeypatch.setattr("sentinel.postmortem.get_settings", with_bucket("sentinel-bucket"))
    result = write_postmortem(None, "inc-3", {"signal": {"title": "Test"}})
    assert result["knowledge_id"] == "kid-1"
