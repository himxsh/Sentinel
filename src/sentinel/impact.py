"""Blast-radius and cost estimate before a fix is applied.

ponytail: static rate card, not live RU accounting. Upgrade path: fold row
counts from diagnose() into estimated_ru and estimated_usd.
"""

AUTO_APPLY_USD = 50

# risk_why is included only when risk is high. Dollar cap is applied separately.
_CARDS = {
    "cancel_query": {
        "scope": "session",
        "targets": "SQL sessions that match the pattern",
        "ru": 0,
        "usd": 0,
        "risk": "low",
        "do": "Cancel sessions that match the runaway pattern.",
        "rollback": "The client can retry the cancelled statement.",
        "risk_why": "",
    },
    "recommend_index": {
        "scope": "schema",
        "targets": "index advice only",
        "ru": 0,
        "usd": 0,
        "risk": "low",
        "do": "Recommend a covering index. Do not create it.",
        "rollback": "Nothing was written. Ignore the advice.",
        "risk_why": "",
    },
    "scatter_range": {
        "scope": "cluster",
        "targets": "hot ranges on every node that holds them",
        "ru": 250_000,
        "usd": 42,
        "risk": "high",
        "do": "Scatter the hot range so reads and writes spread out.",
        "rollback": "Leave the scatter. The allocator settles ranges on its own.",
        "risk_why": (
            "Scatter moves ranges on every node. The latency blip is cluster-wide, "
            "so this waits even though it is not marked destructive."
        ),
    },
    "enable_random_uuids": {
        "scope": "schema",
        "targets": "primary key generation for new writes",
        "ru": 0,
        "usd": 0,
        "risk": "high",
        "do": "Switch new primary keys to random UUIDs.",
        "rollback": "Point the column default back at sequential UUID generation.",
        "risk_why": "This changes how every new primary key is generated.",
    },
    "decommission_node": {
        "scope": "cluster",
        "targets": "one node and its replicas",
        "ru": 800_000,
        "usd": 120,
        "risk": "high",
        "do": "Decommission the dead node and let its replicas move.",
        "rollback": "Recommission the node before it is wiped, or provision a replacement.",
        "risk_why": "Removes a voter and moves its replicas.",
    },
    "reprovision_node": {
        "scope": "cluster",
        "targets": "a replacement node",
        "ru": 50_000,
        "usd": 90,
        "risk": "medium",
        "do": "Join a replacement node to the cluster.",
        "rollback": "Decommission the new node if it fails to join.",
        "risk_why": "",
    },
    "investigate_metrics": {
        "scope": "read",
        "targets": "dashboards only",
        "ru": 0,
        "usd": 0,
        "risk": "low",
        "do": "Open the SQL overview and confirm the metric.",
        "rollback": "Read-only. Nothing to undo.",
        "risk_why": "",
    },
}


def estimate_impact(action: dict) -> dict:
    cmd = str(action.get("cmd") or "")
    args = action.get("args") if isinstance(action.get("args"), dict) else {}
    card = _CARDS.get(cmd)
    note = "Estimate only. Not an invoice."
    if card is None:
        return {
            "cmd": cmd or "unknown",
            "scope": "unknown",
            "targets": "not on the rate card",
            "estimated_ru": None,
            "estimated_usd": None,
            "risk": "high",
            "hold": True,
            "why_hold": "No rate card for this action, so it waits for a person.",
            "do": "Do not run this until it is on the allow list.",
            "rollback": "Do not apply it.",
            "note": note,
        }

    reasons = []
    if action.get("destructive"):
        reasons.append("Marked destructive.")
    if card["risk"] == "high" and card["risk_why"]:
        reasons.append(card["risk_why"])
    if card["usd"] > AUTO_APPLY_USD:
        reasons.append(
            f"Estimated ${card['usd']}/month is over the ${AUTO_APPLY_USD} auto-apply cap."
        )
    return {
        "cmd": cmd,
        "scope": card["scope"],
        "targets": _targets(cmd, args, card["targets"]),
        "estimated_ru": card["ru"],
        "estimated_usd": card["usd"],
        "risk": card["risk"],
        "hold": bool(reasons),
        "why_hold": " ".join(reasons),
        "do": card["do"],
        "rollback": card["rollback"],
        "note": note,
    }


def needs_approval(action: dict, impact: dict, *, dry_ok: bool = True) -> tuple[bool, str]:
    if not dry_ok:
        return True, "Dry run failed, so nothing was applied."
    if action.get("destructive") or impact.get("hold"):
        return True, impact.get("why_hold") or "Needs a person before it runs."
    return False, ""


def pending_action(details: list[dict]) -> dict | None:
    """Earliest unapproved awaiting-action, in plan order. A blanket approval clears the queue.

    Keep in step with pendingGate in web/lib/format.ts and pendingGate in
    src/sentinel/ui/static/app.js.
    """
    approved: set[str] = set()
    for detail in details:
        if not isinstance(detail, dict):
            continue
        body = detail.get("approved")
        if isinstance(body, dict):
            cmd = body.get("cmd")
            approved.add(cmd if isinstance(cmd, str) and cmd else "*")
        elif body:
            approved.add("*")
    if "*" in approved:
        return None
    for detail in details:
        if not isinstance(detail, dict):
            continue
        awaiting = detail.get("awaiting")
        if not isinstance(awaiting, dict):
            continue
        cmd = awaiting.get("cmd")
        if isinstance(cmd, str) and cmd in approved:
            continue
        return awaiting
    return None


def _targets(cmd: str, args: dict, default: str) -> str:
    if cmd == "cancel_query" and args.get("query_pattern"):
        return f"sessions matching {args['query_pattern']}"
    if cmd == "recommend_index" and args.get("table"):
        columns = args.get("columns") or []
        listed = ", ".join(columns) if columns else "*"
        return f"index advice for {args['table']} ({listed})"
    if cmd == "decommission_node":
        return f"node {args.get('node_id') or 'unspecified'} and its replicas"
    return default
