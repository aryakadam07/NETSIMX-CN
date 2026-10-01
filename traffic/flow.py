"""
NetSimX — Traffic Flow Configuration (Member 3)
Defines parameters for simulated network traffic flows.
"""

from dataclasses import dataclass
from core.packet import ProtocolType


@dataclass
class FlowConfig:
    """Configuration specification for a burst or continuous traffic flow."""
    flow_id: str
    source_id: str
    destination_id: str
    packet_count: int = 100
    packet_size_bytes: int = 1024
    inter_packet_gap_ms: float = 20.0
    protocol: ProtocolType = ProtocolType.TCP
    start_time_ms: float = 0.0
