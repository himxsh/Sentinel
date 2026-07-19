from psycopg.types.json import Json

from sentinel.embeddings import embed
from sentinel.db import get_pool

ENTRIES = [
    # ── runbooks ──
    {"source": "runbook", "title": "Hot range detection & rebalance",
     "content": "1. Check cluster range dashboard for range count imbalance. "
     "2. SHOW RANGES FROM TABLE to identify unbalanced ranges. "
     "3. Use ALTER TABLE … SCATTER to rebalance. "
     "4. Set kv.range_split_by_load_key.enabled = true for auto-rebalance. "
     "5. Monitor QPS and latency post-scatter."},
    {"source": "runbook", "title": "Identify runaway high-latency queries",
     "content": "1. Check SQL Activity dashboard for long-running queries. "
     "2. SHOW STATEMENTS WITH EXECUTION TIME > 1s. "
     "3. Look for missing index scans or full table scans. "
     "4. Kill the query with CANCEL QUERY <id>. "
     "5. Add missing index and file a ticket to optimize the query plan."},
    {"source": "runbook", "title": "Node down recovery",
     "content": "1. Verify node status via cockroach node status --decommission. "
     "2. Check if the node is dead (last heartbeat > 5 min). "
     "3. If the node is dead, decommission it. "
     "4. Reprovision a replacement node with --join. "
     "5. Verify replication factor is restored."},
    {"source": "runbook", "title": "Deadlock detection in transactions",
     "content": "1. Look for SQLSTATE 40001 (serialization) or 40P01 (deadlock) errors. "
     "2. SHOW TRANSACTIONS to list blocked sessions. "
     "3. Reduce contention window by shortening transactions. "
     "4. Ensure retry logic is implemented at the application layer. "
     "5. Increase --max-sql-memory for larger sort/join buffers."},
    {"source": "runbook", "title": "Cluster upgrade rollback",
     "content": "1. Stop upgrade with SET CLUSTER SETTING version = '<prev>'. "
     "2. Verify no in-flight migrations. "
     "3. Reset nodes to previous binary version. "
     "4. Restart each node with cockroach start --join=<existing>. "
     "5. Monitor health endpoint until all nodes are stable."},
    {"source": "runbook", "title": "Disk space pressure",
     "content": "1. Check node store usage via DB Console. "
     "2. ALTER TABLE … EXPERIMENTAL_RELOCATE to move ranges. "
     "3. Increase store size or add new nodes. "
     "4. Enable range snapshots to redistribute data. "
     "5. Configure --store size limits per node."},
    {"source": "runbook", "title": "Replication factor recovery",
     "content": "1. SHOW ZONE CONFIGURATION FOR RANGE default. "
     "2. ALTER RANGE default CONFIGURE ZONE USING num_replicas = 3. "
     "3. Check replication via rangelog. "
     "4. If under-replicated, add nodes or wait for allocator. "
     "5. Alter individual table zone configs if needed."},
    {"source": "runbook", "title": "Slow backup / restore",
     "content": "1. Check backup job status via SHOW JOBS. "
     "2. Increase backup concurrency via --max-concurrent-backups. "
     "3. Use smaller batch sizes for incremental backups. "
     "4. Ensure S3 bucket region matches cluster region. "
     "5. Enable backup compression with --compression."},
    {"source": "runbook", "title": "Clock skew investigation",
     "content": "1. Check max_offset metric per node. "
     "2. Ensure NTP service is running and synced. "
     "3. Restart time-daemon on nodes with >500ms offset. "
     "4. Verify firewall rules for NTP traffic (UDP 123). "
     "5. Configure max-offset-clause in cockroach start."},
    {"source": "runbook", "title": "Connection pool exhaustion",
     "content": "1. SHOW SESSIONS to count active connections. "
     "2. SHOW STATEMENTS to find idle-in-transaction sessions. "
     "3. Kill stale sessions with CANCEL SESSION. "
     "4. Set pool max_size lower than PostgreSQL max_connections. "
     "5. Add connection pool metrics to your monitoring stack."},
    {"source": "runbook", "title": "Stale follower reads",
     "content": "1. Query freshness with follower_read_timestamp() function. "
     "2. SET TRANSACTION AS OF SYSTEM TIME follower_read_timestamp(). "
     "3. Verify application can tolerate staleness up to ~5 s. "
     "4. Use global tables with < 48 ms staleness for lookup tables. "
     "5. Monitor closed_timestamp interval via cluster settings."},
    {"source": "runbook", "title": "Data corruption checks",
     "content": "1. Run cockroach debug check-store on suspect nodes. "
     "2. Compare replicas via EXPORT and checksums. "
     "3. Restore corrupted ranges from backup. "
     "4. Enable consistency checks via --consistency-check-interval. "
     "5. File P0 incident if replication reveals silent corruption."},
    {"source": "runbook", "title": "Locality / multi-region tuning",
     "content": "1. Set table locality with ALTER TABLE … SET LOCALITY REGIONAL BY ROW. "
     "2. Configure survival goal: REGION vs ZONE survival. "
     "3. Add regional_by_row column as crdb_region. "
     "4. Pin follower reads for global tables. "
     "5. Test failover latency before production cutover."},
    {"source": "runbook", "title": "Schema migration crash",
     "content": "1. Check migration job via SHOW JOBS. "
     "2. CANCEL JOB for stuck migration. "
     "3. Roll back migration DDL. "
     "4. Retry schema change with SET schema_change_migration_mode = direct. "
     "5. Test DDLs on staging with same cluster version."},
    {"source": "runbook", "title": "Monitoring stack integration",
     "content": "1. Enable Prometheus endpoint on each node --http-addr. "
     "2. Point Prometheus to /_status/vars per node. "
     "3. Import CockroachDB Grafana dashboard (id 12707). "
     "4. Set up alerting on SQL Service Latency > 100 ms p99. "
     "5. Add log alert rule for SQLSTATE serialization errors."},
    {"source": "runbook", "title": "RBAC and audit logging",
     "content": "1. CREATE ROLE <role> and GRANT <permissions>. "
     "2. ALTER ROLE <user> LOGIN PASSWORD '<pw>'. "
     "3. Enable SQL audit logging via ALTER TABLE … EXPERIMENTAL_AUDIT. "
     "4. Ship audit logs to SIEM via fluentd. "
     "5. Rotate audit logs daily with log rotation."},
    {"source": "runbook", "title": "Changefeed setup troubleshooting",
     "content": "1. Check changefeed job: SHOW CHANGEFEED JOBS. "
     "2. Verify Kafka / sink connectivity. "
     "3. Increase changefeed.poll_interval for high-throughput tables. "
     "4. Use protected timestamps to prevent garbage collection. "
     "5. Monitor changefeed lag and retry metrics."},
    {"source": "runbook", "title": "Memory lease transfer",
     "content": "1. Identify lease holder with SHOW RANGES … WITH DETAILS. "
     "2. Transfer lease: ALTER TABLE … EXPERIMENTAL_RELOCATE LEASE. "
     "3. Balance lease count across nodes. "
     "4. Use COCKROACH_ALLOW_LEASE_TRANSFER_TO_DEAD_NODE=false guard. "
     "5. Verify QPS shift matches lease transfer."},
    # ── postmortems ──
    {"source": "postmortem", "title": "Hot range imbalance caused p99 spike",
     "content": "Incident: One key range received 10× more requests than peers. "
     "Root cause: Sequential UUIDs created a hot key on a single range. "
     "Detection: Range dashboard showed one range with 120k QPS vs 8k average. "
     "Mitigation: Scattered the range and switched to random UUIDs. "
     "Prevention: Added scatter-before-schema-migration step to runbooks.",
     "metadata": {"severity": "P1", "duration_min": 45}},
    {"source": "postmortem", "title": "Runaway analytical query exhausted connection pool",
     "content": "Incident: All application connections saturated, p99 latency at 30 s. "
     "Root cause: Unoptimized JOIN scanning 300 M rows without index. "
     "Detection: SHOW STATEMENTS flagged one query running 14 min with full table scan. "
     "Mitigation: CANCEL QUERY terminated the session, pool recovered in 2 min. "
     "Prevention: Added query timeout, index recommendation, and CONNECTIONS dashboard alert.",
     "metadata": {"severity": "P2", "duration_min": 20}},
    {"source": "postmortem", "title": "Node failure degraded replication",
     "content": "Incident: Under-replicated ranges for 25 min after single node crash. "
     "Root cause: Hardware memory ECC error triggered kernel panic. "
     "Detection: Replication dashboard showed 47 under-replicated ranges. "
     "Mitigation: cockroach node recommission replaced the failed node in 12 min. "
     "Prevention: Added hardware health checks, faster decommission automation.",
     "metadata": {"severity": "P1", "duration_min": 37}},
]


def main():
    pool = get_pool()
    with pool.connection() as conn:
        # ponytail: delete-all in these sources; incremental upsert if entries grow large
        sources = {e["source"] for e in ENTRIES}
        conn.execute("DELETE FROM knowledge WHERE source = ANY(%s)", (list(sources),))
        inserted = 0
        for entry in ENTRIES:
            text = entry["title"] + "\n" + entry["content"]
            vector = embed(text)
            emb_str = "[" + ",".join(str(x) for x in vector) + "]"
            conn.execute(
                "INSERT INTO knowledge (source, title, content, metadata, embedding) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    entry["source"],
                    entry["title"],
                    entry["content"],
                    Json(entry.get("metadata")) if entry.get("metadata") else None,
                    emb_str,
                ),
            )
            inserted += 1
        conn.commit()
        print(f"Seeded {inserted} knowledge entries.")


if __name__ == "__main__":
    main()
