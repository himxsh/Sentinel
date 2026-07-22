import re
import urllib.parse

from psycopg import Connection

from sentinel.config import get_settings

_READ_SQL_RE = re.compile(r"^\s*(SELECT|SHOW)\b", re.IGNORECASE)
_COMMENT_RE = re.compile(r"/\*.*?\*/|--[^\n]*", re.DOTALL)


def _is_read_only(sql: str) -> bool:
    cleaned = _COMMENT_RE.sub("", sql)
    return bool(_READ_SQL_RE.match(cleaned))


def _read_dsn() -> str:
    settings = get_settings()
    usr = settings.sentinel_read_user
    pwd = settings.sentinel_read_password
    if not usr or not pwd:
        raise ValueError(
            "SENTINEL_READ_USER and SENTINEL_READ_PASSWORD must be set "
            "to use the read-only query path"
        )
    parsed = urllib.parse.urlparse(settings.database_url)
    netloc = f"{urllib.parse.quote(usr, safe='')}:{urllib.parse.quote(pwd, safe='')}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urllib.parse.urlunparse(parsed._replace(netloc=netloc))


def read_only_query(sql: str) -> list[dict]:
    if not _is_read_only(sql):
        raise ValueError("Only SELECT and SHOW statements are allowed via sentinel_read")
    dsn = _read_dsn()
    with Connection.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description is None:
                return []
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


# ponytail: SQL-via-sentinel_read stand-in for Managed MCP; swap to MCP client when Cloud MCP is configured
# ponytail: version() is a SQL function that works on CRDB Basic without VIEWCLUSTERSETTING
_QUERIES = {
    "version": "SELECT version() AS crdb_version",
    "databases": "SHOW DATABASES",
}


def diagnose(signal: dict) -> dict:
    results = {}
    for name, sql in _QUERIES.items():
        try:
            rows = read_only_query(sql)
            results[name] = {"ok": True, "rows": rows[:3]}
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)}
    return results
