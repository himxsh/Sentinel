import os
import pytest

from sentinel.db import get_pool
from sentinel.embeddings import embed
from sentinel.memory import vector_recall

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — requires live CockroachDB Cloud",
)


@pytest.fixture
def conn():
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def test_vector_recall_returns_runaway_query_postmortem(conn):
    query_text = (
        "Runaway analytical query exhausted connection pool\n"
        "Incident: All application connections saturated, p99 latency at 30 s. "
        "Root cause: Unoptimized JOIN scanning 300 M rows without index. "
        "Detection: SHOW STATEMENTS flagged one query running 14 min with full table scan. "
        "Mitigation: CANCEL QUERY terminated the session, pool recovered in 2 min. "
        "Prevention: Added query timeout, index recommendation, and CONNECTIONS dashboard alert."
    )
    emb = embed(query_text)
    results = vector_recall(conn, emb, k=5)
    assert len(results) >= 1
    assert results[0]["title"] == "Runaway analytical query exhausted connection pool"
