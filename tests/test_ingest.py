import json

import pytest

from urllib.error import URLError

from lambdas.ingest.handler import handle


def test_normalize_defaults(monkeypatch):
    captured = {}

    def fake_execute(fn):
        return fn("fake_conn")

    def fake_handle_alert(conn, signal):
        captured["signal"] = signal
        return {"incident_id": "x", "run_id": "r", "status": "resolved"}

    monkeypatch.setattr("lambdas.ingest.handler.execute", fake_execute)
    monkeypatch.setattr("lambdas.ingest.handler.handle_alert", fake_handle_alert)

    handle({"details": {"cpu": 0.9}})

    assert captured["signal"]["title"] == "Alert"
    assert captured["signal"]["severity"] == "P3"
    assert captured["signal"]["details"] == {"cpu": 0.9}


def test_parse_body_string(monkeypatch):
    captured = {}

    def fake_execute(fn):
        return fn("fake_conn")

    def fake_handle_alert(conn, signal):
        captured["signal"] = signal
        return {"incident_id": "x", "run_id": "r", "status": "resolved"}

    monkeypatch.setattr("lambdas.ingest.handler.execute", fake_execute)
    monkeypatch.setattr("lambdas.ingest.handler.handle_alert", fake_handle_alert)

    handle({"body": json.dumps({"title": "parsed", "severity": "P1"})})

    assert captured["signal"]["title"] == "parsed"
    assert captured["signal"]["severity"] == "P1"


def test_normalize_override(monkeypatch):
    captured = {}

    def fake_execute(fn):
        return fn("fake_conn")

    def fake_handle_alert(conn, signal):
        captured["signal"] = signal
        return {"incident_id": "x", "run_id": "r", "status": "resolved"}

    monkeypatch.setattr("lambdas.ingest.handler.execute", fake_execute)
    monkeypatch.setattr("lambdas.ingest.handler.handle_alert", fake_handle_alert)

    handle({"title": "Custom", "severity": "P1", "details": {"region": "us-east-1"}})

    assert captured["signal"]["title"] == "Custom"
    assert captured["signal"]["severity"] == "P1"
    assert captured["signal"]["details"] == {"region": "us-east-1"}


def test_local_path(monkeypatch):
    expected = {"incident_id": "abc", "run_id": "def", "status": "resolved"}

    def fake_execute(fn):
        return fn("fake_conn")

    def fake_handle_alert(conn, signal):
        assert signal["title"] == "local-test"
        return expected

    monkeypatch.setattr("lambdas.ingest.handler.execute", fake_execute)
    monkeypatch.setattr("lambdas.ingest.handler.handle_alert", fake_handle_alert)

    result = handle({"title": "local-test"})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == expected


def test_remote_path(monkeypatch):
    monkeypatch.setenv("AGENT_URL", "http://localhost:9999")

    class FakeResponse:
        status = 200

        def read(self):
            return b'{"incident_id":"abc"}'

    def fake_urlopen(req, **kw):
        assert getattr(req, "method", "POST") == "POST"
        assert req.get_full_url() == "http://localhost:9999/api/alerts"
        assert req.data == json.dumps({"title": "remote-test", "severity": "P3", "details": {}}).encode()
        return FakeResponse()

    monkeypatch.setattr("lambdas.ingest.handler.urlopen", fake_urlopen)

    result = handle({"title": "remote-test"})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"incident_id": "abc"}


def test_remote_connection_error(monkeypatch):
    monkeypatch.setenv("AGENT_URL", "http://localhost:9999")

    def fake_urlopen(req, **kw):
        raise URLError("connection refused")

    monkeypatch.setattr("lambdas.ingest.handler.urlopen", fake_urlopen)

    result = handle({"title": "fail"})

    assert result["statusCode"] == 502
    assert "connection refused" in result["body"]


def test_invalid_json_body():
    result = handle({"body": "not-json"})
    assert result["statusCode"] == 500
