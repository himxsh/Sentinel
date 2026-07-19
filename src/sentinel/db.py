import time

from psycopg import errors as pg_errors
from psycopg_pool import ConnectionPool

from sentinel.config import get_settings

_pool = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(get_settings().database_url, min_size=1, max_size=4)
    return _pool


def with_retry(fn, *, retries=5):
    # ponytail: 100ms base, 2x backoff, cap at 2s
    for attempt in range(retries):
        try:
            return fn()
        except pg_errors.SerializationFailure:
            if attempt == retries - 1:
                raise
            time.sleep(min(0.1 * (2**attempt), 2.0))


def execute(fn):
    def _exec():
        pool = get_pool()
        with pool.connection() as conn:
            result = fn(conn)
            conn.commit()
            return result

    return with_retry(_exec)
