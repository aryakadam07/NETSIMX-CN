"""
Unit Tests for Traffic Generator & Drop-Tail Queue (Member 3)
"""

import pytest
from core.packet import Packet, PacketStatus, DropReason
from traffic.queue_model import DropTailQueue
from traffic.flow import FlowConfig
from traffic.generator import TrafficGenerator


def test_drop_tail_queue_fifo_order():
    """Verifies FIFO enqueue and dequeue order."""
    queue = DropTailQueue(interface_id="L1", max_size_packets=5, bandwidth_mbps=100.0)
    p1 = Packet(packet_id="P1", flow_id="F1", source_id="A", destination_id="B")
    p2 = Packet(packet_id="P2", flow_id="F1", source_id="A", destination_id="B")

    assert queue.enqueue(p1, node_id="A") is True
    assert queue.enqueue(p2, node_id="A") is True
    assert queue.current_depth == 2

    assert queue.dequeue() == p1
    assert queue.dequeue() == p2
    assert queue.is_empty is True


def test_drop_tail_queue_overflow_drop():
    """Verifies that packets exceeding buffer capacity are dropped with CONGESTION reason."""
    queue = DropTailQueue(interface_id="L1", max_size_packets=2, bandwidth_mbps=100.0)

    p1 = Packet(packet_id="P1", flow_id="F1", source_id="A", destination_id="B")
    p2 = Packet(packet_id="P2", flow_id="F1", source_id="A", destination_id="B")
    p3 = Packet(packet_id="P3", flow_id="F1", source_id="A", destination_id="B")

    assert queue.enqueue(p1, node_id="A") is True
    assert queue.enqueue(p2, node_id="A") is True
    assert queue.is_full is True

    # P3 should be dropped due to buffer overflow
    assert queue.enqueue(p3, node_id="A") is False
    assert p3.is_dropped is True
    assert p3.drop_reason == DropReason.CONGESTION
    assert queue.total_dropped == 1


def test_serialization_delay_math():
    """Verifies serialization delay formula: D_trans = (size * 8) / (bandwidth * 10^6) * 1000."""
    queue = DropTailQueue(interface_id="L1", max_size_packets=10, bandwidth_mbps=10.0)
    # 1024 bytes on 10 Mbps link: (1024 * 8) / (10 * 1000) = 0.8192 ms
    p = Packet(packet_id="P1", flow_id="F1", source_id="A", destination_id="B", size_bytes=1024)
    queue.enqueue(p, node_id="A")

    delay = queue.calculate_current_queuing_delay_ms()
    assert pytest.approx(delay, rel=1e-3) == 0.8192


def test_traffic_generator_burst():
    """Verifies that the traffic generator produces correct packet counts and timestamps."""
    config = FlowConfig(
        flow_id="FLOW_TEST",
        source_id="PC1",
        destination_id="Server1",
        packet_count=10,
        inter_packet_gap_ms=15.0
    )
    route = ["PC1", "R1", "Server1"]
    packets = TrafficGenerator.generate_flow(config, route)

    assert len(packets) == 10
    assert packets[0].packet_id == "FLOW_TEST_P0001"
    assert packets[0].created_time_ms == 0.0
    assert packets[1].created_time_ms == 15.0
    assert packets[9].created_time_ms == 135.0
    assert packets[0].route == route
