import pytest
from psycopg import errors as pg_errors

from sentinel.db import with_retry


def test_retry_on_serialization_failure():
    call_count = 0

    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise pg_errors.SerializationFailure("restart transaction")
        return "done"

    assert with_retry(flaky, retries=3) == "done"
    assert call_count == 3


def test_exhaust_retries():
    def always_fails():
        raise pg_errors.SerializationFailure("permanent fail")

    with pytest.raises(pg_errors.SerializationFailure):
        with_retry(always_fails, retries=2)
