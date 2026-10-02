"""
NetSimX — Discrete-Event Simulation Engine (Member 3)
Drives hop-by-hop packet forwarding, delay accumulation, queuing, scheduled events,
and real-time telemetry snapshots.
"""

import random
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from core.network import NetworkTopology
from core.packet import Packet, PacketStatus, DropReason
from core.event_manager import EventManager, ScheduledEvent
from traffic.queue_model import DropTailQueue


@dataclass
class SimulationStats:
    """Real-time statistical snapshot of the simulation run."""
    packets_sent: int = 0
    packets_delivered: int = 0
    packets_dropped: int = 0
    total_latency_ms: float = 0.0
    total_hops: int = 0

    @property
    def pdr_percent(self) -> float:
        """Packet Delivery Ratio: (Delivered / Sent) * 100."""
        if self.packets_sent == 0:
            return 0.0
        return (self.packets_delivered / self.packets_sent) * 100.0

    @property
    def plr_percent(self) -> float:
        """Packet Loss Ratio: (Dropped / Sent) * 100."""
        if self.packets_sent == 0:
            return 0.0
        return (self.packets_dropped / self.packets_sent) * 100.0

    @property
    def average_delay_ms(self) -> float:
        """Average End-to-End Latency for delivered packets."""
        if self.packets_delivered == 0:
            return 0.0
        return self.total_latency_ms / self.packets_delivered

    @property
    def average_hops(self) -> float:
        """Average Hop Count for delivered packets."""
        if self.packets_delivered == 0:
            return 0.0
        return self.total_hops / self.packets_delivered


@dataclass
class SimulationTickSnapshot:
    """Telemetry data emitted at every discrete simulation clock tick for the GUI / Dashboard."""
    timestamp_ms: float
    active_packets_count: int
    packets_delivered: int
    packets_dropped: int
    pdr_percent: float
    average_delay_ms: float
    executed_events: List[str] = field(default_factory=list)
    queue_depths: Dict[str, int] = field(default_factory=dict)


