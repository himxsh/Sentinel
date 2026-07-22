ALLOWED_ACTIONS = frozenset({
    "cancel_query", "recommend_index", "scatter_range",
    "enable_random_uuids", "decommission_node", "reprovision_node",
    "investigate_metrics",
})


def handle(event: dict, context=None) -> dict:
    action = event.get("action", {})
    cmd = action.get("cmd", "")
    dry_run = event.get("dry_run", False)
    approved = event.get("approved", False)

    if cmd not in ALLOWED_ACTIONS:
        return {"ok": False, "error": f"unknown action: {cmd}"}

    if dry_run:
        return {"ok": True, "dry_run": True, "would_execute": action}

    if action.get("destructive") and not approved:
        return {"ok": False, "error": "approval required"}

    # ponytail: simulated execute; real CRDB CANCEL QUERY / etc. when wired
    return {"ok": True, "dry_run": False, "executed": action, "result": "simulated"}
