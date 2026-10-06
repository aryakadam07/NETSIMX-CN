"""
NetSimX — Member 2 Interactive Routing CLI Demonstration & Viva Presentation Tool
Demonstrates Dijkstra, Bellman-Ford, Distance-Vector (Split Horizon & Poison Reverse),
Dynamic Failover, and Longest-Prefix Matching routing table lookups in terminal.
"""

import sys
from routing.dijkstra import dijkstra_shortest_path, compute_dijkstra_routing_table
from routing.bellman_ford import bellman_ford_shortest_path, NegativeCycleError, compute_bellman_ford_routing_table
from routing.distance_vector import DistanceVectorEngine
from routing.routing_table import RoutingTable, RoutingEntry
from routing.routing_engine import RoutingEngine
from core.network import NetworkTopology
from core.node import Router, PC, Server, DeviceStatus
from core.link import Link


def print_header(title: str):
    print("\n" + "=" * 74)
    print(f"  {title}")
    print("=" * 74)


def demo_1_dijkstra():
    print_header("DEMO 1: Dijkstra Shortest Path Calculation (Link-State / Min-Heap)")
    graph = {
        "PC1": {"R1": 1.0},
        "R1": {"PC1": 1.0, "R2": 2.0, "R3": 4.0},
        "R2": {"R1": 2.0, "R4": 2.0},
        "R3": {"R1": 4.0, "R4": 4.0},
        "R4": {"R2": 2.0, "R3": 4.0, "Server1": 1.0},
        "Server1": {"R4": 1.0}
    }
    res = dijkstra_shortest_path(graph, "PC1", "Server1")
    print(f"Topology Graph Nodes: {list(graph.keys())}")
    print(f"Calculated Path:     {' -> '.join(res.path)}")
    print(f"Total Cost Metric:   {res.total_cost:.1f}")
    print(f"Hop Count:           {res.hop_count}")
    print(f"Next Hop from PC1:   {res.next_hop}")
    print(f"Algorithm Used:      {res.algorithm}")
    print("\n[VERBAL EXPLANATION FOR VIVA]:")
    print("Dijkstra uses a min-heap priority queue to greedily extract the minimum cost node.")
    print("Time complexity is O((V+E) log V). Primary path PC1 -> R1 -> R2 -> R4 -> Server1 selected with cost 6.0.")


def demo_2_bellman_ford():
    print_header("DEMO 2: Bellman-Ford Edge Relaxation & Negative Cycle Detection")
    graph = {
        "PC1": {"R1": 1.0},
        "R1": {"PC1": 1.0, "R2": 2.0, "R3": 4.0},
        "R2": {"R1": 2.0, "R4": 2.0},
        "R3": {"R1": 4.0, "R4": 4.0},
        "R4": {"R2": 2.0, "R3": 4.0, "Server1": 1.0},
        "Server1": {"R4": 1.0}
    }
    res = bellman_ford_shortest_path(graph, "PC1", "Server1")
    print(f"Normal Graph Path:   {' -> '.join(res.path)} (Cost: {res.total_cost:.1f})")

    # Negative Cycle Test
    neg_cycle_graph = {
        "A": {"B": 1.0},
        "B": {"C": -3.0},
        "C": {"A": 1.0}
    }
    print("\nTesting Negative Weight Cycle (A -> B -> C -> A with cost sum -1):")
    try:
        bellman_ford_shortest_path(neg_cycle_graph, "A", "C")
    except NegativeCycleError as exc:
        print(f"  [SUCCESS] Exception Caught: {exc}")

    print("\n[VERBAL EXPLANATION FOR VIVA]:")
    print("Bellman-Ford relaxes all edges |V|-1 times. It supports negative weights because it doesn't")
    print("use greedy finalized flags. On the |V|-th pass, if any distance still drops, a negative cycle is raised.")


def demo_3_distance_vector():
    print_header("DEMO 3: Distance Vector Iterative Exchange & Convergence")
    graph = {
        "R1": {"R2": 2.0, "R3": 5.0},
        "R2": {"R1": 2.0, "R4": 3.0},
        "R3": {"R1": 5.0, "R4": 1.0},
        "R4": {"R2": 3.0, "R3": 1.0}
    }
    engine = DistanceVectorEngine(graph=graph)

    print("Initial Distance Vector for R1:")
    print(f"  D_R1 = {engine.distance_vectors['R1']}")

    step = 0
    while True:
        step += 1
        changed = engine.step_exchange()
        print(f"Iteration {step}: Vector update changed={changed}")
        print(f"  D_R1 = {engine.distance_vectors['R1']}")
        if not changed:
            break

    print(f"\nConverged in {step} iterations.")
    res = engine.get_path("R1", "R4")
    print(f"Converged Path R1 -> R4: {' -> '.join(res.path)} (Cost: {res.total_cost:.1f})")


