from sentinel.tools.remediate import remediate


def test_reject_unknown_cmd():
    result = remediate({"cmd": "nuke_cluster", "args": {}}, dry_run=True)
    assert result == {"ok": False, "error": "unknown action: nuke_cluster"}


def test_dry_run_no_side_effects():
    result = remediate({"cmd": "cancel_query", "args": {"query_pattern": "full table scan"}, "destructive": False}, dry_run=True)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["would_execute"]["cmd"] == "cancel_query"


def test_destructive_dry_run_always_ok():
    result = remediate({"cmd": "decommission_node", "args": {"node_id": "1"}, "destructive": True}, dry_run=True, approved=False)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["would_execute"]["cmd"] == "decommission_node"


def test_destructive_without_approved_fails():
    result = remediate({"cmd": "decommission_node", "args": {"node_id": "1"}, "destructive": True}, dry_run=False, approved=False)
    assert result == {"ok": False, "error": "approval required"}


def test_destructive_with_approved_ok():
    result = remediate({"cmd": "decommission_node", "args": {"node_id": "1"}, "destructive": True}, dry_run=False, approved=True)
    assert result["ok"] is True
    assert result["dry_run"] is False
    assert result["executed"]["cmd"] == "decommission_node"


def test_local_execute_simulated():
    result = remediate({"cmd": "recommend_index", "args": {"table": "orders", "columns": ["status"]}, "destructive": False}, dry_run=False, approved=False)
    assert result["ok"] is True
    assert result["dry_run"] is False
    assert result["result"] == "simulated"
