CREATE TABLE IF NOT EXISTS incidents (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title         STRING NOT NULL,
  severity      STRING NOT NULL,
  status        STRING NOT NULL DEFAULT 'open',
  cluster_ref   STRING,
  signal        JSONB NOT NULL,
  hypothesis    STRING,
  resolution    STRING,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS incident_events (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id  UUID NOT NULL REFERENCES incidents(id),
  ts           TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor        STRING NOT NULL,
  kind         STRING NOT NULL,
  detail       JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_incident ON incident_events (incident_id, ts);

CREATE TABLE IF NOT EXISTS knowledge (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source      STRING NOT NULL,
  title       STRING NOT NULL,
  content     STRING NOT NULL,
  metadata    JSONB,
  embedding   VECTOR(1024) NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE VECTOR INDEX IF NOT EXISTS idx_knowledge_embedding
  ON knowledge (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS agent_runs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id  UUID REFERENCES incidents(id),
  started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at     TIMESTAMPTZ,
  status       STRING NOT NULL DEFAULT 'running',
  model        STRING
);

CREATE TABLE IF NOT EXISTS tool_calls (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id     UUID NOT NULL REFERENCES agent_runs(id),
  ts         TIMESTAMPTZ NOT NULL DEFAULT now(),
  tool       STRING NOT NULL,
  args       JSONB,
  result     JSONB,
  ok         BOOL NOT NULL,
  latency_ms INT
);
