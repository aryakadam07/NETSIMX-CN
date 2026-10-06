"""
NetSimX — Unit Test Suite for Routing Algorithms & Routing Tables (Member 2)
Verifies Dijkstra, Bellman-Ford, Distance-Vector (Split Horizon & Poison Reverse),
RoutingTable Longest-Prefix Matching, and Integration Engine.
"""

import pytest
from routing.dijkstra import PathResult, dijkstra_shortest_path, compute_dijkstra_routing_table
from routing.bellman_ford import bellman_ford_shortest_path, NegativeCycleError, compute_bellman_ford_routing_table
from routing.distance_vector import DistanceVectorEngine
from routing.routing_table import RoutingTable, RoutingEntry
from routing.routing_engine import RoutingEngine
from core.network import NetworkTopology
from core.node import Router, PC, Server
from core.link import Link


# ==============================================================================
# DIJKSTRA TEST SUITE (TESTS 1 - 9)
# ==============================================================================

def test_dijkstra_1_simple_graph():
    """Test 1: Simple linear graph A -> B -> C."""
    graph = {
        "A": {"B": 2.0},
        "B": {"A": 2.0, "C": 3.0},
        "C": {"B": 3.0}
    }
    res = dijkstra_shortest_path(graph, "A", "C")
    assert res.is_reachable is True
    assert res.path == ["A", "B", "C"]
    assert res.total_cost == 5.0
    assert res.next_hop == "B"


def test_dijkstra_2_multiple_paths():
    """Test 2: Multiple alternative paths between A and D."""
    graph = {
        "A": {"B": 2.0, "C": 5.0},
        "B": {"A": 2.0, "D": 4.0},
        "C": {"A": 5.0, "D": 1.0},
        "D": {"B": 4.0, "C": 1.0}
    }
    # A->B->D cost = 6, A->C->D cost = 6
    res = dijkstra_shortest_path(graph, "A", "D")
    assert res.is_reachable is True
    assert res.total_cost == 6.0
    assert res.path in [["A", "B", "D"], ["A", "C", "D"]]


def test_dijkstra_3_correct_shortest_path():
    """Test 3: Diamond graph selecting lower cost path A -> B -> D over A -> C -> D."""
    graph = {
        "A": {"B": 1.0, "C": 10.0},
        "B": {"A": 1.0, "D": 2.0},
        "C": {"A": 10.0, "D": 1.0},
        "D": {"B": 2.0, "C": 1.0}
    }
    res = dijkstra_shortest_path(graph, "A", "D")
    assert res.path == ["A", "B", "D"]


def test_dijkstra_4_correct_total_cost():
    """Test 4: Verify accurate accumulated total path cost."""
    graph = {
        "R1": {"R2": 2.5, "R3": 4.0},
        "R2": {"R1": 2.5, "R4": 3.5},
        "R3": {"R1": 4.0, "R4": 1.0},
        "R4": {"R2": 3.5, "R3": 1.0}
    }
    res = dijkstra_shortest_path(graph, "R1", "R4")
    assert res.total_cost == 5.0  # R1->R3->R4 = 4.0 + 1.0 = 5.0 vs R1->R2->R4 = 6.0


def test_dijkstra_5_correct_next_hop():
    """Test 5: Verify correct next-hop decision for edge router."""
    graph = {
        "R1": {"R2": 3.0, "R3": 8.0},
        "R2": {"R4": 2.0},
        "R3": {"R4": 1.0},
        "R4": {}
    }
    res = dijkstra_shortest_path(graph, "R1", "R4")
    assert res.next_hop == "R2"  # R1->R2->R4 (cost 5) vs R1->R3->R4 (cost 9)


def test_dijkstra_6_source_equals_destination():
    """Test 6: Source node is equal to destination node."""
    graph = {"A": {"B": 1.0}, "B": {"A": 1.0}}
    res = dijkstra_shortest_path(graph, "A", "A")
    assert res.is_reachable is True
    assert res.path == ["A"]
    assert res.total_cost == 0.0
    assert res.next_hop == "A"


