from sentinel.tools.mcp_read import read_only_query

# Adapted curated SQL inspired by CockroachDB agent skills:
# triaging-live-sql-activity, analyzing-range-distribution,
# profiling-statement-fingerprints, monitoring-background-jobs.
# Not vendored markdown — thin runner only.
# ponytail: curated SQL stand-in for full skill markdown runner.
# Upgrade by loading SKILL.md from a configured path when skill files are vendored.
SKILL_QUERIES = {
    "triaging-live-sql-activity": [
        {"name": "active_statements", "sql": "SHOW CLUSTER STATEMENTS"},
    ],
    "analyzing-range-distribution": [
        {"name": "range_count", "sql": "SELECT count(*) AS range_count FROM crdb_internal.ranges_no_leases"},
    ],
    "profiling-statement-fingerprints": [
        {"name": "top_fingerprints", "sql": "SELECT fingerprint_id, metadata ->> 'db' AS db FROM crdb_internal.statement_statistics ORDER BY aggregated_ts DESC LIMIT 10"},
    ],
    "monitoring-background-jobs": [
        {"name": "active_jobs", "sql": "SHOW JOBS"},
    ],
}

_SIGNAL_SKILL_MAP = {
    "runaway": ["triaging-live-sql-activity", "profiling-statement-fingerprints"],
    "p99": ["triaging-live-sql-activity", "profiling-statement-fingerprints"],
    "latency": ["triaging-live-sql-activity", "profiling-statement-fingerprints"],
    "hot range": ["analyzing-range-distribution"],
    "imbalance": ["analyzing-range-distribution"],
    "job": ["monitoring-background-jobs"],
    "backup": ["monitoring-background-jobs"],
    "schema change": ["monitoring-background-jobs"],
}


def _sanitize_row(row: dict) -> dict:
    return {k: v.hex() if isinstance(v, bytes) else v for k, v in row.items()}


def relevant_skills(signal: dict) -> list[str]:
    text = str(signal).lower()
    for kw, skills in _SIGNAL_SKILL_MAP.items():
        if kw in text:
            return skills
    return ["triaging-live-sql-activity"]


def run_skills(signal: dict) -> dict:
    results = {}
    for skill_id in relevant_skills(signal):
        results[skill_id] = {"queries": []}
        for query in SKILL_QUERIES.get(skill_id, []):
            try:
                rows = read_only_query(query["sql"])
                results[skill_id]["queries"].append({
                    "name": query["name"],
                    "ok": True,
                    "rows": [_sanitize_row(r) for r in rows[:20]],
                })
            except Exception as e:
                results[skill_id]["queries"].append({
                    "name": query["name"],
                    "ok": False,
                    "error": str(e),
                })
    return results
