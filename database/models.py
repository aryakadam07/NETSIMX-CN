"""
NetSimX — Database Repository Models (Member 4)
Repository pattern: no raw SQL outside this file.
"""

import uuid
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import Database

logger = logging.getLogger("Models")


# ======================================================================
# Record dataclasses
# ======================================================================

@dataclass
class ExperimentRecord:
    name: str
    algorithm: str
    source: str
    destination: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    topology: str = ""          # JSON-serialized topology snapshot
    duration_ms: float = 0.0
    packet_count: int = 0
    traffic_level: str = "LOW"
    status: str = "CREATED"


@dataclass
class MetricsRecord:
    experiment_id: str
    timestamp_ms: float
    packets_sent: int = 0
    packets_delivered: int = 0
    packets_dropped: int = 0
    throughput_mbps: float = 0.0
    avg_latency_ms: float = 0.0
    jitter_ms: float = 0.0
    utilization_pct: float = 0.0
    pdr_percent: float = 0.0
    plr_percent: float = 0.0
    avg_hops: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class EventRecord:
    experiment_id: str
    timestamp_ms: float
    event_type: str
    target: str = ""
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ======================================================================
# Repositories
# ======================================================================

class ExperimentRepository:
    """CRUD operations for experiments table."""

    def __init__(self, db: Database):
        self._db = db

    def create(self, exp: ExperimentRecord) -> str:
        self._db.execute(
            """INSERT INTO experiments
               (id, name, created_at, topology, algorithm, source, destination,
                duration_ms, packet_count, traffic_level, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (exp.id, exp.name, exp.created_at, exp.topology,
             exp.algorithm, exp.source, exp.destination,
             exp.duration_ms, exp.packet_count, exp.traffic_level, exp.status)
        )
        self._db.commit()
        return exp.id

    def get_by_id(self, experiment_id: str) -> Optional[ExperimentRecord]:
        row = self._db.fetchone(
            "SELECT * FROM experiments WHERE id=?", (experiment_id,))
        return self._row_to_record(row) if row else None

    def get_all(self) -> List[ExperimentRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM experiments ORDER BY created_at DESC")
        return [self._row_to_record(r) for r in rows]

    def update_status(self, experiment_id: str, status: str,
                      duration_ms: float = 0.0) -> None:
        self._db.execute(
            "UPDATE experiments SET status=?, duration_ms=? WHERE id=?",
            (status, duration_ms, experiment_id))
        self._db.commit()

    def delete(self, experiment_id: str) -> None:
        self._db.execute("DELETE FROM experiments WHERE id=?", (experiment_id,))
        self._db.commit()

    @staticmethod
    def _row_to_record(row) -> ExperimentRecord:
        return ExperimentRecord(
            id=row["id"],
            name=row["name"],
            created_at=row["created_at"],
            topology=row["topology"] or "",
            algorithm=row["algorithm"],
            source=row["source"],
            destination=row["destination"],
            duration_ms=row["duration_ms"],
            packet_count=row["packet_count"],
            traffic_level=row["traffic_level"],
            status=row["status"],
        )


class MetricsRepository:
    """CRUD operations for metrics table."""

    def __init__(self, db: Database):
        self._db = db

    def save(self, m: MetricsRecord) -> None:
        self._db.execute(
            """INSERT INTO metrics
               (id, experiment_id, timestamp_ms, packets_sent, packets_delivered,
                packets_dropped, throughput_mbps, avg_latency_ms, jitter_ms,
                utilization_pct, pdr_percent, plr_percent, avg_hops)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (m.id, m.experiment_id, m.timestamp_ms, m.packets_sent,
             m.packets_delivered, m.packets_dropped, m.throughput_mbps,
             m.avg_latency_ms, m.jitter_ms, m.utilization_pct,
             m.pdr_percent, m.plr_percent, m.avg_hops)
        )
        self._db.commit()

    def save_many(self, records: List[MetricsRecord]) -> None:
        self._db.executemany(
            """INSERT INTO metrics
               (id, experiment_id, timestamp_ms, packets_sent, packets_delivered,
                packets_dropped, throughput_mbps, avg_latency_ms, jitter_ms,
                utilization_pct, pdr_percent, plr_percent, avg_hops)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [(m.id, m.experiment_id, m.timestamp_ms, m.packets_sent,
              m.packets_delivered, m.packets_dropped, m.throughput_mbps,
              m.avg_latency_ms, m.jitter_ms, m.utilization_pct,
              m.pdr_percent, m.plr_percent, m.avg_hops)
             for m in records]
        )
        self._db.commit()

    def get_by_experiment(self, experiment_id: str) -> List[MetricsRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM metrics WHERE experiment_id=? ORDER BY timestamp_ms",
            (experiment_id,))
        return [self._row_to_record(r) for r in rows]

    def get_final(self, experiment_id: str) -> Optional[MetricsRecord]:
        """Returns the last recorded metrics snapshot for an experiment."""
        row = self._db.fetchone(
            "SELECT * FROM metrics WHERE experiment_id=? ORDER BY timestamp_ms DESC LIMIT 1",
            (experiment_id,))
        return self._row_to_record(row) if row else None

    @staticmethod
    def _row_to_record(row) -> MetricsRecord:
        return MetricsRecord(
            id=row["id"],
            experiment_id=row["experiment_id"],
            timestamp_ms=row["timestamp_ms"],
            packets_sent=row["packets_sent"],
            packets_delivered=row["packets_delivered"],
            packets_dropped=row["packets_dropped"],
            throughput_mbps=row["throughput_mbps"],
            avg_latency_ms=row["avg_latency_ms"],
            jitter_ms=row["jitter_ms"],
            utilization_pct=row["utilization_pct"],
            pdr_percent=row["pdr_percent"],
            plr_percent=row["plr_percent"],
            avg_hops=row["avg_hops"],
        )


class EventRepository:
    """CRUD operations for simulation events table."""

    def __init__(self, db: Database):
        self._db = db

    def save(self, ev: EventRecord) -> None:
        self._db.execute(
            """INSERT INTO events (id, experiment_id, timestamp_ms, event_type, target, description)
               VALUES (?,?,?,?,?,?)""",
            (ev.id, ev.experiment_id, ev.timestamp_ms,
             ev.event_type, ev.target, ev.description))
        self._db.commit()

    def save_many(self, records: List[EventRecord]) -> None:
        self._db.executemany(
            """INSERT INTO events (id, experiment_id, timestamp_ms, event_type, target, description)
               VALUES (?,?,?,?,?,?)""",
            [(e.id, e.experiment_id, e.timestamp_ms,
              e.event_type, e.target, e.description)
             for e in records]
        )
        self._db.commit()

    def get_by_experiment(self, experiment_id: str) -> List[EventRecord]:
        rows = self._db.fetchall(
            "SELECT * FROM events WHERE experiment_id=? ORDER BY timestamp_ms",
            (experiment_id,))
        return [EventRecord(
            id=r["id"], experiment_id=r["experiment_id"],
            timestamp_ms=r["timestamp_ms"], event_type=r["event_type"],
            target=r["target"], description=r["description"]
        ) for r in rows]


class TopologyRepository:
    """Saves/loads topology snapshots linked to experiments."""

    def __init__(self, db: Database):
        self._db = db

    def save_snapshot(self, experiment_id: str,
                      nodes: List[Dict[str, Any]],
                      links: List[Dict[str, Any]]) -> None:
        snapshot = json.dumps({"nodes": nodes, "links": links})
        self._db.execute(
            "UPDATE experiments SET topology=? WHERE id=?",
            (snapshot, experiment_id))
        self._db.commit()

    def get_snapshot(self, experiment_id: str) -> Dict[str, Any]:
        row = self._db.fetchone(
            "SELECT topology FROM experiments WHERE id=?", (experiment_id,))
        if row and row["topology"]:
            try:
                return json.loads(row["topology"])
            except (json.JSONDecodeError, TypeError):
                pass
        return {"nodes": [], "links": []}
