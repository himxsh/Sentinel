import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

DEFAULTS = {"title": "Alert", "severity": "P3", "details": {}}


def _normalize(raw: dict) -> dict:
    signal = DEFAULTS.copy()
    signal.update(raw)
    return signal


def _parse_event(event: dict) -> dict:
    body = event.get("body") if "body" in event else event
    if body is None:
        return event
    if isinstance(body, str):
        return json.loads(body)
    return body


def handle(event: dict, context=None) -> dict:
    try:
        raw = _parse_event(event)
        signal = _normalize(raw)
        agent_url = os.environ.get("AGENT_URL")
        if agent_url:
            return _remote(agent_url, signal)
        return _local(signal)
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def _remote(agent_url: str, signal: dict) -> dict:
    req = Request(
        f"{agent_url.rstrip('/')}/api/alerts",
        data=json.dumps(signal).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urlopen(req)
        body = resp.read().decode()
        return {"statusCode": resp.status, "body": body}
    except URLError as e:
        status = e.code if hasattr(e, "code") and e.code else 502
        return {"statusCode": status, "body": json.dumps({"error": str(e)})}


# ponytail: local path reuses execute/handle_alert like server.py;
#            per-account pool if ingest volume grows
def _local(signal: dict) -> dict:
    from sentinel.agent import handle_alert as ha
    from sentinel.db import execute

    def _q(conn):
        return ha(conn, signal)

    result = execute(_q)
    return {"statusCode": 200, "body": json.dumps(result)}
