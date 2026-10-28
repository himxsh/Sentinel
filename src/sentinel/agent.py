from sentinel.embeddings import embed
from sentinel import llm
from sentinel.impact import estimate_impact, needs_approval
from sentinel.memory import (
    end_agent_run,
    log_event,
    open_incident,
    record_action,
    set_status,
    start_agent_run,
    timed_tool,
    update_incident,
    vector_recall,
)
from sentinel.postmortem import write_postmortem
from sentinel.recall import explain_matches
from sentinel.runbook import save_runbook
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
    run_id = start_agent_run(conn, incident_id=incident_id)
    failed = False

    try:
        emb = embed(str(signal))
        memories = vector_recall(conn, emb, k=5)
        explained = explain_matches(signal, memories)
        log_event(conn, incident_id, "agent", "observation", {
            "recalled_titles": [m["title"] for m in memories],
            "recalled": explained,
        })

        set_status(conn, incident_id, "diagnosing")

        live = timed_tool(conn, run_id, "diagnose", signal, lambda: diagnose(signal))
        log_event(conn, incident_id, "agent", "observation", {"live_diagnostics": live})

        control = timed_tool(conn, run_id, "control_plane", signal, lambda: control_plane(signal))
        log_event(conn, incident_id, "agent", "observation", {"control_plane": control})

        skills = timed_tool(conn, run_id, "run_skills", signal, lambda: run_skills(signal))
        log_event(conn, incident_id, "agent", "observation", {"skills": skills})

        plan = timed_tool(conn, run_id, "llm.plan", {
            "signal_title": signal.get("title"), "memories_count": len(memories),
        }, lambda: llm.plan({
            "signal": signal, "memories": memories,
            "live": live, "control": control, "skills": skills,
        }))
        update_incident(conn, incident_id, hypothesis=plan["hypothesis"])
        log_event(conn, incident_id, "agent", "decision", {
            "hypothesis": plan["hypothesis"],
            "summary": plan["summary"],
        })

        set_status(conn, incident_id, "remediating")

        executed = []
        held = []
        for action in plan["actions"]:
            dry = timed_tool(conn, run_id, "remediate", {**action, "dry_run": True}, lambda a=action: remediate(a, dry_run=True))
            impact = estimate_impact(action)
            if isinstance(dry, dict):
                dry = {**dry, "impact": impact}
            log_event(conn, incident_id, "agent", "observation", {"dry_run": dry, "impact": impact})
            dry_ok = bool(isinstance(dry, dict) and dry.get("ok"))
            hold, reason = needs_approval(action, impact, dry_ok=dry_ok)
            if hold:
                held.append({**action, "impact": impact})
                log_event(conn, incident_id, "agent", "approval", {
                    "awaiting": action,
                    "impact": impact,
                    "reason": reason,
                })
                continue
            result = timed_tool(conn, run_id, "remediate", {**action, "dry_run": False}, lambda a=action: remediate(a, dry_run=False, approved=False))
            record_action(conn, incident_id, {**action, "result": result}, destructive=False)
            executed.append({**action, "impact": impact, "result": result})

        runbook = save_runbook(conn, incident_id, signal, plan, executed, held)

        pm_context = {
            "signal": signal,
            "memories": memories,
            "plan": plan,
            "live": live,
            "skills": skills,
            "executed": [step.get("cmd") for step in executed],
            "held": [step.get("cmd") for step in held],
        }
        pm_result = timed_tool(conn, run_id, "write_postmortem", {"incident_id": incident_id}, lambda: write_postmortem(conn, incident_id, pm_context))

        set_status(conn, incident_id, "resolved")
        update_incident(conn, incident_id, resolution=pm_result["summary"])

        return {
            "incident_id": incident_id,
            "run_id": run_id,
            "status": "resolved",
            "hypothesis": plan["hypothesis"],
            "recalled": [m["title"] for m in memories],
            "explanations": explained,
            "runbook": {
                "title": runbook["title"],
                "knowledge_id": runbook["knowledge_id"],
                "steps": runbook["steps"],
            },
            "plan": plan,
            "knowledge_id": pm_result["knowledge_id"],
        }
    except Exception:
        failed = True
        raise
    finally:
        end_agent_run(conn, run_id, status="failed" if failed else "done")