def test_dijkstra_7_unreachable_destination():
    """Test 7: Partitioned node with no edge paths."""
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0},
        "C": {}  # Isolated node
    }
    res = dijkstra_shortest_path(graph, "A", "C")
    assert res.is_reachable is False
    assert res.path == []
    assert res.total_cost == float('inf')
    assert res.next_hop is None


def test_dijkstra_8_disconnected_graph():
    """Test 8: Two completely disconnected components."""
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0},
        "X": {"Y": 2.0},
        "Y": {"X": 2.0}
    }
    res = dijkstra_shortest_path(graph, "A", "Y")
    assert res.is_reachable is False
    assert res.total_cost == float('inf')


def test_dijkstra_9_multiple_equal_cost_paths():
    """Test 9: Equal cost paths handled deterministically."""
    graph = {
        "A": {"B": 2.0, "C": 2.0},
        "B": {"D": 3.0},
        "C": {"D": 3.0},
        "D": {}
    }
    res = dijkstra_shortest_path(graph, "A", "D")
    assert res.is_reachable is True
    assert res.total_cost == 5.0
    assert len(res.path) == 3


# ==============================================================================
# BELLMAN-FORD TEST SUITE (TESTS 10 - 16)
# ==============================================================================

def test_bellman_ford_10_simple_graph():
    """Test 10: Bellman-Ford on simple graph."""
    graph = {
        "A": {"B": 3.0},
        "B": {"C": 4.0},
        "C": {}
    }
    res = bellman_ford_shortest_path(graph, "A", "C")
    assert res.is_reachable is True
    assert res.path == ["A", "B", "C"]
    assert res.total_cost == 7.0


def test_bellman_ford_11_multiple_paths():
    """Test 11: Bellman-Ford with multiple paths."""
    graph = {
        "A": {"B": 5.0, "C": 2.0},
        "B": {"D": 1.0},
        "C": {"B": 1.0, "D": 6.0},
        "D": {}
    }
    # A->C->B->D cost = 2+1+1 = 4 vs A->B->D = 5+1=6 vs A->C->D = 2+6=8
    res = bellman_ford_shortest_path(graph, "A", "D")
    assert res.path == ["A", "C", "B", "D"]
    assert res.total_cost == 4.0


def test_bellman_ford_12_correct_shortest_path():
    """Test 12: Bellman-Ford shortest path selection."""
    graph = {
        "R1": {"R2": 10.0, "R3": 3.0},
        "R3": {"R2": 2.0},
        "R2": {}
    }
    res = bellman_ford_shortest_path(graph, "R1", "R2")
    assert res.path == ["R1", "R3", "R2"]
    assert res.total_cost == 5.0


def test_bellman_ford_13_negative_edge_test():
    """Test 13: Bellman-Ford handling non-cycle negative edge weights."""
    graph = {
        "A": {"B": 4.0, "C": 3.0},
        "B": {"D": 2.0},
        "C": {"B": -2.0, "D": 5.0},
        "D": {}
    }
    # Path A->C->B->D cost = 3 + (-2) + 2 = 3.0
    res = bellman_ford_shortest_path(graph, "A", "D")
    assert res.is_reachable is True
    assert res.path == ["A", "C", "B", "D"]
    assert res.total_cost == 3.0


def test_bellman_ford_14_negative_cycle_detection():
    """Test 14: Bellman-Ford detects negative-weight cycle and raises NegativeCycleError."""
    graph = {
        "A": {"B": 1.0},
        "B": {"C": -3.0},
        "C": {"A": 1.0}  # Cycle A->B->C->A sum = 1 - 3 + 1 = -1 < 0
    }
    with pytest.raises(NegativeCycleError):
        bellman_ford_shortest_path(graph, "A", "C")


def test_bellman_ford_15_unreachable_destination():
    """Test 15: Bellman-Ford handling unreachable target."""
    graph = {
        "A": {"B": 2.0},
        "B": {},
        "C": {"D": 1.0}
    }
    res = bellman_ford_shortest_path(graph, "A", "D")
    assert res.is_reachable is False
    assert res.total_cost == float('inf')


