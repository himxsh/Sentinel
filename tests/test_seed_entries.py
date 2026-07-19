from infra.seed_runbooks import ENTRIES


def test_entry_count():
    assert len(ENTRIES) >= 15


def test_exactly_three_postmortems():
    postmortems = [e for e in ENTRIES if e["source"] == "postmortem"]
    assert len(postmortems) == 3


def test_postmortem_keywords():
    titles = " ".join(e["title"] for e in ENTRIES if e["source"] == "postmortem").lower()
    assert "range" in titles or "hot" in titles
    assert "p99" in titles or "runaway" in titles or "query" in titles
    assert "node" in titles
