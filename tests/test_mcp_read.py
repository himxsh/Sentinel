import pytest

from sentinel.tools.mcp_read import _is_read_only, diagnose, read_only_query


@pytest.mark.parametrize("sql", [
    "INSERT INTO foo VALUES (1)",
    "UPDATE foo SET x = 1",
    "DELETE FROM foo",
    "ALTER TABLE foo ADD COLUMN x int",
    "DROP TABLE foo",
    "CREATE TABLE foo (x int)",
])
def test_rejects_mutating_sql(sql):
    with pytest.raises(ValueError, match="Only SELECT and SHOW"):
        read_only_query(sql)


@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "SHOW DATABASES",
    "-- get version\nSELECT 1",
    "/* debug */ SHOW DATABASES",
])
def test_allows_read_only_sql(sql, monkeypatch):
    monkeypatch.setattr("sentinel.tools.mcp_read._read_dsn", lambda: _raise("no creds"))
    with pytest.raises(ValueError, match="no creds"):
        read_only_query(sql)


def test_is_read_only_utility():
    assert _is_read_only("SELECT 1")
    assert _is_read_only("SHOW DATABASES")
    assert _is_read_only("-- comment\nSELECT 1")
    assert _is_read_only("/* block */ SELECT 1")
    assert not _is_read_only("INSERT INTO foo VALUES (1)")
    assert not _is_read_only("DROP TABLE foo")
    assert not _is_read_only("DELETE FROM foo")
    assert not _is_read_only("CREATE TABLE foo")
    assert not _is_read_only("ALTER TABLE foo ADD x int")
    assert not _is_read_only("UPDATE foo SET x = 1")


def test_diagnose_catches_errors_per_query(monkeypatch):
    def fake_read_only_query(sql):
        raise ValueError("SENTINEL_READ_USER not set")

    monkeypatch.setattr("sentinel.tools.mcp_read.read_only_query", fake_read_only_query)
    result = diagnose({"title": "test"})
    assert len(result) == 2
    for name, entry in result.items():
        assert entry["ok"] is False
        assert "SENTINEL_READ_USER" in entry["error"]


def _raise(msg):
    raise ValueError(msg)
