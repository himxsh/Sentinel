"""Turn a resolved case into a reusable runbook and store it as knowledge."""

from sentinel.embeddings import embed
from sentinel.impact import estimate_impact
from sentinel.memory import log_event, store_knowledge


def build_runbook(signal: dict, plan: dict, executed: list[dict], held: list[dict]) -> dict:
    title = f"Runbook: {signal.get('title') or 'Incident'}"
    steps = []
    for status, actions in (("applied", executed), ("held", held)):
        for action in actions:
            impact = action.get("impact") if isinstance(action.get("impact"), dict) else estimate_impact(action)
            cmd = str(action.get("cmd") or impact.get("cmd") or "unknown")
            steps.append({"cmd": cmd, "status": status, "do": impact.get("do") or f"Run {cmd}."})

    checks = ["Confirm the alerting metric is back under its threshold."]
    if any(step["cmd"] == "cancel_query" and step["status"] == "applied" for step in steps):
        checks.append("Confirm the connection pool is accepting new sessions.")
    if any(step["status"] == "held" for step in steps):
        checks.append("Leave the case open until every held step is approved or declined.")

    rollback = []
    if not executed:
        rollback.append("Nothing was applied. Declining the held steps leaves the cluster unchanged.")
    for action in list(executed) + list(held):
        impact = action.get("impact") if isinstance(action.get("impact"), dict) else estimate_impact(action)
        line = impact.get("rollback")
        if line and line not in rollback:
            rollback.append(line)

    hypothesis = (plan or {}).get("hypothesis") or ""
    markdown = _markdown(title, signal, hypothesis, steps, checks, rollback)
    return {
        "title": title,
        "steps": steps,
        "checks": checks,
        "rollback": rollback,
        "markdown": markdown,
    }


def save_runbook(conn, incident_id, signal: dict, plan: dict, executed: list[dict], held: list[dict]) -> dict:
    runbook = build_runbook(signal, plan, executed, held)
    knowledge_id = store_knowledge(
        conn,
        source="runbook",
        title=runbook["title"],
        content=runbook["markdown"],
        embedding=embed(runbook["markdown"]),
        metadata={"incident_id": str(incident_id), "generated": True},
    )
    log_event(
        conn,
        incident_id,
        "agent",
        "observation",
        {
            "runbook_id": knowledge_id,
            "title": runbook["title"],
            "steps": runbook["steps"],
            "checks": runbook["checks"],
            "rollback": runbook["rollback"],
            "markdown": runbook["markdown"],
        },
    )
    return {**runbook, "knowledge_id": knowledge_id}


def _markdown(title, signal, hypothesis, steps, checks, rollback) -> str:
    lines = [f"# {title}", ""]
    lines.append(f"Severity: {signal.get('severity', 'n/a')}")
    if signal.get("cluster_ref"):
        lines.append(f"Cluster: {signal['cluster_ref']}")
    if hypothesis:
        lines.append(f"Hypothesis: {hypothesis}")
    lines += ["", "## Steps"]
    if not steps:
        lines.append("1. No action was planned.")
    for index, step in enumerate(steps, 1):
        mark = "applied" if step["status"] == "applied" else "needs approval"
        lines.append(f"{index}. [{mark}] {step['do']} (`{step['cmd']}`)")
    lines += ["", "## Checks"]
    lines.extend(f"- {check}" for check in checks)
    lines += ["", "## Rollback"]
    lines.extend(f"- {line}" for line in rollback)
    lines += ["", "Dollar figures are the static rate card, not an invoice.", ""]
    return "\n".join(lines)
