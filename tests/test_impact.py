from sentinel.impact import estimate_impact, needs_approval, pending_action


def test_cancel_query_is_safe_to_apply():
    impact = estimate_impact({"cmd": "cancel_query", "args": {"query_pattern": "full table scan"}, "destructive": False})
    assert impact["hold"] is False
    assert impact["scope"] == "session"
    assert "full table scan" in impact["targets"]
    assert needs_approval({"cmd": "cancel_query", "destructive": False}, impact) == (False, "")


def test_scatter_holds_for_blast_radius_without_destructive_flag():
    action = {"cmd": "scatter_range", "args": {}, "destructive": False}
    impact = estimate_impact(action)
    assert impact["hold"] is True
    assert impact["risk"] == "high"
    assert impact["estimated_usd"] == 42
    hold, reason = needs_approval(action, impact)
    assert hold is True
    assert "cluster-wide" in reason


def test_reprovision_holds_on_dollar_cap():
    impact = estimate_impact({"cmd": "reprovision_node", "args": {}, "destructive": False})
    assert impact["risk"] == "medium"
    assert impact["hold"] is True
    assert "auto-apply cap" in impact["why_hold"]


def test_unknown_and_failed_dry_run_wait():
    impact = estimate_impact({"cmd": "drop_database", "destructive": False})
    assert impact["hold"] is True
    assert needs_approval({"cmd": "cancel_query", "destructive": False}, {"hold": False, "why_hold": ""}, dry_ok=False)[0] is True


def test_pending_action_walks_in_plan_order():
    both = [
        {"awaiting": {"cmd": "scatter_range"}},
        {"awaiting": {"cmd": "enable_random_uuids"}},
    ]
    assert pending_action(both)["cmd"] == "scatter_range"
    both.append({"approved": {"cmd": "scatter_range"}})
    assert pending_action(both)["cmd"] == "enable_random_uuids"
    assert pending_action([{"awaiting": {"op": "kill"}}, {"approved": True}]) is None
    assert pending_action([]) is None
