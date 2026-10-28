from sentinel.replay import replay_beats


def test_replay_narrates_recall_impact_hold_and_runbook():
    events = [
        {"kind": "observation", "detail": {"title": "Hot range", "severity": "P1"}},
        {
            "kind": "observation",
            "detail": {
                "recalled": [{"why": "Shares range with this alert.", "title": "Hot range runbook"}],
            },
        },
        {
            "kind": "observation",
            "detail": {
                "impact": {
                    "cmd": "scatter_range",
                    "scope": "cluster",
                    "estimated_usd": 42,
                    "risk": "high",
                    "hold": True,
                },
            },
        },
        {
            "kind": "approval",
            "detail": {
                "awaiting": {"cmd": "scatter_range"},
                "impact": {"estimated_usd": 42},
                "reason": "The latency blip is cluster-wide.",
            },
        },
        {
            "kind": "observation",
            "detail": {"title": "Runbook: Hot range", "steps": [{"cmd": "scatter_range"}]},
        },
    ]
    beats = replay_beats(events)
    assert beats[0]["narration"].startswith("Opened Hot range")
    assert beats[1]["narration"].startswith("Recalled 1 case.")
    assert "Shares range" in beats[1]["narration"]
    assert "scatter_range: cluster blast, $42/month" in beats[2]["narration"]
    assert "Held for approval" in beats[2]["narration"]
    assert beats[3]["narration"].startswith("Paused scatter_range.")
    assert "$42/month" in beats[3]["narration"]
    assert beats[4]["narration"] == 'Filed runbook "Runbook: Hot range" with 1 step.'


def test_replay_empty():
    assert replay_beats(None) == []
