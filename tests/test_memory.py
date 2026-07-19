import pytest

from sentinel.memory import record_action, log_event, ApprovalRequired


class _Row:
    def __getitem__(self, i):
        return 1


class _Cursor:
    def __init__(self, row=None):
        self.row = row
    def fetchone(self):
        return self.row
    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, has_approval=False):
        self.executes = []
        self._has_approval = has_approval
    def execute(self, sql, params=None):
        self.executes.append((sql, params))
        return _Cursor(_Row() if self._has_approval and "approval" in sql else None)
    def commit(self):
        pass


def test_destructive_without_approval_raises():
    c = _FakeConn(has_approval=False)
    with pytest.raises(ApprovalRequired):
        record_action(c, "inc-1", {"cmd": "restart"}, destructive=True)


def test_destructive_after_approval_succeeds():
    c = _FakeConn(has_approval=True)
    log_event(c, "inc-1", "human", "approval", {"approved": True})
    record_action(c, "inc-1", {"cmd": "restart"}, destructive=True)
    approvals = [p for s, p in c.executes if "approval" in s]
    assert len(approvals) >= 1  # at least the SELECT approval check ran


def test_non_destructive_no_approval_needed():
    c = _FakeConn(has_approval=False)
    record_action(c, "inc-1", {"cmd": "describe"}, destructive=False)
    # no exception = success
