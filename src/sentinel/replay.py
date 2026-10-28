"""Narrated beats for the incident replay. One beat per audit event."""

_LABELS = {
    "observation": "Noted",
    "decision": "Decided",
    "approval": "Approval",
    "action": "Acted",
}


def replay_beats(events: list[dict] | None) -> list[dict]:
    beats = []
    for event in events or []:
        kind = event.get("kind")
        beats.append({"label": _LABELS.get(kind, str(kind or "Event")), "narration": _narrate(event)})
    return beats


def _narrate(event: dict) -> str:
    detail = event.get("detail") if isinstance(event.get("detail"), dict) else {}
    kind = event.get("kind")
    label = _LABELS.get(kind, str(kind or "Event"))
    if not detail:
        return label

    if kind == "approval" and isinstance(detail.get("awaiting"), dict):
        awaiting = detail["awaiting"]
        cmd = awaiting.get("cmd") or "a change"
        impact = detail.get("impact") if isinstance(detail.get("impact"), dict) else {}
        usd = impact.get("estimated_usd")
        money = f" About ${usd}/month." if isinstance(usd, (int, float)) else ""
        reason = detail.get("reason") or "Needs a person."
        return f"Paused {cmd}.{money} {reason}".strip()

    if kind == "approval" and detail.get("approved"):
        return "Approved. The held change can run."

    recalled = detail.get("recalled")
    if isinstance(recalled, list) and recalled:
        first = recalled[0] if isinstance(recalled[0], dict) else {}
        why = first.get("why") or ""
        noun = "case" if len(recalled) == 1 else "cases"
        return f"Recalled {len(recalled)} {noun}. {why}".strip()

    impact = _impact(detail)
    if impact and impact.get("cmd"):
        usd = impact.get("estimated_usd")
        money = f"${usd}/month" if isinstance(usd, (int, float)) else "no dollar estimate"
        hold = "Held for approval." if impact.get("hold") else "Clear to apply."
        return (
            f"{impact['cmd']}: {impact.get('scope', 'unknown')} blast, "
            f"{money}, {impact.get('risk', 'unknown')} risk. {hold}"
        )

    if detail.get("hypothesis"):
        return str(detail["hypothesis"])

    if isinstance(detail.get("steps"), list) and detail.get("title"):
        count = len(detail["steps"])
        noun = "step" if count == 1 else "steps"
        return f"Filed runbook \"{detail['title']}\" with {count} {noun}."

    if detail.get("from") and detail.get("to"):
        return f"Status {detail['from']} to {detail['to']}."

    if detail.get("summary"):
        return str(detail["summary"])

    if detail.get("title") and detail.get("severity"):
        return f"Opened {detail['title']} ({detail['severity']})."

    title = str(detail.get("title") or "")
    if title.startswith("Postmortem"):
        return f"Filed the write-up: {title}."

    if kind == "action" and detail.get("cmd"):
        return f"Applied {detail['cmd']}."

    return label


def _impact(detail: dict):
    impact = detail.get("impact")
    if isinstance(impact, dict):
        return impact
    dry = detail.get("dry_run")
    if isinstance(dry, dict) and isinstance(dry.get("impact"), dict):
        return dry["impact"]
    return None