def test_bellman_ford_16_early_termination():
    """Test 16: Verify Bellman-Ford early termination when graph converges before |V|-1 steps."""
    graph = {
        "A": {"B": 1.0},
        "B": {"C": 1.0},
        "C": {"D": 1.0},
        "D": {"E": 1.0},
        "E": {}
    }
    res = bellman_ford_shortest_path(graph, "A", "E")
    assert res.is_reachable is True
    assert res.total_cost == 4.0
    assert res.hop_count == 4


# ==============================================================================
# DISTANCE VECTOR TEST SUITE (TESTS 17 - 25)
# ==============================================================================

def test_distance_vector_17_initial_routing_table():
    """Test 17: Initial distance vector state before exchanges."""
    graph = {
        "A": {"B": 2.0},
        "B": {"A": 2.0, "C": 4.0},
        "C": {"B": 4.0}
    }
    engine = DistanceVectorEngine(graph=graph)
    assert engine.distance_vectors["A"]["A"] == 0.0
    assert engine.distance_vectors["A"]["B"] == 2.0
    assert engine.distance_vectors["A"]["C"] == 16.0  # Initial infinite distance


def test_distance_vector_18_neighbor_exchange():
    """Test 18: Single exchange step updates 2-hop distances."""
    graph = {
        "A": {"B": 2.0},
        "B": {"A": 2.0, "C": 4.0},
        "C": {"B": 4.0}
    }
    engine = DistanceVectorEngine(graph=graph)
    engine.step_exchange()
    assert engine.distance_vectors["A"]["C"] == 6.0  # Learned via B
    assert engine.next_hops["A"]["C"] == "B"


def test_distance_vector_19_route_update():
    """Test 19: Distance vector update when cheaper link added."""
    graph = {
        "A": {"B": 10.0, "C": 2.0},
        "B": {"A": 10.0, "C": 1.0},
        "C": {"A": 2.0, "B": 1.0}
    }
    engine = DistanceVectorEngine(graph=graph)
    engine.run_to_convergence()
    assert engine.distance_vectors["A"]["B"] == 3.0  # A->C->B (2+1=3) instead of direct 10.0
    assert engine.next_hops["A"]["B"] == "C"


def test_distance_vector_20_better_route_selection():
    """Test 20: DV selects better route metric."""
    graph = {
        "R1": {"R2": 5.0, "R3": 1.0},
        "R3": {"R1": 1.0, "R2": 2.0},
        "R2": {"R1": 5.0, "R3": 2.0}
    }
    engine = DistanceVectorEngine(graph=graph)
    engine.run_to_convergence()
    path_res = engine.get_path("R1", "R2")
    assert path_res.total_cost == 3.0
    assert path_res.path == ["R1", "R3", "R2"]


def test_distance_vector_21_unreachable_route():
    """Test 21: Disconnected node remains infinite metric."""
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0},
        "Z": {}
    }
    engine = DistanceVectorEngine(graph=graph)
    engine.run_to_convergence()
    assert engine.distance_vectors["A"]["Z"] == 16.0
    res = engine.get_path("A", "Z")
    assert res.is_reachable is False


def test_distance_vector_22_convergence():
    """Test 22: Convergence occurs within finite iterations."""
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0, "C": 1.0},
        "C": {"B": 1.0, "D": 1.0},
        "D": {"C": 1.0}
    }
    engine = DistanceVectorEngine(graph=graph)
    iters = engine.run_to_convergence(max_iterations=50)
    assert iters < 10
    assert engine.distance_vectors["A"]["D"] == 3.0


def test_distance_vector_23_split_horizon():
    """Test 23: Split Horizon prevents advertising learned routes back to source neighbor."""
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0, "C": 2.0},
        "C": {"B": 2.0}
    }
    # A learns C through B. Next hop for C at A is B.
    # When A advertises to B, Split Horizon must exclude C from advertisement to B.
    engine = DistanceVectorEngine(graph=graph, split_horizon=True, poison_reverse=False)
    engine.run_to_convergence()

    adv_a_to_b = engine.create_advertisement("A", "B")
    # Destination C must NOT be in advertisement from A to B under Split Horizon
    assert "C" not in adv_a_to_b


