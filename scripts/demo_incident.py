from sentinel.agent import handle_alert
from sentinel.db import get_pool

SIGNALS = {
    2: {
        "title": "P99 latency spike on transaction processing",
        "severity": "P1",
        "cluster_ref": "kooky-efreet",
        "details": {
            "metric": "p99_latency",
            "value": 30,
            "unit": "s",
            "description": (
                "Transaction processing latency spiked to 30s p99. "
                "SHOW STATEMENTS flags a full table scan on orders (300M rows) without index."
            ),
        },
    },
}


def main():
    signal = SIGNALS[2]
    print(f"Firing scenario #2: {signal['title']}")
    pool = get_pool()
    with pool.connection() as conn:
        result = handle_alert(conn, signal)
        conn.commit()
    print(f"  incident_id : {result['incident_id']}")
    print(f"  status      : {result['status']}")
    print(f"  hypothesis  : {result['hypothesis']}")
    print(f"  recalled    : {[t for t in result['recalled']]}")
    print(f"  actions     : {result['plan']['actions']}")
    print(f"  summary     : {result['plan']['summary']}")


if __name__ == "__main__":
    main()
