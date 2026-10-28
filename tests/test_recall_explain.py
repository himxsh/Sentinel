from sentinel.recall import explain_matches


def test_overlap_names_shared_words_and_band():
    signal = {
        "title": "P99 latency spike",
        "details": {"query": "SELECT count FROM orders"},
    }
    memories = [{
        "title": "Identify runaway high-latency queries",
        "content": "Cancel the latency query.",
        "source": "runbook",
        "distance": 0.08,
    }]
    hit = explain_matches(signal, memories)[0]
    assert hit["band"] == "near"
    assert "latency" in hit["overlap"]
    assert "Shares latency" in hit["why"]
    assert "runbook" in hit["why"]


def test_no_overlap_still_explains_the_neighbor():
    hit = explain_matches(
        {"title": "Clock skew on n7"},
        [{"title": "Disk space pressure", "content": "Add a store.", "source": "runbook", "distance": 0.5}],
    )[0]
    assert hit["overlap"] == []
    assert hit["band"] == "loose"
    assert hit["why"].startswith("No shared keywords.")


def test_empty_recall():
    assert explain_matches({"title": "x"}, []) == []
