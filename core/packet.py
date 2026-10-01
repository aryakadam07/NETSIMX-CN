"""
NetSimX — Packet Data Model & Lifecycle Engine (Member 3)
Defines packet data structures, state machine transitions, and latency tracking.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class ProtocolType(str, Enum):
    """Transport and network protocols supported in simulation."""
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"


class PacketStatus(str, Enum):
    """Lifecycle states of a packet during simulation."""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    TRANSMITTING = "TRANSMITTING"
    FORWARDED = "FORWARDED"
    DELIVERED = "DELIVERED"
    DROPPED = "DROPPED"


class DropReason(str, Enum):
    """Specific cause for a packet drop event."""
    CONGESTION = "CONGESTION"          # Buffer overflow (Drop-Tail queue full)
    LOSS = "LOSS"                      # Random bit-error rate on physical channel
    NO_ROUTE = "NO_ROUTE"              # Next hop unreachable / severed link
    TTL_EXPIRED = "TTL_EXPIRED"        # Loop prevention threshold exceeded (TTL <= 0)


@dataclass
class Packet:
    """Represents a discrete network packet traversing the simulated topology."""
    packet_id: str
    flow_id: str
    source_id: str
    destination_id: str
    size_bytes: int = 1024
    protocol: ProtocolType = ProtocolType.TCP
    ttl: int = 64
    created_time_ms: float = 0.0

    # Path & Location State
    current_node: str = ""
    current_hop_index: int = 0
    route: List[str] = field(default_factory=list)
    status: PacketStatus = PacketStatus.CREATED

    # Performance Tracking Metrics
    accumulated_delay_ms: float = 0.0
    hops_traveled: int = 0
    delivered_time_ms: Optional[float] = None
    drop_reason: Optional[DropReason] = None
    drop_node: Optional[str] = None

    def __post_init__(self):
        if not self.current_node and self.source_id:
            self.current_node = self.source_id

    @property
    def is_active(self) -> bool:
        """Returns True if the packet is still moving or queued in the network."""
        return self.status in (PacketStatus.CREATED, PacketStatus.QUEUED,
                               PacketStatus.TRANSMITTING, PacketStatus.FORWARDED)

    @property
    def is_delivered(self) -> bool:
        """Returns True if the packet successfully reached its destination."""
        return self.status == PacketStatus.DELIVERED

    @property
    def is_dropped(self) -> bool:
        """Returns True if the packet was terminated prior to delivery."""
        return self.status == PacketStatus.DROPPED

    def get_next_hop(self) -> Optional[str]:
        """Returns the ID of the next node along the planned route, if any."""
        if not self.route:
            return None
        next_idx = self.current_hop_index + 1
        if next_idx < len(self.route):
            return self.route[next_idx]
        return None

    def step_forward(self, hop_delay_ms: float) -> bool:
        """
        Advances the packet to the next hop in its planned route.
        Decrements TTL, accumulates delay, and increments hop counter.
        Returns True if forward succeeded, False if destination reached or TTL expired.
        """
        if self.is_dropped or self.is_delivered:
            return False

        # Decrement TTL
        self.ttl -= 1
        if self.ttl <= 0:
            self.mark_dropped(DropReason.TTL_EXPIRED, self.current_node)
            return False

        self.current_hop_index += 1
        self.accumulated_delay_ms += hop_delay_ms
        self.hops_traveled += 1

        if self.current_hop_index < len(self.route):
            self.current_node = self.route[self.current_hop_index]
            self.status = PacketStatus.FORWARDED

            # Check if this new node is the final destination
            if self.current_node == self.destination_id:
                self.mark_delivered(self.created_time_ms + self.accumulated_delay_ms)
                return False
            return True
        else:
            # Reached end of assigned route array
            if self.current_node == self.destination_id:
                self.mark_delivered(self.created_time_ms + self.accumulated_delay_ms)
            else:
                self.mark_dropped(DropReason.NO_ROUTE, self.current_node)
            return False

    def mark_delivered(self, timestamp_ms: float) -> None:
        """Transitions packet to terminal DELIVERED state."""
        self.status = PacketStatus.DELIVERED
        self.delivered_time_ms = timestamp_ms

    def mark_dropped(self, reason: DropReason, node_id: str) -> None:
        """Transitions packet to terminal DROPPED state with causal reason."""
        self.status = PacketStatus.DROPPED
        self.drop_reason = reason
        self.drop_node = node_id

    def update_route(self, new_remaining_path: List[str]) -> None:
        """
        Dynamically updates the route vector during in-flight route recalculation.
        Example: Current path was [PC1, R1, R2, Server], fails at R1.
        New remaining path: [R1, R3, R4, Server].
        """
        self.route = self.route[:self.current_hop_index] + new_remaining_path
