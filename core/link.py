"""
NetSimX — Physical Link Data Model
Encapsulates communication channels between network devices.
"""

from dataclasses import dataclass
from core.node import DeviceStatus


@dataclass
class Link:
    """Represents a duplex communication channel connecting two nodes."""
    link_id: str
    source: str                           # Source node ID
    destination: str                      # Destination node ID
    cost: float = 1.0                     # Routing metric (weight)
    bandwidth_mbps: float = 100.0         # Channel capacity (Mbps)
    delay_ms: float = 10.0                # Physical propagation latency (ms)
    loss_probability: float = 0.0         # Random bit error drop rate [0.0 - 1.0]
    status: DeviceStatus = DeviceStatus.UP
    queue_capacity: int = 50              # Egress Drop-Tail buffer size in packets

    @property
    def is_up(self) -> bool:
        """Returns True if the link is active and operational."""
        return self.status == DeviceStatus.UP

    def calculate_serialization_delay(self, size_bytes: int) -> float:
        """
        Calculates serialization/transmission delay in milliseconds:
        D_trans = (size_bytes * 8) / (bandwidth_mbps * 1,000,000) * 1,000 ms
        """
        if self.bandwidth_mbps <= 0:
            return 0.0
        return (size_bytes * 8.0) / (self.bandwidth_mbps * 1_000.0)

    def calculate_total_hop_delay(self, size_bytes: int, queuing_delay_ms: float = 0.0) -> float:
        """
        Total latency across the hop:
        D_hop = D_queuing + D_serialization + D_propagation
        """
        return queuing_delay_ms + self.calculate_serialization_delay(size_bytes) + self.delay_ms
