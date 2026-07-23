#!/usr/bin/env bash
# Prove CockroachDB memory survives a connection-level fault mid-incident.
# Basic / free Cloud clusters often cannot node-kill; this is the documented fallback
# (see PLAN.md risks): drop the client connection, reconnect, assert zero data loss.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
exec .venv/bin/python - <<'PY'
"""Connection-fault resilience check for Sentinel memory."""
from __future__ import annotations

import sys

from sentinel.config import get_settings
from sentinel.db import get_pool
from sentinel.memory import log_event, open_incident
import sentinel.db as db


def main() -> int:
    if not get_settings().database_url:
        print("DATABASE_URL required (via env or .env)", file=sys.stderr)
        return 1

    pool = get_pool()

    with pool.connection() as conn:
        incident = open_incident(
            conn,
            title="Resilience demo: connection fault mid-incident",
            severity="P2",
            signal={
                "title": "Resilience demo",
                "severity": "P2",
                "cluster_ref": "kooky-efreet",
                "details": {"kind": "connection_fault"},
            },
            cluster_ref="kooky-efreet",
        )
        incident_id = incident["id"]
        log_event(
            conn,
            incident_id,
            "agent",
            "observation",
            {"phase": "before_fault", "note": "persisted before connection drop"},
        )
        conn.commit()
        print(f"opened incident {incident_id}")

    # Simulate mid-incident client/network failure: tear down the pool.
    pool.close()
    print("connection pool closed (simulated fault)")

    db._pool = None
    pool2 = get_pool()

    with pool2.connection() as conn:
        row = conn.execute(
            "SELECT id, title, status FROM incidents WHERE id = %s",
            (incident_id,),
        ).fetchone()
        if row is None:
            print("FAIL: incident row missing after reconnect", file=sys.stderr)
            return 1

        events = conn.execute(
            "SELECT kind, detail FROM incident_events WHERE incident_id = %s ORDER BY ts",
            (incident_id,),
        ).fetchall()
        if not events:
            print("FAIL: incident_events empty after reconnect", file=sys.stderr)
            return 1

        log_event(
            conn,
            incident_id,
            "agent",
            "observation",
            {"phase": "after_fault", "events_before": len(events)},
        )
        conn.commit()

        after = conn.execute(
            "SELECT count(*) FROM incident_events WHERE incident_id = %s",
            (incident_id,),
        ).fetchone()[0]

    print(f"incident intact: id={row[0]} status={row[2]}")
    print(f"events intact: {after} (had {len(events)} before resume write)")
    print("PASS: zero data loss across connection fault")
    pool2.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