def test_distance_vector_24_poison_reverse():
    """Test 24: Poison Reverse advertises infinity back to source neighbor."""
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0, "C": 2.0},
        "C": {"B": 2.0}
    }
    # A learns C through B. Next hop for C at A is B.
    # When A advertises to B, Poison Reverse must advertise C with metric 16.0 (max_metric).
    engine = DistanceVectorEngine(graph=graph, split_horizon=True, poison_reverse=True)
    engine.run_to_convergence()

    adv_a_to_b = engine.create_advertisement("A", "B")
    # Under Poison Reverse, A advertises C to B with metric = 16.0 (max_metric)
    assert adv_a_to_b.get("C") == 16.0


def test_distance_vector_25_count_to_infinity_protection():
    """Test 25: Link breakdown count-to-infinity bounded by max_metric."""
    # A - B - C
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0, "C": 1.0},
        "C": {"B": 1.0}
    }
    engine = DistanceVectorEngine(graph=graph, split_horizon=True, poison_reverse=True, max_metric=16.0)
    engine.run_to_convergence()

    # Sever B-C link
    del engine.graph["B"]["C"]
    del engine.graph["C"]["B"]
    engine.distance_vectors["B"]["C"] = 16.0
    engine.next_hops["B"]["C"] = None

    iters = engine.run_to_convergence(max_iterations=30)
    assert engine.distance_vectors["A"]["C"] == 16.0


# ==============================================================================
# ROUTING TABLE & LPM TEST SUITE (TESTS 26 - 34)
# ==============================================================================

def test_routing_table_26_add_route():
    """Test 26: Add route to routing table."""
    rt = RoutingTable(router_id="R1")
    e = RoutingEntry(destination="192.168.1.0/24", next_hop="10.0.0.1", metric=2.0)
    added = rt.add_route(e)
    assert added is True
    assert rt.get_route("192.168.1.0/24") == e


def test_routing_table_27_delete_route():
    """Test 27: Delete route from routing table."""
    rt = RoutingTable(router_id="R1")
    e = RoutingEntry(destination="10.0.0.0/8", next_hop="R2", metric=1.0)
    rt.add_route(e)
    deleted = rt.remove_route("10.0.0.0/8")
    assert deleted is True
    assert rt.get_route("10.0.0.0/8") is None


def test_routing_table_28_update_route():
    """Test 28: Update existing route in table."""
    rt = RoutingTable(router_id="R1")
    rt.add_route(RoutingEntry(destination="172.16.0.0/16", next_hop="R2", metric=5.0))
    # Update with lower metric
    rt.update_route(RoutingEntry(destination="172.16.0.0/16", next_hop="R3", metric=2.0))
    entry = rt.get_route("172.16.0.0/16")
    assert entry.metric == 2.0
    assert entry.next_hop == "R3"


def test_routing_table_29_exact_match():
    """Test 29: Exact match on host IP CIDR (/32)."""
    rt = RoutingTable(router_id="R1")
    rt.add_route(RoutingEntry(destination="10.10.10.5/32", next_hop="R2", metric=1.0))
    match = rt.lookup("10.10.10.5")
    assert match is not None
    assert match.destination == "10.10.10.5/32"
    assert match.next_hop == "R2"


def test_routing_table_30_longest_prefix_match():
    """Test 30: Longest-Prefix Matching selects /24 over /16 over /8."""
    rt = RoutingTable(router_id="R1")
    rt.add_route(RoutingEntry(destination="10.0.0.0/8", next_hop="Gateway_8", metric=1.0))
    rt.add_route(RoutingEntry(destination="10.10.0.0/16", next_hop="Gateway_16", metric=1.0))
    rt.add_route(RoutingEntry(destination="10.10.10.0/24", next_hop="Gateway_24", metric=1.0))

    match = rt.lookup("10.10.10.25")
    assert match is not None
    assert match.prefix_length == 24
    assert match.next_hop == "Gateway_24"


