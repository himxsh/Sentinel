import json
import subprocess

from sentinel.config import get_settings

# ponytail: only read commands; expand when a destructive flow is designed
ALLOWED = frozenset([
    ("cluster", "list"),
    ("cluster", "info"),
])


def _bin() -> str:
    return get_settings().ccloud_bin


def run(args: list[str]) -> dict:
    prefix = tuple(args[:2])
    if prefix not in ALLOWED:
        raise ValueError(f"Command {args!r} not in allow-list; allowed: {sorted(ALLOWED)}")

    if "-o" not in args and "--format" not in args:
        args = [*args, "-o", "json"]

    try:
        proc = subprocess.run(
            [_bin(), *args],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        return {"ok": False, "error": "ccloud binary not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "ccloud command timed out"}

    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr.strip() or f"exit code {proc.returncode}", "stderr": proc.stderr}

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "failed to parse ccloud JSON output", "stderr": proc.stderr}

    return {"ok": True, "data": data}


def control_plane(signal: dict | None = None) -> dict:
    # ponytail: soft-fail covers missing binary / auth; no fake/mock path needed
    return run(["cluster", "list"])
