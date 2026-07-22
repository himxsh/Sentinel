import json

import pytest

from sentinel.tools.skills import SKILL_QUERIES, relevant_skills, run_skills


def test_skills_have_one_query_each():
    for skill_id, queries in SKILL_QUERIES.items():
        assert len(queries) == 1, f"{skill_id} has {len(queries)} queries, expected 1"
        assert "name" in queries[0]
        assert "sql" in queries[0]


def test_skill_sql_is_read_only():
    for skill_id, queries in SKILL_QUERIES.items():
        for q in queries:
            upper = q["sql"].strip().upper()
            assert upper.startswith("SELECT") or upper.startswith("SHOW"), \
                f"{skill_id}/{q['name']} is not read-only: {q['sql']}"


@pytest.mark.parametrize("title,expected", [
    ("Runaway query detected", ["triaging-live-sql-activity", "profiling-statement-fingerprints"]),
    ("P99 latency spike", ["triaging-live-sql-activity", "profiling-statement-fingerprints"]),
    ("Hot range detected", ["analyzing-range-distribution"]),
    ("Range imbalance", ["analyzing-range-distribution"]),
    ("Job failure backup", ["monitoring-background-jobs"]),
    ("Schema change slow", ["monitoring-background-jobs"]),
    ("Unknown alert", ["triaging-live-sql-activity"]),
])
def test_relevant_skills(title, expected):
    assert relevant_skills({"title": title}) == expected


def test_run_skills_soft_fails_on_privilege_error(monkeypatch):
    def fake_read_only_query(sql):
        raise PermissionError("user sentinel_read lacks VIEWACTIVITY privilege")

    monkeypatch.setattr("sentinel.tools.skills.read_only_query", fake_read_only_query)
    result = run_skills({"title": "Runaway query"})
    assert "triaging-live-sql-activity" in result
    queries = result["triaging-live-sql-activity"]["queries"]
    assert len(queries) == 1
    assert queries[0]["ok"] is False
    assert "VIEWACTIVITY" in queries[0]["error"]


def test_run_skills_sanitizes_bytes(monkeypatch):
    def fake_read_only_query(sql):
        return [{"fingerprint_id": b"abc123", "db": "defaultdb"}]

    monkeypatch.setattr("sentinel.tools.skills.read_only_query", fake_read_only_query)
    result = run_skills({"title": "Runaway query"})
    rows = result["triaging-live-sql-activity"]["queries"][0]["rows"]
    assert rows == [{"fingerprint_id": "616263313233", "db": "defaultdb"}]
    json.dumps(rows)  # no TypeError from bytes