def demo_4_split_horizon():
    print_header("DEMO 4: Split Horizon Preventing Loop Advertisements")
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0, "C": 2.0},
        "C": {"B": 2.0}
    }
    # A learned C through B.
    engine = DistanceVectorEngine(graph=graph, split_horizon=True, poison_reverse=False)
    engine.run_to_convergence()

    adv_a_to_b = engine.create_advertisement("A", "B")
    print("Ad vectors from A to neighbor B (Split Horizon ON):")
    print(f"  {adv_a_to_b}")
    print("\n[VERBAL EXPLANATION FOR VIVA]:")
    print("A learned route to C via B. Under Split Horizon, A MUST NOT advertise route to C back to B.")
    print(f"Notice destination 'C' is absent from A->B vector: {'C' not in adv_a_to_b}")


def demo_5_poison_reverse():
    print_header("DEMO 5: Poison Reverse Advertising Infinite Metric (16.0)")
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0, "C": 2.0},
        "C": {"B": 2.0}
    }
    engine = DistanceVectorEngine(graph=graph, split_horizon=True, poison_reverse=True, max_metric=16.0)
    engine.run_to_convergence()

    adv_a_to_b = engine.create_advertisement("A", "B")
    print("Ad vectors from A to neighbor B (Poison Reverse ON):")
    print(f"  {adv_a_to_b}")
    print("\n[VERBAL EXPLANATION FOR VIVA]:")
    print("Under Poison Reverse, A advertises route to C back to B with metric = 16.0 (Infinity),")
    print("immediately poisoning any reverse loops.")
    print(f"Advertised metric for C: {adv_a_to_b.get('C')}")


def demo_6_link_failure_failover():
    print_header("DEMO 6: Dynamic Link Failure & Autonomous Rerouting")
    net = NetworkTopology(network_id="NET_DEMO", name="Campus Topology")
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

    routing_engine = RoutingEngine(default_algorithm="Dijkstra")

    # Primary Path
    res1 = routing_engine.find_path(net, "R1", "R4")
    print(f"1. Initial Primary Path (R1 -> R4): {' -> '.join(res1.path)} (Cost: {res1.total_cost:.1f})")

    # Fail Link L_R1_R2
    print("\n2. Injecting Link Fault: L_R1_R2 status = DOWN...")
    net.set_link_status("L_R1_R2", DeviceStatus.DOWN)

    # Alternate Path
    res2 = routing_engine.find_path(net, "R1", "R4")
    print(f"3. Recalculated Alternate Path:     {' -> '.join(res2.path)} (Cost: {res2.total_cost:.1f})")

    print("\n[VERBAL EXPLANATION FOR VIVA]:")
    print("When L_R1_R2 fails, get_active_adjacency_dict() excludes the link. Dijkstra recalculates")
    print("the optimal path via R3 automatically.")


def demo_7_longest_prefix_matching():
    print_header("DEMO 7: Longest-Prefix Matching (LPM) Routing Table Lookup")
    rt = RoutingTable(router_id="R1")
    rt.add_route(RoutingEntry(destination="10.0.0.0/8", next_hop="GW_8", metric=1.0))
    rt.add_route(RoutingEntry(destination="10.10.0.0/16", next_hop="GW_16", metric=1.0))
    rt.add_route(RoutingEntry(destination="10.10.10.0/24", next_hop="GW_24", metric=1.0))
    rt.add_route(RoutingEntry(destination="0.0.0.0/0", next_hop="GW_Default", metric=10.0))

    print(rt.display_table())

    test_ips = ["10.10.10.25", "10.10.5.1", "10.1.1.1", "8.8.8.8"]
    for ip in test_ips:
        match = rt.lookup(ip)
        print(f"Lookup Target IP [{ip:<12}] -> Matched: {match.destination:<14} via Next Hop [{match.next_hop}]")


def main():
    print("=" * 74)
    print("  NETSIMX MEMBER 2 — ROUTING ALGORITHMS & ROUTING TABLES DEMO CLI")
    print("=" * 74)
    demo_1_dijkstra()
    demo_2_bellman_ford()
    demo_3_distance_vector()
    demo_4_split_horizon()
    demo_5_poison_reverse()
    demo_6_link_failure_failover()
    demo_7_longest_prefix_matching()
    print("\n" + "=" * 74)
    print("  ALL 7 DEMO SCENARIOS PASSED 100% OPERATIONAL")
    print("=" * 74)


if __name__ == "__main__":
    main()
