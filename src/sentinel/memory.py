from psycopg.types.json import Json

ALLOWED = {
    "open": {"diagnosing"},
    "diagnosing": {"remediating"},
    "remediating": {"resolved", "failed"},
}


class IllegalTransition(ValueError):
    pass


class ApprovalRequired(ValueError):
    pass


def open_incident(conn, *, title, severity, signal: dict, cluster_ref=None) -> dict:
    cur = conn.execute(
        "INSERT INTO incidents (title, severity, signal, cluster_ref) "
        "VALUES (%s, %s, %s, %s) RETURNING id, status, created_at",
        (title, severity, Json(signal), cluster_ref),
    )
    row = cur.fetchone()
    log_event(conn, row[0], "system", "observation", {"title": title, "severity": severity})
    return {"id": row[0], "status": row[1], "created_at": row[2]}


def set_status(conn, incident_id, new_status: str, *, actor="agent", detail=None) -> None:
    cur = conn.execute("SELECT status FROM incidents WHERE id = %s", (incident_id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"incident {incident_id} not found")
    current = row[0]
    if new_status not in ALLOWED.get(current, set()):
        raise IllegalTransition(f"{current} -> {new_status} not allowed")
    conn.execute(
        "UPDATE incidents SET status = %s, updated_at = now() WHERE id = %s",
        (new_status, incident_id),
    )
    log_event(conn, incident_id, actor, "decision", detail or {"from": current, "to": new_status})


def log_event(conn, incident_id, actor, kind, detail: dict) -> None:
    conn.execute(
        "INSERT INTO incident_events (incident_id, actor, kind, detail) VALUES (%s, %s, %s, %s)",
        (incident_id, actor, kind, Json(detail) if isinstance(detail, dict) else detail),
    )


def record_action(conn, incident_id, action: dict, *, destructive=False, actor="agent") -> None:
    if destructive:
        cur = conn.execute(
            "SELECT 1 FROM incident_events WHERE incident_id = %s AND kind = 'approval' LIMIT 1",
            (incident_id,),
        )
        if cur.fetchone() is None:
            raise ApprovalRequired(f"no approval for destructive action on {incident_id}")
    log_event(conn, incident_id, actor, "action", action)


def update_incident(conn, incident_id, **fields) -> None:
    allowed = {"hypothesis", "resolution", "title"}
    cols = [k for k in fields if k in allowed]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = %s" for c in cols) + ", updated_at = now()"
    vals = [fields[c] for c in cols] + [incident_id]
    conn.execute(f"UPDATE incidents SET {set_clause} WHERE id = %s", vals)


def vector_recall(conn, embedding: list[float], k=5) -> list[dict]:
    emb = "[" + ",".join(str(x) for x in embedding) + "]"
    cur = conn.execute(
        "SELECT id, source, title, content, embedding <=> %s::VECTOR AS distance "
        "FROM knowledge ORDER BY embedding <=> %s::VECTOR LIMIT %s",
        (emb, emb, k),
    )
    return [
        {"id": r[0], "source": r[1], "title": r[2], "content": r[3], "distance": r[4]}
        for r in cur.fetchall()
    ]
