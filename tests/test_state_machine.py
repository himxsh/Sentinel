import pytest

from sentinel.memory import set_status, IllegalTransition


class _Row:
    def __init__(self, val):
        self._val = val
    def __getitem__(self, i):
        return self._val if i == 0 else None


class _Cursor:
    def __init__(self, row=None):
        self.row = row
    def fetchone(self):
        return self.row
    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, status):
        self.executes = []
        self._status = status
    def execute(self, sql, params=None):
        self.executes.append((sql, params))
        if "SELECT status" in sql:
            return _Cursor(_Row(self._status))
        return _Cursor()
    def commit(self):
        pass


def _conn(status="open"):
    return _FakeConn(status)


def test_legal_open_to_diagnosing():
    c = _conn("open")
    set_status(c, "id-1", "diagnosing")
    assert any("UPDATE incidents" in s for s, _ in c.executes)
    assert any("INSERT INTO incident_events" in s for s, _ in c.executes)


def test_legal_diagnosing_to_remediating():
    c = _conn("diagnosing")
    set_status(c, "id-1", "remediating")
    assert any("UPDATE incidents" in s for s, _ in c.executes)


def test_legal_remediating_to_resolved():
    c = _conn("remediating")
    set_status(c, "id-1", "resolved")
    assert any("UPDATE incidents" in s for s, _ in c.executes)


def test_illegal_open_to_resolved():
    c = _conn("open")
    with pytest.raises(IllegalTransition):
        set_status(c, "id-1", "resolved")


def test_illegal_diagnosing_to_resolved():
    c = _conn("diagnosing")
    with pytest.raises(IllegalTransition):
        set_status(c, "id-1", "resolved")