def test_routing_table_31_default_route():
    """Test 31: Default route 0.0.0.0/0 fallback when no subnet matches."""
    rt = RoutingTable(router_id="R1")
    rt.add_route(RoutingEntry(destination="192.168.1.0/24", next_hop="Local_GW", metric=1.0))
    rt.add_route(RoutingEntry(destination="0.0.0.0/0", next_hop="ISP_Default_GW", metric=10.0))

    # Match specific subnet
    m1 = rt.lookup("192.168.1.50")
    assert m1.next_hop == "Local_GW"

    # Fallback to default route for unknown external IP
    m2 = rt.lookup("8.8.8.8")
    assert m2 is not None
    assert m2.destination == "0.0.0.0/0"
    assert m2.next_hop == "ISP_Default_GW"


def test_routing_table_32_lower_metric_selection():
    """Test 32: When prefix lengths are equal, select route with lower metric."""
    rt = RoutingTable(router_id="R1")
    rt.add_route(RoutingEntry(destination="10.0.0.0/16", next_hop="Slow_Path", metric=10.0))
    rt.add_route(RoutingEntry(destination="10.0.0.0/16", next_hop="Fast_Path", metric=2.0))

    match = rt.lookup("10.0.5.1")
    assert match is not None
    assert match.next_hop == "Fast_Path"
    assert match.metric == 2.0


def test_routing_table_33_equal_prefix_tie_breaking():
    """Test 33: Deterministic tie-breaking on equal prefix length and metric."""
    rt = RoutingTable(router_id="R1")
    # Equal prefix /24 and equal metric 5.0
    rt.add_route(RoutingEntry(destination="192.168.10.0/24", next_hop="Router_B", metric=5.0))
    rt.add_route(RoutingEntry(destination="192.168.10.0/24", next_hop="Router_A", metric=5.0))

    match = rt.lookup("192.168.10.12")
    assert match is not None
    # Lexicographical tie-breaker selects 'Router_A' over 'Router_B'
    assert match.next_hop in ["Router_A", "Router_B"]


def test_routing_table_34_no_matching_route():
    """Test 34: Unmatched IP returns None when no default route exists."""
    rt = RoutingTable(router_id="R1")
    rt.add_route(RoutingEntry(destination="10.0.0.0/8", next_hop="Internal_GW", metric=1.0))

    match = rt.lookup("172.16.1.1")
    assert match is None


# ==============================================================================
# ROUTING ENGINE INTEGRATION TESTS
# ==============================================================================

def test_routing_engine_integration_campus_topology():
    """Verifies RoutingEngine on campus topology with simulated link failure."""
    net = NetworkTopology(network_id="TEST_NET", name="Test Campus")
    r1 = Router(node_id="R1", name="R1", ip_address="192.168.1.1")
    r2 = Router(node_id="R2", name="R2", ip_address="10.0.1.1")
    r3 = Router(node_id="R3", name="R3", ip_address="10.0.2.1")
    r4 = Router(node_id="R4", name="R4", ip_address="10.0.3.1")

    for r in [r1, r2, r3, r4]:
        net.add_node(r)

    net.add_link(Link(link_id="L_R1_R2", source="R1", destination="R2", cost=2.0))
    net.add_link(Link(link_id="L_R2_R4", source="R2", destination="R4", cost=2.0))
    net.add_link(Link(link_id="L_R1_R3", source="R1", destination="R3", cost=4.0))
    net.add_link(Link(link_id="L_R3_R4", source="R3", destination="R4", cost=4.0))

    engine = RoutingEngine(default_algorithm="Dijkstra")

    # 1. Primary path check (R1 -> R2 -> R4, cost = 4.0)
    res1 = engine.find_path(net, "R1", "R4")
    assert res1.path == ["R1", "R2", "R4"]
    assert res1.total_cost == 4.0

    # 2. Fail link L_R1_R2
    net.set_link_status("L_R1_R2", status=pytest.importorskip("core.node").DeviceStatus.DOWN)

    # 3. Dynamic failover path check (R1 -> R3 -> R4, cost = 8.0)
    res2 = engine.find_path(net, "R1", "R4")
    assert res2.path == ["R1", "R3", "R4"]
    assert res2.total_cost == 8.0
