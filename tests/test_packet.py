"""
Unit Tests for Packet Data Model & State Machine (Member 3)
"""

import pytest
from core.packet import Packet, PacketStatus, ProtocolType, DropReason


def test_packet_initialization():
    """Verifies that a packet instantiates with correct default attributes."""
    packet = Packet(
        packet_id="P001",
        flow_id="FLOW1",
        source_id="PC1",
        destination_id="Server1",
        route=["PC1", "R1", "R2", "Server1"]
    )
    assert packet.packet_id == "P001"
    assert packet.current_node == "PC1"
    assert packet.status == PacketStatus.CREATED
    assert packet.ttl == 64
    assert packet.accumulated_delay_ms == 0.0
    assert packet.hops_traveled == 0
    assert packet.is_active is True
    assert packet.is_delivered is False
    assert packet.is_dropped is False


def test_packet_step_forward_success():
    """Verifies hop-by-hop forwarding, delay accumulation, and TTL decrement."""
    packet = Packet(
        packet_id="P002",
        flow_id="FLOW1",
        source_id="PC1",
        destination_id="Server1",
        route=["PC1", "R1", "Server1"]
    )
    # Hop 1: PC1 -> R1
    in_transit = packet.step_forward(hop_delay_ms=10.5)
    assert in_transit is True
    assert packet.current_node == "R1"
    assert packet.accumulated_delay_ms == 10.5
    assert packet.hops_traveled == 1
    assert packet.ttl == 63
    assert packet.status == PacketStatus.FORWARDED

    # Hop 2: R1 -> Server1 (Destination reached)
    in_transit_final = packet.step_forward(hop_delay_ms=12.0)
    assert in_transit_final is False
    assert packet.current_node == "Server1"
    assert packet.accumulated_delay_ms == 22.5
    assert packet.hops_traveled == 2
    assert packet.ttl == 62
    assert packet.status == PacketStatus.DELIVERED
    assert packet.is_delivered is True


def test_packet_ttl_expiration():
    """Verifies that a packet drops with TTL_EXPIRED when TTL reaches zero."""
    packet = Packet(
        packet_id="P003",
        flow_id="FLOW1",
        source_id="PC1",
        destination_id="Server1",
        ttl=1,  # Set low TTL
        route=["PC1", "R1", "Server1"]
    )
    in_transit = packet.step_forward(hop_delay_ms=5.0)
    assert in_transit is False
    assert packet.is_dropped is True
    assert packet.drop_reason == DropReason.TTL_EXPIRED


def test_packet_dynamic_route_update():
    """Verifies in-flight route modification for failure recovery."""
    packet = Packet(
        packet_id="P004",
        flow_id="FLOW1",
        source_id="PC1",
        destination_id="Server1",
        route=["PC1", "R1", "R2", "Server1"]
    )
    # Move to R1
    packet.step_forward(hop_delay_ms=10.0)
    assert packet.current_node == "R1"

    # Suppose R2 fails; update route from R1 via R3
    new_subpath = ["R1", "R3", "R4", "Server1"]
    packet.update_route(new_subpath)

    assert packet.route == ["PC1", "R1", "R3", "R4", "Server1"]
    assert packet.get_next_hop() == "R3"
