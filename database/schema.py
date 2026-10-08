"""
NetSimX — SQLite Schema DDL (Member 4)
All CREATE TABLE statements for the NetSimX database.
"""

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS experiments (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    topology    TEXT,
    algorithm   TEXT NOT NULL DEFAULT 'Dijkstra',
    source      TEXT NOT NULL DEFAULT '',
    destination TEXT NOT NULL DEFAULT '',
    duration_ms REAL NOT NULL DEFAULT 0.0,
    packet_count INTEGER NOT NULL DEFAULT 0,
    traffic_level TEXT NOT NULL DEFAULT 'LOW',
    status      TEXT NOT NULL DEFAULT 'CREATED'
                CHECK(status IN ('CREATED','RUNNING','COMPLETED','ABORTED'))
);

CREATE TABLE IF NOT EXISTS metrics (
    id              TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    timestamp_ms    REAL NOT NULL,
    packets_sent    INTEGER NOT NULL DEFAULT 0,
    packets_delivered INTEGER NOT NULL DEFAULT 0,
    packets_dropped INTEGER NOT NULL DEFAULT 0,
    throughput_mbps REAL NOT NULL DEFAULT 0.0,
    avg_latency_ms  REAL NOT NULL DEFAULT 0.0,
    jitter_ms       REAL NOT NULL DEFAULT 0.0,
    utilization_pct REAL NOT NULL DEFAULT 0.0,
    pdr_percent     REAL NOT NULL DEFAULT 0.0,
    plr_percent     REAL NOT NULL DEFAULT 0.0,
    avg_hops        REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id              TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    timestamp_ms    REAL NOT NULL,
    event_type      TEXT NOT NULL,
    target          TEXT NOT NULL DEFAULT '',
    description     TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topology_nodes (
    id              TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    node_id         TEXT NOT NULL,
    node_name       TEXT NOT NULL,
    node_type       TEXT NOT NULL,
    ip_address      TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'UP',
    pos_x           REAL NOT NULL DEFAULT 0.0,
    pos_y           REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topology_links (
    id              TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    link_id         TEXT NOT NULL,
    source          TEXT NOT NULL,
    destination     TEXT NOT NULL,
    cost            REAL NOT NULL DEFAULT 1.0,
    bandwidth_mbps  REAL NOT NULL DEFAULT 100.0,
    delay_ms        REAL NOT NULL DEFAULT 10.0,
    status          TEXT NOT NULL DEFAULT 'UP',
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metrics_exp ON metrics(experiment_id);
CREATE INDEX IF NOT EXISTS idx_events_exp  ON events(experiment_id);
CREATE INDEX IF NOT EXISTS idx_tnodes_exp  ON topology_nodes(experiment_id);
CREATE INDEX IF NOT EXISTS idx_tlinks_exp  ON topology_links(experiment_id);
"""
