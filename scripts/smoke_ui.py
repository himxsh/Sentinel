"""Offline UI surface checks + optional live fire→timeline→postmortem smoke.

Offline (default): pages and static assets load.
Live (DATABASE_URL set): POST /api/alerts → incident has events + resolution.

  PYTHONPATH=src:. .venv/bin/python scripts/smoke_ui.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from sentinel.server import STATIC_DIR, UI_DIR, app


def check_static_files() -> None:
    assert (UI_DIR / "index.html").is_file()
    assert (UI_DIR / "incidents.html").is_file()
    assert (UI_DIR / "incident.html").is_file()
    assert (STATIC_DIR / "app.css").is_file()
    assert (STATIC_DIR / "app.js").is_file()
    # Interim inline HTML must be gone
    import sentinel.server as server_mod

    assert not hasattr(server_mod, "_HTML")


def check_pages(client: TestClient) -> None:
    for path in ("/", "/incidents", "/incidents/00000000-0000-0000-0000-000000000001"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "text/html" in r.headers["content-type"]
        assert "Sentinel" in r.text
    css = client.get("/static/app.css")
    assert css.status_code == 200
    js = client.get("/static/app.js")
    assert js.status_code == 200
    assert "fireDemoAlert" in js.text


def check_live_loop(client: TestClient) -> None:
    signal = {
        "title": "Smoke: runaway query for UI check",
        "severity": "P1",
        "cluster_ref": "kooky-efreet",
        "details": {"metric": "connection_pool_usage", "value": 0.95},
    }
    r = client.post("/api/alerts", json=signal)
    assert r.status_code == 200, r.text
    body = r.json()
    incident_id = body["incident_id"]
    assert body.get("status") == "resolved"

    detail = client.get(f"/api/incidents/{incident_id}")
    assert detail.status_code == 200
    inc = detail.json()
    assert len(inc.get("events") or []) > 0, "timeline empty"
    assert inc.get("resolution"), "expected postmortem/resolution"
    assert len(inc["resolution"]) > 10

    page = client.get(f"/incidents/{incident_id}")
    assert page.status_code == 200
    assert "Audit timeline" in page.text


def main() -> int:
    check_static_files()
    client = TestClient(app)
    check_pages(client)
    print("PASS offline UI smoke (pages + static + no _HTML)")

    if not os.environ.get("DATABASE_URL"):
        print("SKIP live loop (DATABASE_URL unset)")
        return 0

    check_live_loop(client)
    print("PASS live fire → timeline → postmortem")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