class SimulationEngine:
    """
    Coordinates packet traversal across the network topology.
    Models interface buffers, link delays, drop conditions, scheduled timeline events,
    and in-flight rerouting.
    """

    def __init__(self, network: NetworkTopology, event_manager: Optional[EventManager] = None):
        self.network = network
        self.event_manager = event_manager
        self.packets: List[Packet] = []
        self.interface_queues: Dict[str, DropTailQueue] = {}
        self.stats = SimulationStats()
        self.current_time_ms: float = 0.0
        self.on_route_failed: Optional[Callable[[Packet, str], Optional[List[str]]]] = None
        self.on_tick_listeners: List[Callable[[SimulationTickSnapshot], None]] = []

        self._initialize_queues()

    def _initialize_queues(self) -> None:
        """Instantiates a DropTailQueue for every active link in the network."""
        for link_id, link in self.network.links.items():
            self.interface_queues[link_id] = DropTailQueue(
                interface_id=link_id,
                max_size_packets=link.queue_capacity,
                bandwidth_mbps=link.bandwidth_mbps
            )

    def load_packets(self, packets: List[Packet]) -> None:
        """Loads a burst of packets to be processed in the simulation."""
        self.packets.extend(packets)
        self.stats.packets_sent += len(packets)

    def register_tick_listener(self, callback: Callable[[SimulationTickSnapshot], None]) -> None:
        """Subscribes a listener (e.g. GUI canvas or logger) to clock tick updates."""
        self.on_tick_listeners.append(callback)

    def step_packet(self, packet: Packet) -> bool:
        """
        Processes one hop forward for a single active packet.
        Returns True if packet is still in transit, False if delivered or dropped.
        """
        if not packet.is_active:
            return False

        current_node_id = packet.current_node
        next_node_id = packet.get_next_hop()

        # 1. Validation: Route continuity check
        if not next_node_id:
            if current_node_id == packet.destination_id:
                packet.mark_delivered(packet.created_time_ms + packet.accumulated_delay_ms)
                self.stats.packets_delivered += 1
                self.stats.total_latency_ms += packet.accumulated_delay_ms
                self.stats.total_hops += packet.hops_traveled
            else:
                packet.mark_dropped(DropReason.NO_ROUTE, current_node_id)
                self.stats.packets_dropped += 1
            return False

        # 2. Check if current node is UP
        curr_node = self.network.nodes.get(current_node_id)
        if not curr_node or not curr_node.is_up:
            packet.mark_dropped(DropReason.NO_ROUTE, current_node_id)
            self.stats.packets_dropped += 1
            return False

        # 3. Check connecting link and next node
        link = self.network.get_link_between(current_node_id, next_node_id)
        next_node = self.network.nodes.get(next_node_id)

        # Failure Condition: Link or Next Node is DOWN
        if not link or not link.is_up or not next_node or not next_node.is_up:
            # Check if dynamic route recalculation handler is provided
            if self.on_route_failed:
                new_subpath = self.on_route_failed(packet, current_node_id)
                if new_subpath and len(new_subpath) > 1:
                    packet.update_route(new_subpath)
                    # Retry next hop with newly discovered path
                    return self.step_packet(packet)

            # No alternative route: Drop packet
            packet.mark_dropped(DropReason.NO_ROUTE, current_node_id)
            self.stats.packets_dropped += 1
            return False

        # 4. Check Random Physical Loss Rate on Link
        if link.loss_probability > 0.0 and random.random() < link.loss_probability:
            packet.mark_dropped(DropReason.LOSS, current_node_id)
            self.stats.packets_dropped += 1
            return False

        # 5. Interface Queue & Congestion Check (Drop-Tail Buffer)
        queue = self.interface_queues.get(link.link_id)
        if queue:
            queuing_delay = queue.calculate_current_queuing_delay_ms()
            enqueued = queue.enqueue(packet, current_node_id)
            if not enqueued:
                self.stats.packets_dropped += 1
                return False
            # Immediate dequeue for forward step progression in discrete step
            queue.dequeue()
        else:
            queuing_delay = 0.0

        # 6. Calculate Hop Latency: D_hop = D_queue + D_trans + D_prop
        hop_delay = link.calculate_total_hop_delay(packet.size_bytes, queuing_delay)

        # 7. Advance packet
        still_in_transit = packet.step_forward(hop_delay)

        if packet.is_delivered:
            self.stats.packets_delivered += 1
            self.stats.total_latency_ms += packet.accumulated_delay_ms
            self.stats.total_hops += packet.hops_traveled
            return False
        elif packet.is_dropped:
            self.stats.packets_dropped += 1
            return False

        return still_in_transit

    def step_clock(self, delta_t_ms: float = 50.0) -> SimulationTickSnapshot:
        """
        Advances simulation time by delta_t_ms:
        1. Executes scheduled timeline events due at this timestamp.
        2. Advances in-transit packets.
        3. Samples queue depths.
        4. Emits snapshot to listeners.
        """
        self.current_time_ms += delta_t_ms

        # 1. Process Timeline Events
        executed_events: List[str] = []
        if self.event_manager:
            fired = self.event_manager.process_due_events(self.current_time_ms)
            executed_events = [f"{e.event_type.value}:{e.target_id}" for e in fired]

        # 2. Advance active packets that have been created by current_time_ms
        active_packets = [
            p for p in self.packets
            if p.is_active and p.created_time_ms <= self.current_time_ms
        ]
        for packet in active_packets:
            self.step_packet(packet)

        # 3. Sample Queue Depths & Utilization
        queue_depths = {}
        for link_id, q in self.interface_queues.items():
            q.record_tick_sample(self.current_time_ms, delta_t_ms)
            queue_depths[link_id] = q.current_depth

        # 4. Generate Snapshot
        snapshot = SimulationTickSnapshot(
            timestamp_ms=self.current_time_ms,
            active_packets_count=len([p for p in self.packets if p.is_active]),
            packets_delivered=self.stats.packets_delivered,
            packets_dropped=self.stats.packets_dropped,
            pdr_percent=self.stats.pdr_percent,
            average_delay_ms=self.stats.average_delay_ms,
            executed_events=executed_events,
            queue_depths=queue_depths
        )

        for listener in self.on_tick_listeners:
            listener(snapshot)

        return snapshot

    def run_all(self, max_steps: int = 1000, tick_interval_ms: float = 50.0) -> SimulationStats:
        """
        Runs the simulation loop until all loaded packets are either
        DELIVERED or DROPPED, or max_steps is reached.
        """
        for _ in range(max_steps):
            active = [p for p in self.packets if p.is_active]
            if not active and (not self.event_manager or not self.event_manager.get_pending_events()):
                break
            self.step_clock(tick_interval_ms)

        return self.stats
