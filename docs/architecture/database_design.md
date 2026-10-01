# NetSimX — Database Design Document
**Document ID:** NX-ARCH-007  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Relational Entity-Relationship (ER) Diagram

The SQLite database (`data/db/netsimx.db`) is structured to record network configurations, simulation experiments, granular packet-level telemetry, and failure events.

```
┌──────────────────┐
│     NETWORKS     │
├──────────────────┤
│ PK  network_id   │
│     name         │
│     description  │
│     created_at   │
└────────┬─────────┘
         │ 1
         ├────────────────────────────────┬───────────────────────────────┐
         │ N                              │ N                             │ N
         ▼                                ▼                               ▼
┌──────────────────┐             ┌──────────────────┐            ┌──────────────────┐
│      NODES       │             │      LINKS       │            │   EXPERIMENTS    │
├──────────────────┤             ├──────────────────┤            ├──────────────────┤
│ PK,FK1 network_id│             │ PK  link_id      │            │ PK  experiment_id│
│ PK  node_id      │             │ FK1 network_id   │            │ FK1 network_id   │
│     name         │             │     source_node  │            │     algorithm    │
│     type         │             │     dest_node    │            │     traffic_level│
│     ip_address   │             │     cost         │            │     packet_count │
│     subnet_mask  │             │     bandwidth    │            │     start_time   │
│     gateway_ip   │             │     delay_ms     │            │     end_time     │
│     status       │             │     loss_prob    │            │     status       │
│     pos_x, pos_y │             │     status       │            └────────┬─────────┘
└──────────────────┘             └──────────────────┘                     │ 1
                                                                          ├──────────────────┬──────────────────┐
                                                                          │ N                │ N                │ 1
                                                                          ▼                  ▼                  ▼
                                                                 ┌──────────────────┐┌──────────────────┐┌──────────────────┐
                                                                 │     PACKETS      ││      EVENTS      ││     METRICS      │
                                                                 ├──────────────────┤├──────────────────┤├──────────────────┤
                                                                 │ PK,FK1 exp_id    ││ PK  event_id     ││ PK  metric_id    │
                                                                 │ PK  packet_id    ││ FK1 exp_id       ││ FK1 exp_id (UQ)  │
                                                                 │     source       ││     timestamp_ms ││     packets_sent │
                                                                 │     destination  ││     event_type   ││     packets_deliv│
                                                                 │     protocol     ││     target_id    ││     packets_lost │
                                                                 │     size_bytes   ││     result_detail││     pdr_percent  │
                                                                 │     status       │└──────────────────┘│     loss_percent │
                                                                 │     latency_ms   │                    │     throughput   │
                                                                 │     hop_count    │                    │     avg_delay_ms │
                                                                 │     drop_reason  │                    │     avg_hops     │
                                                                 └──────────────────┘                    │     utilization  │
                                                                                                         │     recovery_time│
                                                                                                         └──────────────────┘
```

---

## 2. Table Specifications & DDL Statements

### 2.1 Table: `networks`
Stores saved network topology metadata.
```sql
CREATE TABLE IF NOT EXISTS networks (
    network_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 Table: `nodes`
Stores device properties and canvas coordinates.
```sql
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT NOT NULL,
    network_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('ROUTER', 'SWITCH', 'PC', 'SERVER')),
    ip_address TEXT NOT NULL,
    subnet_mask TEXT NOT NULL DEFAULT '255.255.255.0',
    gateway_ip TEXT,
    status TEXT NOT NULL DEFAULT 'UP' CHECK(status IN ('UP', 'DOWN')),
    pos_x REAL DEFAULT 0.0,
    pos_y REAL DEFAULT 0.0,
    PRIMARY KEY (network_id, node_id),
    FOREIGN KEY (network_id) REFERENCES networks(network_id) ON DELETE CASCADE
);
```

### 2.3 Table: `links`
Stores physical and operational link attributes.
```sql
CREATE TABLE IF NOT EXISTS links (
    link_id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    source_node TEXT NOT NULL,
    destination_node TEXT NOT NULL,
    cost REAL NOT NULL DEFAULT 1.0,
    bandwidth_mbps REAL NOT NULL DEFAULT 100.0,
    delay_ms REAL NOT NULL DEFAULT 10.0,
    loss_probability REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'UP' CHECK(status IN ('UP', 'DOWN')),
    FOREIGN KEY (network_id) REFERENCES networks(network_id) ON DELETE CASCADE
);
```

### 2.4 Table: `experiments`
Tracks individual simulation runs.
```sql
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    algorithm TEXT NOT NULL CHECK(algorithm IN ('Dijkstra', 'Bellman-Ford', 'Distance-Vector')),
    traffic_level TEXT NOT NULL,
    packet_count INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT NOT NULL CHECK(status IN ('RUNNING', 'COMPLETED', 'ABORTED')),
    FOREIGN KEY (network_id) REFERENCES networks(network_id)
);
```

### 2.5 Table: `packets`
Maintains discrete packet hop telemetry for deep analysis.
```sql
CREATE TABLE IF NOT EXISTS packets (
    packet_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    protocol TEXT NOT NULL DEFAULT 'TCP',
    size_bytes INTEGER NOT NULL,
    status TEXT NOT NULL,
    latency_ms REAL,
    hop_count INTEGER,
    created_at_ms REAL NOT NULL,
    delivered_at_ms REAL,
    drop_reason TEXT,
    PRIMARY KEY (experiment_id, packet_id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE
);
```

### 2.6 Table: `metrics`
Aggregate performance metrics for dashboards and comparative analysis.
```sql
CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL UNIQUE,
    packets_sent INTEGER NOT NULL,
    packets_delivered INTEGER NOT NULL,
    packets_lost INTEGER NOT NULL,
    packet_delivery_ratio REAL NOT NULL,
    packet_loss_ratio REAL NOT NULL,
    throughput_kbps REAL NOT NULL,
    average_delay_ms REAL NOT NULL,
    average_hops REAL NOT NULL,
    network_utilization REAL NOT NULL,
    recovery_time_ms REAL DEFAULT 0.0,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE
);
```

### 2.7 Table: `events`
Logs failure and topology recalculation events.
```sql
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    timestamp_ms REAL NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('NODE_DOWN', 'NODE_UP', 'LINK_DOWN', 'LINK_UP', 'ROUTE_RECALC', 'TRAFFIC_SPIKE')),
    target_id TEXT NOT NULL,
    result_summary TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE
);
```

---

## 3. Indexing & Concurrency Strategy

To ensure queries on thousands of packet traces remain sub-millisecond without impacting GUI rendering:
```sql
CREATE INDEX IF NOT EXISTS idx_packets_experiment ON packets(experiment_id);
CREATE INDEX IF NOT EXISTS idx_packets_status ON packets(experiment_id, status);
CREATE INDEX IF NOT EXISTS idx_events_experiment ON events(experiment_id);
CREATE INDEX IF NOT EXISTS idx_nodes_network ON nodes(network_id);
CREATE INDEX IF NOT EXISTS idx_links_network ON links(network_id);
```

### Write-Ahead Logging (WAL) Mode
SQLite is initialized with WAL mode:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
```
This enables concurrent reads (by the GUI dashboard thread) while the background simulation worker writes telemetry batches.
