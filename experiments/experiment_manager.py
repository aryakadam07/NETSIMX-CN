"""
NetSimX — Experiment Manager (Member 4)
Manages the lifecycle of simulation experiments:
create → start → run → stop → save → load → export.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from database.database import Database
from database.models import (
    ExperimentRecord, MetricsRecord, EventRecord,
    ExperimentRepository, MetricsRepository, EventRepository, TopologyRepository
)
from analytics.metrics import MetricsCalculator
from export.csv_exporter import CsvExporter
from export.json_exporter import JsonExporter

logger = logging.getLogger("ExperimentManager")


class ExperimentManager:
    """
    Single class managing the full experiment lifecycle.
    All database interactions go through repository objects.
    """

    def __init__(self, db: Database):
        self._db = db
        self._exp_repo = ExperimentRepository(db)
        self._met_repo = MetricsRepository(db)
        self._evt_repo = EventRepository(db)
        self._topo_repo = TopologyRepository(db)
        self._active_experiment_id: Optional[str] = None
        self._start_time_ms: float = 0.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create_experiment(self, name: str, algorithm: str,
                          source: str, destination: str,
                          traffic_level: str = "LOW",
                          packet_count: int = 0) -> str:
        """Creates and persists a new experiment. Returns the experiment ID."""
        exp = ExperimentRecord(
            name=name,
            algorithm=algorithm,
            source=source,
            destination=destination,
            traffic_level=traffic_level,
            packet_count=packet_count,
            status="CREATED",
        )
        self._exp_repo.create(exp)
        logger.info(f"Experiment created: {exp.id} — {name}")
        return exp.id

    def start_experiment(self, experiment_id: str) -> None:
        """Marks experiment as RUNNING and records start time."""
        import time
        self._active_experiment_id = experiment_id
        self._start_time_ms = time.monotonic() * 1000.0
        self._exp_repo.update_status(experiment_id, "RUNNING")
        logger.info(f"Experiment {experiment_id} started")

    def stop_experiment(self, experiment_id: str) -> None:
        """Marks experiment as COMPLETED."""
        import time
        duration = 0.0
        if self._start_time_ms > 0:
            duration = time.monotonic() * 1000.0 - self._start_time_ms
        self._exp_repo.update_status(experiment_id, "COMPLETED", duration_ms=duration)
        self._active_experiment_id = None
        logger.info(f"Experiment {experiment_id} stopped (duration={duration:.1f}ms)")

    def abort_experiment(self, experiment_id: str) -> None:
        self._exp_repo.update_status(experiment_id, "ABORTED")
        self._active_experiment_id = None

    # ------------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------------

    def save_results(self, experiment_id: str,
                     stats,
                     snapshots: list,
                     events: Optional[List[Dict[str, Any]]] = None,
                     topology_snapshot: Optional[Dict[str, Any]] = None) -> None:
        """
        Persists final metrics and event log.
        stats: SimulationStats from SimulationEngine
        snapshots: list of SimulationTickSnapshot
        events: optional list of failure event dicts
        topology_snapshot: optional topology dict
        """
        # Build final metrics record
        final = MetricsCalculator.from_sim_stats(stats)
        snap_metrics = MetricsCalculator.from_snapshots(snapshots)

        # Use best available data
        rec = MetricsRecord(
            experiment_id=experiment_id,
            timestamp_ms=getattr(snapshots[-1], "timestamp_ms", 0.0) if snapshots else 0.0,
            packets_sent=final["packets_sent"],
            packets_delivered=final["packets_delivered"],
            packets_dropped=final["packets_dropped"],
            throughput_mbps=snap_metrics["throughput_mbps"],
            avg_latency_ms=final["avg_latency_ms"],
            jitter_ms=snap_metrics["jitter_ms"],
            pdr_percent=final["pdr_percent"],
            plr_percent=final["plr_percent"],
            avg_hops=final["avg_hops"],
        )
        self._met_repo.save(rec)

        # Save events
        if events:
            event_records = [
                EventRecord(
                    experiment_id=experiment_id,
                    timestamp_ms=ev.get("timestamp_ms", 0.0),
                    event_type=ev.get("event_type", ""),
                    target=ev.get("target", ""),
                    description=ev.get("description", ""),
                )
                for ev in events
            ]
            self._evt_repo.save_many(event_records)

        # Save topology snapshot
        if topology_snapshot:
            self._topo_repo.save_snapshot(
                experiment_id,
                topology_snapshot.get("nodes", []),
                topology_snapshot.get("links", [])
            )

        logger.info(f"Results saved for experiment {experiment_id}")

    # ------------------------------------------------------------------
    # Load / List
    # ------------------------------------------------------------------

    def load_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        return self._exp_repo.get_by_id(experiment_id)

    def list_experiments(self) -> List[ExperimentRecord]:
        return self._exp_repo.get_all()

    def get_experiment_metrics(self, experiment_id: str) -> Optional[MetricsRecord]:
        return self._met_repo.get_final(experiment_id)

    def get_experiment_events(self, experiment_id: str) -> List[EventRecord]:
        return self._evt_repo.get_by_experiment(experiment_id)

    def get_experiment_topology(self, experiment_id: str) -> Dict[str, Any]:
        return self._topo_repo.get_snapshot(experiment_id)

    def delete_experiment(self, experiment_id: str) -> None:
        self._exp_repo.delete(experiment_id)
        logger.info(f"Experiment {experiment_id} deleted")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _build_export_dict(self, experiment_id: str) -> Dict[str, Any]:
        exp = self._exp_repo.get_by_id(experiment_id)
        if not exp:
            return {}
        metrics = self._met_repo.get_final(experiment_id)
        events = self._evt_repo.get_by_experiment(experiment_id)
        topo = self._topo_repo.get_snapshot(experiment_id)

        config = {
            "id": exp.id,
            "name": exp.name,
            "created_at": exp.created_at,
            "algorithm": exp.algorithm,
            "source": exp.source,
            "destination": exp.destination,
            "traffic_level": exp.traffic_level,
            "packet_count": exp.packet_count,
            "duration_ms": exp.duration_ms,
            "status": exp.status,
        }

        metrics_dict: Dict[str, Any] = {}
        if metrics:
            metrics_dict = {
                "packets_sent": metrics.packets_sent,
                "packets_delivered": metrics.packets_delivered,
                "packets_dropped": metrics.packets_dropped,
                "throughput_mbps": metrics.throughput_mbps,
                "avg_latency_ms": metrics.avg_latency_ms,
                "jitter_ms": metrics.jitter_ms,
                "pdr_percent": metrics.pdr_percent,
                "plr_percent": metrics.plr_percent,
            }

        events_list = [
            {
                "timestamp_ms": e.timestamp_ms,
                "event_type": e.event_type,
                "target": e.target,
                "description": e.description,
            }
            for e in events
        ]

        return {
            "config": config,
            "metrics": metrics_dict,
            "events": events_list,
            "topology": topo,
        }

    def export_csv(self, experiment_id: str, filepath: str) -> None:
        data = self._build_export_dict(experiment_id)
        CsvExporter.export_full_experiment(data, filepath)

    def export_json(self, experiment_id: str, filepath: str) -> None:
        data = self._build_export_dict(experiment_id)
        JsonExporter.export_full_experiment(data, filepath)

    # ------------------------------------------------------------------
    # Active experiment
    # ------------------------------------------------------------------

    @property
    def active_experiment_id(self) -> Optional[str]:
        return self._active_experiment_id
