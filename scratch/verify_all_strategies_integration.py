"""
NetSimX — Comprehensive Multi-Module Integration & Strategy Verification Script
Tests integration between Member 1 (Topology), Member 2 (Routing), and Member 3 (Simulation Core).
"""

import sys
from core.node import Router, PC, Server, DeviceStatus
from core.link import Link
from core.network import NetworkTopology
from core.packet import Packet
from core.event_manager import EventManager, EventType
from core.simulation import SimulationEngine
from failures.failure_manager import FailureManager
from traffic.generator import TrafficGenerator
from traffic.flow import FlowConfig
from routing.routing_engine import RoutingEngine
from routing.routing_table import RoutingTable, RoutingEntry


def build_test_network() -> NetworkTopology:
    net = NetworkTopology(network_id="INT_NET", name="Integration Network")
    pc1 = PC(node_id="PC1", name="PC1", ip_address="192.168.1.10")
    r1 = Router(node_id="R1", name="R1", ip_address="192.168.1.1")
    r2 = Router(node_id="R2", name="R2", ip_address="10.0.1.1")
    r3 = Router(node_id="R3", name="R3", ip_address="10.0.2.1")
    r4 = Router(node_id="R4", name="R4", ip_address="10.0.3.1")
    srv1 = Server(node_id="Server1", name="Server1", ip_address="172.16.1.100")

    for node in [pc1, r1, r2, r3, r4, srv1]:
        net.add_node(node)

    links = [
        Link(link_id="L_PC1_R1", source="PC1", destination="R1", cost=1.0, bandwidth_mbps=100.0, delay_ms=5.0),
        Link(link_id="L_R1_R2", source="R1", destination="R2", cost=2.0, bandwidth_mbps=100.0, delay_ms=10.0),
        Link(link_id="L_R2_R4", source="R2", destination="R4", cost=2.0, bandwidth_mbps=100.0, delay_ms=10.0),
        Link(link_id="L_R1_R3", source="R1", destination="R3", cost=4.0, bandwidth_mbps=100.0, delay_ms=12.0),
        Link(link_id="L_R3_R4", source="R3", destination="R4", cost=4.0, bandwidth_mbps=100.0, delay_ms=12.0),
        Link(link_id="L_R4_SRV", source="R4", destination="Server1", cost=1.0, bandwidth_mbps=100.0, delay_ms=5.0),
    ]
    for link in links:
        net.add_link(link)

    return net


def test_strategy(algorithm: str):
    print(f"\n--- Testing Strategy: {algorithm} ---")
    net = build_test_network()
    routing_engine = RoutingEngine(default_algorithm=algorithm)

    # 1. Path computation test
    path_res = routing_engine.find_path(net, "PC1", "Server1", algorithm=algorithm)
    assert path_res.is_reachable is True
    print(f"Primary Path ({algorithm}): {' -> '.join(path_res.path)} (Cost: {path_res.total_cost:.1f})")

    # 2. Routing Table Generation & LPM lookup test
    rt = routing_engine.generate_table_for_router(net, "R1", algorithm=algorithm)
    print(f"Generated Routing Table for R1 ({algorithm}):\n{rt.display_table()}")
    
    match = rt.lookup("10.0.1.1")
    if match:
        print(f"LPM Lookup '10.0.1.1' -> Next Hop: {match.next_hop} (Metric: {match.metric})")

    # 3. Simulation Engine Integration with Dynamic Failover
    fail_mgr = FailureManager(net)
    event_mgr = EventManager(failure_manager=fail_mgr)
    sim_engine = SimulationEngine(network=net, event_manager=event_mgr)

    # Dynamic failover hook
    sim_engine.on_route_failed = routing_engine.create_reroute_handler(net, algorithm=algorithm)

    # Schedule fault: Link L_R1_R2 fails at t = 50ms
    event_mgr.schedule(trigger_time_ms=50.0, event_type=EventType.LINK_DOWN, target_id="L_R1_R2")

    # Generate traffic flow
    flow = FlowConfig(flow_id=f"FLOW_{algorithm}", source_id="PC1", destination_id="Server1", packet_count=20)
    packets = TrafficGenerator.generate_flow(flow, path_res.path)
    sim_engine.load_packets(packets)

    stats = sim_engine.run_all(max_steps=100, tick_interval_ms=25.0)

    print(f"Simulation Stats ({algorithm}): Sent={stats.packets_sent}, Delivered={stats.packets_delivered}, "
          f"Dropped={stats.packets_dropped}, PDR={stats.pdr_percent:.1f}%")
    assert stats.packets_delivered == stats.packets_sent
    assert stats.packets_dropped == 0


def main():
    print("=================================================================")
    print(" NETSIMX MULTI-MODULE INTEGRATION & ERROR HANDLING VERIFICATION")
    print("=================================================================")
    for algo in ["Dijkstra", "Bellman-Ford", "Distance-Vector"]:
        test_strategy(algo)
    print("\n=================================================================")
    print(" ALL STRATEGIES & MODULE INTERFACES VERIFIED 100% OPERATIONAL!")
    print("=================================================================")


if __name__ == "__main__":
    main()
