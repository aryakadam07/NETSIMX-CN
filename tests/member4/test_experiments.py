"""
NetSimX — Tests: Experiment Manager (Member 4)
"""

import os
import json
import tempfile
import pytest

from database.database import Database
from experiments.experiment_manager import ExperimentManager


@pytest.fixture
def tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    db.initialize()
    yield db
    db.close()
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def mgr(tmp_db):
    return ExperimentManager(tmp_db)


class MockStats:
    packets_sent = 200
    packets_delivered = 180
    packets_dropped = 20
    total_latency_ms = 3600.0   # 20ms avg
    total_hops = 540            # 3 avg hops

    @property
    def pdr_percent(self):
        return (self.packets_delivered / self.packets_sent) * 100

    @property
    def plr_percent(self):
        return (self.packets_dropped / self.packets_sent) * 100

    @property
    def average_delay_ms(self):
        return self.total_latency_ms / self.packets_delivered if self.packets_delivered else 0.0

    @property
    def average_hops(self):
        return self.total_hops / self.packets_delivered if self.packets_delivered else 0.0


class TestExperimentManager:

    def test_create_experiment(self, mgr):
        eid = mgr.create_experiment(
            name="Test Run 1",
            algorithm="Dijkstra",
            source="PC1",
            destination="Server1",
            traffic_level="LOW",
            packet_count=100,
        )
        assert eid is not None
        assert len(eid) > 0

    def test_list_experiments_empty(self, mgr):
        assert mgr.list_experiments() == []

    def test_list_experiments(self, mgr):
        mgr.create_experiment("E1", "Dijkstra", "PC1", "Server1")
        mgr.create_experiment("E2", "Bellman-Ford", "PC1", "Server1")
        exps = mgr.list_experiments()
        assert len(exps) == 2

    def test_load_experiment(self, mgr):
        eid = mgr.create_experiment("LoadTest", "Dijkstra", "PC1", "Server1")
        loaded = mgr.load_experiment(eid)
        assert loaded is not None
        assert loaded.name == "LoadTest"
        assert loaded.algorithm == "Dijkstra"

    def test_start_stop_experiment(self, mgr):
        eid = mgr.create_experiment("StartStop", "Dijkstra", "PC1", "Server1")
        mgr.start_experiment(eid)
        loaded = mgr.load_experiment(eid)
        assert loaded.status == "RUNNING"

        mgr.stop_experiment(eid)
        loaded = mgr.load_experiment(eid)
        assert loaded.status == "COMPLETED"

    def test_save_results(self, mgr):
        eid = mgr.create_experiment("ResultTest", "Dijkstra", "PC1", "Server1",
                                    packet_count=200)
        mgr.start_experiment(eid)

        # Build mock snapshots
        class MockSnap:
            def __init__(self, t, d, dr, pdr, lat):
                self.timestamp_ms = t
                self.packets_delivered = d
                self.packets_dropped = dr
                self.pdr_percent = pdr
                self.average_delay_ms = lat
                self.active_packets_count = 0
                self.executed_events = []
                self.queue_depths = {}

        snapshots = [MockSnap(i * 50, i * 9, i, 90.0, 20.0) for i in range(1, 11)]
        mgr.save_results(eid, MockStats(), snapshots)
        mgr.stop_experiment(eid)

        metrics = mgr.get_experiment_metrics(eid)
        assert metrics is not None
        assert metrics.packets_sent == 200
        assert metrics.packets_delivered == 180
        assert metrics.packets_dropped == 20
        assert metrics.pdr_percent == pytest.approx(90.0)
        assert metrics.plr_percent == pytest.approx(10.0)

    def test_delete_experiment(self, mgr):
        eid = mgr.create_experiment("DeleteMe", "Dijkstra", "A", "B")
        mgr.delete_experiment(eid)
        assert mgr.load_experiment(eid) is None
        assert len(mgr.list_experiments()) == 0

    def test_export_json(self, mgr):
        eid = mgr.create_experiment("JsonExport", "Dijkstra", "PC1", "Server1",
                                    packet_count=100)
        mgr.start_experiment(eid)
        mgr.save_results(eid, MockStats(), [])
        mgr.stop_experiment(eid)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            mgr.export_json(eid, path)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "config" in data
            assert "metrics" in data
            assert data["config"]["algorithm"] == "Dijkstra"
        finally:
            os.unlink(path)

    def test_export_csv(self, mgr):
        eid = mgr.create_experiment("CsvExport", "Bellman-Ford", "PC1", "Server1",
                                    packet_count=100)
        mgr.start_experiment(eid)
        mgr.save_results(eid, MockStats(), [])
        mgr.stop_experiment(eid)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            mgr.export_csv(eid, path)
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "algorithm" in content.lower() or "EXPERIMENT" in content
        finally:
            os.unlink(path)

    def test_get_events_empty(self, mgr):
        eid = mgr.create_experiment("NoEvents", "Dijkstra", "A", "B")
        events = mgr.get_experiment_events(eid)
        assert events == []

    def test_save_events(self, mgr):
        eid = mgr.create_experiment("WithEvents", "Dijkstra", "PC1", "Server1")
        mgr.start_experiment(eid)
        events = [
            {"timestamp_ms": 500.0, "event_type": "LINK_DOWN",
             "target": "L_R1_R2", "description": "Link failed"},
        ]
        mgr.save_results(eid, MockStats(), [], events=events)
        mgr.stop_experiment(eid)

        loaded_events = mgr.get_experiment_events(eid)
        assert len(loaded_events) == 1
        assert loaded_events[0].event_type == "LINK_DOWN"

    def test_abort_experiment(self, mgr):
        eid = mgr.create_experiment("Abort", "Dijkstra", "A", "B")
        mgr.start_experiment(eid)
        mgr.abort_experiment(eid)
        loaded = mgr.load_experiment(eid)
        assert loaded.status == "ABORTED"
