"""
NetSimX — Tests: Database Layer (Member 4)
Uses a temp SQLite file for isolation.
"""

import os
import tempfile
import pytest

from database.database import Database
from database.models import (
    ExperimentRepository, MetricsRepository, EventRepository, TopologyRepository,
    ExperimentRecord, MetricsRecord, EventRecord
)


@pytest.fixture
def tmp_db():
    """Creates a temporary SQLite database for each test."""
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
def exp_repo(tmp_db):
    return ExperimentRepository(tmp_db)


@pytest.fixture
def met_repo(tmp_db):
    return MetricsRepository(tmp_db)


@pytest.fixture
def evt_repo(tmp_db):
    return EventRepository(tmp_db)


@pytest.fixture
def topo_repo(tmp_db):
    return TopologyRepository(tmp_db)


# ======================================================================
# ExperimentRepository
# ======================================================================

class TestExperimentRepository:

    def test_create_and_get(self, exp_repo):
        exp = ExperimentRecord(
            name="Test Exp", algorithm="Dijkstra",
            source="PC1", destination="Server1"
        )
        eid = exp_repo.create(exp)
        assert eid == exp.id

        loaded = exp_repo.get_by_id(eid)
        assert loaded is not None
        assert loaded.name == "Test Exp"
        assert loaded.algorithm == "Dijkstra"
        assert loaded.source == "PC1"
        assert loaded.destination == "Server1"
        assert loaded.status == "CREATED"

    def test_get_all(self, exp_repo):
        for i in range(3):
            exp_repo.create(ExperimentRecord(
                name=f"Exp {i}", algorithm="Dijkstra",
                source="PC1", destination="Server1"
            ))
        all_exps = exp_repo.get_all()
        assert len(all_exps) == 3

    def test_update_status(self, exp_repo):
        exp = ExperimentRecord(name="E1", algorithm="Dijkstra",
                               source="A", destination="B")
        exp_repo.create(exp)
        exp_repo.update_status(exp.id, "COMPLETED", duration_ms=500.0)
        loaded = exp_repo.get_by_id(exp.id)
        assert loaded.status == "COMPLETED"
        assert loaded.duration_ms == pytest.approx(500.0)

    def test_delete(self, exp_repo):
        exp = ExperimentRecord(name="ToDelete", algorithm="Dijkstra",
                               source="A", destination="B")
        exp_repo.create(exp)
        exp_repo.delete(exp.id)
        assert exp_repo.get_by_id(exp.id) is None

    def test_get_by_id_not_found(self, exp_repo):
        result = exp_repo.get_by_id("nonexistent-id")
        assert result is None


# ======================================================================
# MetricsRepository
# ======================================================================

class TestMetricsRepository:

    def _make_exp(self, exp_repo):
        exp = ExperimentRecord(name="Metrics Test", algorithm="Dijkstra",
                               source="PC1", destination="Server1")
        exp_repo.create(exp)
        return exp.id

    def test_save_and_retrieve(self, tmp_db, met_repo):
        exp_repo = ExperimentRepository(tmp_db)
        eid = self._make_exp(exp_repo)

        m = MetricsRecord(
            experiment_id=eid, timestamp_ms=1000.0,
            packets_sent=100, packets_delivered=90, packets_dropped=10,
            throughput_mbps=8.5, avg_latency_ms=22.0, jitter_ms=3.0,
            pdr_percent=90.0, plr_percent=10.0
        )
        met_repo.save(m)

        records = met_repo.get_by_experiment(eid)
        assert len(records) == 1
        assert records[0].packets_sent == 100
        assert records[0].throughput_mbps == pytest.approx(8.5)
        assert records[0].avg_latency_ms == pytest.approx(22.0)

    def test_get_final(self, tmp_db, met_repo):
        exp_repo = ExperimentRepository(tmp_db)
        eid = self._make_exp(exp_repo)

        for ts in [100.0, 200.0, 300.0]:
            met_repo.save(MetricsRecord(
                experiment_id=eid, timestamp_ms=ts,
                packets_sent=10, packets_delivered=9, packets_dropped=1
            ))

        final = met_repo.get_final(eid)
        assert final is not None
        assert final.timestamp_ms == pytest.approx(300.0)

    def test_empty_experiment(self, tmp_db, met_repo):
        exp_repo = ExperimentRepository(tmp_db)
        eid = self._make_exp(exp_repo)
        assert met_repo.get_by_experiment(eid) == []
        assert met_repo.get_final(eid) is None


# ======================================================================
# EventRepository
# ======================================================================

class TestEventRepository:

    def _make_exp(self, exp_repo):
        exp = ExperimentRecord(name="Event Test", algorithm="Dijkstra",
                               source="PC1", destination="Server1")
        exp_repo.create(exp)
        return exp.id

    def test_save_and_retrieve(self, tmp_db, evt_repo):
        exp_repo = ExperimentRepository(tmp_db)
        eid = self._make_exp(exp_repo)

        events = [
            EventRecord(experiment_id=eid, timestamp_ms=500.0,
                        event_type="LINK_DOWN", target="L_R1_R2",
                        description="Link R1-R2 failed"),
            EventRecord(experiment_id=eid, timestamp_ms=1000.0,
                        event_type="LINK_UP", target="L_R1_R2",
                        description="Link R1-R2 restored"),
        ]
        evt_repo.save_many(events)

        loaded = evt_repo.get_by_experiment(eid)
        assert len(loaded) == 2
        assert loaded[0].event_type == "LINK_DOWN"
        assert loaded[1].event_type == "LINK_UP"


# ======================================================================
# TopologyRepository
# ======================================================================

class TestTopologyRepository:

    def test_save_and_get(self, tmp_db, topo_repo):
        exp_repo = ExperimentRepository(tmp_db)
        exp = ExperimentRecord(name="Topo Test", algorithm="Dijkstra",
                               source="PC1", destination="Server1")
        exp_repo.create(exp)

        nodes = [{"id": "PC1", "name": "PC1", "type": "PC"}]
        links = [{"id": "L1", "source": "PC1", "destination": "R1"}]
        topo_repo.save_snapshot(exp.id, nodes, links)

        snapshot = topo_repo.get_snapshot(exp.id)
        assert len(snapshot["nodes"]) == 1
        assert len(snapshot["links"]) == 1
        assert snapshot["nodes"][0]["id"] == "PC1"

    def test_empty_snapshot(self, tmp_db, topo_repo):
        exp_repo = ExperimentRepository(tmp_db)
        exp = ExperimentRecord(name="E", algorithm="Dijkstra",
                               source="A", destination="B")
        exp_repo.create(exp)
        snapshot = topo_repo.get_snapshot(exp.id)
        assert snapshot == {"nodes": [], "links": []}
