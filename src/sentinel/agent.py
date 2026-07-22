from sentinel.embeddings import embed
from sentinel import llm
from sentinel.memory import (
    log_event,
    open_incident,
    record_action,
    set_status,
    update_incident,
    vector_recall,
)
from sentinel.tools.ccloud import control_plane
from sentinel.tools.mcp_read import diagnose
from sentinel.tools.remediate import remediate
from sentinel.tools.skills import run_skills


def handle_alert(conn, signal: dict) -> dict:
    incident = open_incident(
        conn,
        title=signal.get("title", "Alert"),
        severity=signal.get("severity", "P3"),
        signal=signal,
        cluster_ref=signal.get("cluster_ref"),
    )
    incident_id = incident["id"]

    emb = embed(str(signal))
    memories = vector_recall(conn, emb, k=5)
    log_event(conn, incident_id, "agent", "observation", {
        "recalled_titles": [m["title"] for m in memories],
    })

    set_status(conn, incident_id, "diagnosing")

    live = diagnose(signal)
    log_event(conn, incident_id, "agent", "observation", {"live_diagnostics": live})

    control = control_plane(signal)
    log_event(conn, incident_id, "agent", "observation", {"control_plane": control})

    skills = run_skills(signal)
    log_event(conn, incident_id, "agent", "observation", {"skills": skills})

    plan = llm.plan({"signal": signal, "memories": memories, "live": live, "control": control, "skills": skills})
    update_incident(conn, incident_id, hypothesis=plan["hypothesis"])
    log_event(conn, incident_id, "agent", "decision", {
        "hypothesis": plan["hypothesis"],
        "summary": plan["summary"],
    })

    set_status(conn, incident_id, "remediating")

    for action in plan["actions"]:
        if action.get("destructive"):
            log_event(conn, incident_id, "agent", "approval", {"awaiting": action})
            continue
        dry = remediate(action, dry_run=True)
        log_event(conn, incident_id, "agent", "observation", {"dry_run": dry})
        result = remediate(action, dry_run=False, approved=False)
        record_action(conn, incident_id, {**action, "result": result}, destructive=False)

    set_status(conn, incident_id, "resolved")
    update_incident(conn, incident_id, resolution=plan["summary"])

    return {
        "incident_id": incident_id,
        "status": "resolved",
        "hypothesis": plan["hypothesis"],
        "recalled": [m["title"] for m in memories],
        "plan": plan,
    }
