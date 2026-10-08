"""
NetSimX — Metrics Calculator (Member 4)
Centralised performance metric computations.
All methods are static and division-by-zero safe.
Units: latency=ms, throughput=Mbps, loss=%, utilization=%.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("MetricsCalculator")


class MetricsCalculator:
    """
    Pure-function metric calculator.
    Consumes SimulationStats and SimulationTickSnapshot objects from Member 3.
    """

    # ------------------------------------------------------------------
    # Core formulas
    # ------------------------------------------------------------------

    @staticmethod
    def packet_loss_percent(sent: int, dropped: int) -> float:
        """dropped / sent * 100. Returns 0.0 if sent == 0."""
        if sent <= 0:
            return 0.0
        return max(0.0, min(100.0, (dropped / sent) * 100.0))

    @staticmethod
    def pdr_percent(sent: int, delivered: int) -> float:
        """delivered / sent * 100. Returns 0.0 if sent == 0."""
        if sent <= 0:
            return 0.0
        return max(0.0, min(100.0, (delivered / sent) * 100.0))

    @staticmethod
    def throughput_mbps(delivered_bytes: int, duration_seconds: float) -> float:
        """
        Throughput = (delivered_bytes * 8) / (duration_s * 1_000_000) Mbps.
        Returns 0.0 for zero duration or bytes.
        """
        if duration_seconds <= 0 or delivered_bytes <= 0:
            return 0.0
        return (delivered_bytes * 8.0) / (duration_seconds * 1_000_000.0)

    @staticmethod
    def average_latency_ms(latency_values: List[float]) -> float:
        """Mean of a list of per-packet latencies. Returns 0.0 for empty list."""
        if not latency_values:
            return 0.0
        return sum(latency_values) / len(latency_values)

    @staticmethod
    def jitter_ms(latency_values: List[float]) -> float:
        """
        RFC 3550 mean absolute deviation between consecutive packets.
        Returns 0.0 for fewer than 2 samples.
        """
        if len(latency_values) < 2:
            return 0.0
        diffs = [abs(latency_values[i] - latency_values[i - 1])
                 for i in range(1, len(latency_values))]
        return sum(diffs) / len(diffs)

    @staticmethod
    def network_utilization_percent(queue_depths: Dict[str, int],
                                    max_capacities: Dict[str, int]) -> float:
        """
        Mean buffer utilization across all links.
        queue_depths: {link_id: current_depth}
        max_capacities: {link_id: max_size_packets}
        Falls back to default capacity of 50 packets when a link is not in max_capacities.
        Returns 0.0 when queue_depths is empty.
        """
        if not queue_depths:
            return 0.0
        DEFAULT_CAPACITY = 50
        utils = []
        for link_id, depth in queue_depths.items():
            cap = max_capacities.get(link_id, DEFAULT_CAPACITY)
            if cap > 0:
                utils.append(min(100.0, (depth / cap) * 100.0))
        return sum(utils) / len(utils) if utils else 0.0

    # ------------------------------------------------------------------
    # Aggregate from SimulationStats (Member 3 object)
    # ------------------------------------------------------------------

    @staticmethod
    def from_sim_stats(stats, duration_ms: float = 0.0,
                       packet_size_bytes: int = 1024) -> Dict[str, Any]:
        """
        Converts a SimulationStats object into a metrics dict.
        stats must have: packets_sent, packets_delivered, packets_dropped,
                         total_latency_ms, total_hops,
                         pdr_percent (property), plr_percent (property),
                         average_delay_ms (property), average_hops (property).
        """
        sent = getattr(stats, "packets_sent", 0)
        delivered = getattr(stats, "packets_delivered", 0)
        dropped = getattr(stats, "packets_dropped", 0)
        total_latency = getattr(stats, "total_latency_ms", 0.0)
        total_hops = getattr(stats, "total_hops", 0)

        duration_s = duration_ms / 1000.0 if duration_ms > 0 else 0.0
        delivered_bytes = delivered * packet_size_bytes
        throughput = MetricsCalculator.throughput_mbps(delivered_bytes, duration_s)

        avg_lat = (total_latency / delivered) if delivered > 0 else 0.0
        avg_hops = (total_hops / delivered) if delivered > 0 else 0.0
        pdr = MetricsCalculator.pdr_percent(sent, delivered)
        plr = MetricsCalculator.packet_loss_percent(sent, dropped)

        return {
            "packets_sent": sent,
            "packets_delivered": delivered,
            "packets_dropped": dropped,
            "throughput_mbps": round(throughput, 4),
            "avg_latency_ms": round(avg_lat, 3),
            "jitter_ms": 0.0,
            "pdr_percent": round(pdr, 2),
            "plr_percent": round(plr, 2),
            "avg_hops": round(avg_hops, 2),
        }

    # ------------------------------------------------------------------
    # Aggregate from list of SimulationTickSnapshot (Member 3 objects)
    # ------------------------------------------------------------------

    @staticmethod
    def from_snapshots(snapshots: list,
                       packet_size_bytes: int = 1024) -> Dict[str, Any]:
        """
        Derives final metrics from a recorded list of SimulationTickSnapshot objects.
        Each snapshot has: timestamp_ms, packets_delivered, packets_dropped,
                           pdr_percent, average_delay_ms, active_packets_count.
        """
        if not snapshots:
            return {
                "packets_sent": 0, "packets_delivered": 0, "packets_dropped": 0,
                "throughput_mbps": 0.0, "avg_latency_ms": 0.0, "jitter_ms": 0.0,
                "pdr_percent": 0.0, "plr_percent": 0.0, "avg_hops": 0.0,
            }

        last = snapshots[-1]
        first = snapshots[0]

        delivered = getattr(last, "packets_delivered", 0)
        dropped = getattr(last, "packets_dropped", 0)
        sent = delivered + dropped

        duration_ms = (getattr(last, "timestamp_ms", 0.0) -
                       getattr(first, "timestamp_ms", 0.0))
        duration_s = max(duration_ms / 1000.0, 0.001)
        delivered_bytes = delivered * packet_size_bytes
        throughput = MetricsCalculator.throughput_mbps(delivered_bytes, duration_s)

        latencies = [getattr(s, "average_delay_ms", 0.0) for s in snapshots
                     if getattr(s, "average_delay_ms", 0.0) > 0]
        avg_lat = MetricsCalculator.average_latency_ms(latencies)
        jitter = MetricsCalculator.jitter_ms(latencies)
        pdr = MetricsCalculator.pdr_percent(sent, delivered)
        plr = MetricsCalculator.packet_loss_percent(sent, dropped)

        return {
            "packets_sent": sent,
            "packets_delivered": delivered,
            "packets_dropped": dropped,
            "throughput_mbps": round(throughput, 4),
            "avg_latency_ms": round(avg_lat, 3),
            "jitter_ms": round(jitter, 3),
            "pdr_percent": round(pdr, 2),
            "plr_percent": round(plr, 2),
            "avg_hops": 0.0,
        }

    # ------------------------------------------------------------------
    # Per-tick snapshot for live monitoring
    # ------------------------------------------------------------------

    @staticmethod
    def from_tick(snapshot, prev_snapshot=None, packet_size_bytes: int = 1024,
                  tick_interval_ms: float = 50.0) -> Dict[str, Any]:
        """
        Builds a live metrics dict from a single SimulationTickSnapshot.
        """
        delivered = getattr(snapshot, "packets_delivered", 0)
        dropped = getattr(snapshot, "packets_dropped", 0)
        sent = delivered + dropped
        pdr = getattr(snapshot, "pdr_percent", 0.0)
        avg_lat = getattr(snapshot, "average_delay_ms", 0.0)
        plr = MetricsCalculator.packet_loss_percent(sent, dropped)

        # Instantaneous throughput from this tick
        interval_s = tick_interval_ms / 1000.0
        prev_del = getattr(prev_snapshot, "packets_delivered", 0) if prev_snapshot else 0
        new_del = max(0, delivered - prev_del)
        throughput = MetricsCalculator.throughput_mbps(new_del * packet_size_bytes, interval_s)

        # Jitter from consecutive avg_delay values
        jitter = 0.0
        if prev_snapshot:
            prev_lat = getattr(prev_snapshot, "average_delay_ms", 0.0)
            jitter = abs(avg_lat - prev_lat)

        queue_depths = getattr(snapshot, "queue_depths", {})

        return {
            "packets_sent": sent,
            "packets_delivered": delivered,
            "packets_dropped": dropped,
            "pdr_percent": round(pdr, 2),
            "plr_percent": round(plr, 2),
            "throughput_mbps": round(throughput, 4),
            "avg_latency_ms": round(avg_lat, 3),
            "jitter_ms": round(jitter, 3),
            "queue_depths": queue_depths,
            "active_packets": getattr(snapshot, "active_packets_count", 0),
            "timestamp_ms": getattr(snapshot, "timestamp_ms", 0.0),
        }
