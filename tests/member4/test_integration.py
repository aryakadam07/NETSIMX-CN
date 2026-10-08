"""
NetSimX — Tests: Integration Adapters (Member 4)
Tests TopologyAdapter, RoutingAdapter, and FailureAdapter
using the actual core modules from Members 1-3.
"""

import pytest
from integration.topology_adapter import TopologyAdapter
from integration.routing_adapter import RoutingAdapter
from integration.failure_adapter import FailureAdapter


@pytest.fixture
def topo():
    """Creates a fresh demo topology adapter."""
    return TopologyAdapter()


@pytest.fixture
def routing(topo):
    return RoutingAdapter(topo)


@pytest.fixture
def failure(topo):
    return FailureAdapter(topo)


# ======================================================================
# TopologyAdapter
# ======================================================================

class TestTopologyAdapter:

    def test_demo_topology_has_nodes(self, topo):
        nodes = topo.get_nodes()
        assert len(nodes) >= 6

    def test_demo_topology_has_links(self, topo):
        links = topo.get_links()
        assert len(links) >= 6

    def test_node_ids_non_empty(self, topo):
        ids = topo.get_node_ids()
        assert "PC1" in ids
        assert "Server1" in ids

    def test_link_ids_non_empty(self, topo):
        ids = topo.get_link_ids()
        assert len(ids) > 0

    def test_node_dict_fields(self, topo):
        nodes = topo.get_nodes()
        for n in nodes:
            assert "id" in n
            assert "name" in n
            assert "type" in n
            assert "is_up" in n
            assert "status" in n
            assert "ip" in n

    def test_link_dict_fields(self, topo):
        links = topo.get_links()
        for l in links:
            assert "id" in l
            assert "source" in l
            assert "destination" in l
            assert "cost" in l
            assert "is_up" in l

    def test_get_node_status(self, topo):
        status = topo.get_node_status("PC1")
        assert status == "UP"

    def test_set_node_status_down_and_up(self, topo):
        topo.set_node_status("R1", False)
        assert topo.get_node_status("R1") == "DOWN"
        topo.set_node_status("R1", True)
        assert topo.get_node_status("R1") == "UP"

    def test_get_topology_stats(self, topo):
        stats = topo.get_topology_stats()
        assert stats["total_nodes"] >= 6
        assert stats["total_links"] >= 6
        assert stats["routers"] >= 4
        assert stats["pcs"] >= 1
        assert stats["servers"] >= 1

    def test_adjacency_graph_non_empty(self, topo):
        graph = topo.get_adjacency_graph()
        assert len(graph) > 0
        # All nodes in graph should be up
        for node_id, neighbors in graph.items():
            assert isinstance(neighbors, dict)


# ======================================================================
# RoutingAdapter
# ======================================================================

class TestRoutingAdapter:

    def test_available_algorithms(self, routing):
        algos = routing.get_available_algorithms()
        assert "Dijkstra" in algos
        assert "Bellman-Ford" in algos
        assert "Distance Vector" in algos
        assert len(algos) == 3

    def test_dijkstra_finds_route(self, routing):
        result = routing.find_route("PC1", "Server1", "Dijkstra")
        assert result["reachable"] is True
        assert result["path"][0] == "PC1"
        assert result["path"][-1] == "Server1"
        assert result["hops"] >= 2
        assert result["cost"] > 0
        assert result["next_hop"] is not None
        assert result["error"] is None

    def test_bellman_ford_finds_route(self, routing):
        result = routing.find_route("PC1", "Server1", "Bellman-Ford")
        assert result["reachable"] is True
        assert result["path"][0] == "PC1"
        assert result["path"][-1] == "Server1"

    def test_distance_vector_finds_route(self, routing):
        result = routing.find_route("PC1", "Server1", "Distance Vector")
        assert result["reachable"] is True

    def test_same_source_dest(self, routing):
        result = routing.find_route("PC1", "PC1", "Dijkstra")
        # Same source/dest — may return unreachable or trivial path
        # We just check it doesn't crash
        assert "reachable" in result
        assert "path" in result

    def test_invalid_source(self, routing):
        result = routing.find_route("DOES_NOT_EXIST", "Server1", "Dijkstra")
        assert result["reachable"] is False
        assert result["error"] is not None

    def test_route_result_has_required_keys(self, routing):
        result = routing.find_route("PC1", "Server1", "Dijkstra")
        for key in ["path", "cost", "hops", "algorithm", "reachable", "error", "next_hop"]:
            assert key in result

    def test_dijkstra_vs_bellman_ford_same_path(self, routing):
        """On a positive-cost graph, Dijkstra and Bellman-Ford should agree."""
        d = routing.find_route("PC1", "Server1", "Dijkstra")
        b = routing.find_route("PC1", "Server1", "Bellman-Ford")
        if d["reachable"] and b["reachable"]:
            assert d["cost"] == pytest.approx(b["cost"], rel=1e-3)

    def test_routing_table_for_router(self, routing):
        table = routing.build_routing_table("R1", "Dijkstra")
        assert isinstance(table, list)
        assert len(table) > 0
        for entry in table:
            assert "destination" in entry
            assert "next_hop" in entry
            assert "metric" in entry


# ======================================================================
# FailureAdapter
# ======================================================================

class TestFailureAdapter:

    def test_fail_node(self, topo, failure):
        result = failure.fail_node("R2")
        assert result is True
        assert topo.get_node_status("R2") == "DOWN"
        assert "R2" in failure.get_failed_nodes()

    def test_restore_node(self, topo, failure):
        failure.fail_node("R2")
        result = failure.restore_node("R2")
        assert result is True
        assert topo.get_node_status("R2") == "UP"
        assert "R2" not in failure.get_failed_nodes()

    def test_fail_link(self, topo, failure):
        link_ids = topo.get_link_ids()
        assert len(link_ids) > 0
        lid = link_ids[0]
        result = failure.fail_link(lid)
        assert result is True
        assert topo.get_link_status(lid) == "DOWN"
        assert lid in failure.get_failed_links()

    def test_restore_link(self, topo, failure):
        lid = topo.get_link_ids()[0]
        failure.fail_link(lid)
        result = failure.restore_link(lid)
        assert result is True
        assert topo.get_link_status(lid) == "UP"
        assert lid not in failure.get_failed_links()

    def test_fail_unknown_node(self, failure):
        result = failure.fail_node("GHOST_NODE_999")
        assert result is False

    def test_fail_unknown_link(self, failure):
        result = failure.fail_link("GHOST_LINK_999")
        assert result is False

    def test_no_failures_initially(self, failure):
        assert failure.get_failed_nodes() == []
        assert failure.get_failed_links() == []

    def test_routing_avoids_failed_node(self, topo, routing, failure):
        """After failing R2, the route should no longer pass through R2."""
        failure.fail_node("R2")
        result = routing.find_route("PC1", "Server1", "Dijkstra")
        if result["reachable"]:
            assert "R2" not in result["path"]
        # Restore for other tests
        failure.restore_node("R2")
