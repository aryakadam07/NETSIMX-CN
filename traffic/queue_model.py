"""
NetSimX — Drop-Tail FIFO Queuing & Congestion Model (Member 3)
Simulates an egress interface buffer with finite capacity and Drop-Tail overflow.
"""

from collections import deque
from typing import Optional, Deque
from core.packet import Packet, PacketStatus, DropReason


class DropTailQueue:
    """
    Finite-buffer Drop-Tail FIFO queue modeling a router egress interface buffer.
    When current occupancy reaches max_size_packets, subsequent packets are dropped.
    """

    def __init__(self, interface_id: str, max_size_packets: int = 50, bandwidth_mbps: float = 100.0):
        self.interface_id = interface_id
        self.max_size_packets = max_size_packets
        self.bandwidth_mbps = bandwidth_mbps
        self._buffer: Deque[Packet] = deque()

        # Telemetry counters
        self.total_enqueued: int = 0
        self.total_dequeued: int = 0
        self.total_dropped: int = 0

    @property
    def current_depth(self) -> int:
        """Returns the number of packets currently waiting in the buffer."""
        return len(self._buffer)

    @property
    def is_full(self) -> bool:
        """Returns True if the buffer cannot accept any more packets."""
        return len(self._buffer) >= self.max_size_packets

    @property
    def is_empty(self) -> bool:
        """Returns True if the buffer contains no packets."""
        return len(self._buffer) == 0

    @property
    def utilization_percent(self) -> float:
        """Returns buffer capacity utilization percentage."""
        if self.max_size_packets <= 0:
            return 0.0
        return (len(self._buffer) / self.max_size_packets) * 100.0

    def calculate_current_queuing_delay_ms(self) -> float:
        """
        Calculates total queuing delay in ms for a newly arriving packet,
        based on the serialization time of all packets ahead in the queue.
        D_queue = sum(size_i * 8 / (bandwidth * 10^6) * 1000)
        """
        if self.bandwidth_mbps <= 0:
            return 0.0
        total_bits = sum(p.size_bytes * 8.0 for p in self._buffer)
        return total_bits / (self.bandwidth_mbps * 1_000.0)

    def enqueue(self, packet: Packet, node_id: str) -> bool:
        """
        Attempts to enqueue a packet into the interface buffer.
        If buffer is full, drops packet with reason DROPPED_CONGESTION.
        Returns True if enqueued successfully, False if dropped.
        """
        if self.is_full:
            self.total_dropped += 1
            packet.mark_dropped(DropReason.CONGESTION, node_id)
            return False

        packet.status = PacketStatus.QUEUED
        self._buffer.append(packet)
        self.total_enqueued += 1
        return True

    def dequeue(self) -> Optional[Packet]:
        """Removes and returns the next packet from the head of the FIFO queue."""
        if self.is_empty:
            return None
        packet = self._buffer.popleft()
        self.total_dequeued += 1
        return packet

    def clear(self) -> list[Packet]:
        """Clears all packets from the buffer (used during node failure / reset)."""
        purged = list(self._buffer)
        self._buffer.clear()
        return purged
