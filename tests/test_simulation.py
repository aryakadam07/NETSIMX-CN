"""
Unit & Integration Tests for Simulation Engine & Failures (Member 3)
"""

import pytest
from core.node import Router, PC, Server
from core.link import Link
from core.network import NetworkTopology
from core.packet import Packet, DropReason
from core.simulation import SimulationEngine
from failures.failure_manager import FailureManager
from traffic.generator import TrafficGenerator
from traffic.flow import FlowConfig


def build_sample_topology() -> NetworkTopology:
    """
    Constructs a reference 4-node topology:
    PC1 --- R1 --- R2 --- Server1
            |              |
            +----- R3 -----+
    """
    net = NetworkTopology(network_id="NET1", name="Sample Campus")

    # Add devices
    pc1 = PC(node_id="PC1", name="Host 1", ip_address="192.168.1.10")
    r1 = Router(node_id="R1", name="Router 1", ip_address="192.168.1.1")
    r2 = Router(node_id="R2", name="Router 2", ip_address="10.0.1.1")
    r3 = Router(node_id="R3", name="Router 3", ip_address="10.0.2.1")
    server1 = Server(node_id="Server1", name="Web Server", ip_address="172.16.1.10")

    for node in [pc1, r1, r2, r3, server1]:
        net.add_node(node)

    # Add links
    l1 = Link(link_id="L_PC1_R1", source="PC1", destination="R1", cost=1.0, bandwidth_mbps=100.0, delay_ms=5.0)
    l2 = Link(link_id="L_R1_R2", source="R1", destination="R2", cost=2.0, bandwidth_mbps=100.0, delay_ms=10.0)
    l3 = Link(link_id="L_R2_SRV", source="R2", destination="Server1", cost=1.0, bandwidth_mbps=100.0, delay_ms=5.0)
    l4 = Link(link_id="L_R1_R3", source="R1", destination="R3", cost=4.0, bandwidth_mbps=100.0, delay_ms=10.0)
    l5 = Link(link_id="L_R3_SRV", source="R3", destination="Server1", cost=4.0, bandwidth_mbps=100.0, delay_ms=10.0)

    for link in [l1, l2, l3, l4, l5]:
        net.add_link(link)

    return net


def test_simulation_healthy_traffic_delivery():
    """Verifies that packets traverse PC1 -> R1 -> R2 -> Server1 with 100% PDR."""
    net = build_sample_topology()
    engine = SimulationEngine(net)

    route = ["PC1", "R1", "R2", "Server1"]
    config = FlowConfig(flow_id="FLOW1", source_id="PC1", destination_id="Server1", packet_count=20)
    packets = TrafficGenerator.generate_flow(config, route)

    engine.load_packets(packets)
    stats = engine.run_all()

    assert stats.packets_sent == 20
    assert stats.packets_delivered == 20
    assert stats.packets_dropped == 0
    assert stats.pdr_percent == 100.0
    assert stats.average_hops == 3.0  # PC1 -> R1 -> R2 -> Server1 = 3 hops
    assert stats.average_delay_ms > 0.0


def test_simulation_link_failure_drops_packets_without_reroute():
    """Verifies that severed link causes packet drops if no alternate route is provided."""
    net = build_sample_topology()
    failure_mgr = FailureManager(net)
    engine = SimulationEngine(net)

    # Fail Link R1-R2
    failure_mgr.fail_link("L_R1_R2", timestamp_ms=100.0)

    route = ["PC1", "R1", "R2", "Server1"]
    p = Packet(packet_id="P1", flow_id="F1", source_id="PC1", destination_id="Server1", route=route)
    engine.load_packets([p])

    # First step moves to R1
    engine.step_packet(p)
    assert p.current_node == "R1"

    # Second step encounters failed link R1-R2
    engine.step_packet(p)
    assert p.is_dropped is True
    assert p.drop_reason == DropReason.NO_ROUTE


def test_simulation_dynamic_rerouting_and_convergence():
    """Verifies in-flight dynamic rerouting via R3 upon R1-R2 link failure."""
    net = build_sample_topology()
    failure_mgr = FailureManager(net)
    engine = SimulationEngine(net)

    # Define dynamic rerouting handler (simulating RoutingEngine)
    def on_failure_reroute(packet: Packet, current_node: str):
        if current_node == "R1":
            # Recalculated path from R1 via R3 to Server1
            return ["R1", "R3", "Server1"]
        return None

    engine.on_route_failed = on_failure_reroute

    # Fail link R1-R2 at t=50ms
    failure_mgr.fail_link("L_R1_R2", timestamp_ms=50.0)

    # Packet originally configured with primary path
    p = Packet(
        packet_id="P_FAILOVER",
        flow_id="F1",
        source_id="PC1",
        destination_id="Server1",
        route=["PC1", "R1", "R2", "Server1"]
    )
    engine.load_packets([p])

    # Run simulation: Packet should advance PC1 -> R1, detect failure, reroute R1 -> R3 -> Server1
    stats = engine.run_all()

    assert p.is_delivered is True
    assert p.current_node == "Server1"
    assert p.route == ["PC1", "R1", "R3", "Server1"]
    assert stats.packets_delivered == 1

    # Record convergence time
    recov_time = failure_mgr.record_successful_reroute(timestamp_ms=120.0)
    assert recov_time == 70.0  # 120ms - 50ms = 70ms
