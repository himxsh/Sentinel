import json
import urllib.request

from sentinel.config import get_settings

import lambdas.executor.handler as handler


def remediate(action: dict, *, dry_run: bool = True, approved: bool = False) -> dict:
    settings = get_settings()
    mode = settings.remediate_mode

    if mode == "local" or not settings.remediate_lambda_url:
        return handler.handle({
            "action": action,
            "dry_run": dry_run,
            "approved": approved,
        })

    # ponytail: urllib POST to Lambda URL; soft-fail on network errors
    try:
        req = urllib.request.Request(
            settings.remediate_lambda_url,
            data=json.dumps({"action": action, "dry_run": dry_run, "approved": approved}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"ok": False, "error": f"remediation request failed: {e}"}
