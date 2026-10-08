"""
NetSimX — Packet State Visualizer (Member 4)
Provides status-coloured packet representation for the topology view.
"""

from typing import Dict, List, Any


class PacketVisualizer:
    """Translates packet status to display properties."""

    STATUS_COLORS = {
        "CREATED":      "#AAAAAA",
        "QUEUED":       "#F0A500",
        "TRANSMITTING": "#4A90D9",
        "FORWARDED":    "#4A90D9",
        "DELIVERED":    "#5CB85C",
        "DROPPED":      "#CC3333",
    }

    STATUS_LABELS = {
        "CREATED":      "Pending",
        "QUEUED":       "Queued",
        "TRANSMITTING": "In Transit",
        "FORWARDED":    "Forwarding",
        "DELIVERED":    "Delivered",
        "DROPPED":      "Dropped",
    }

    @staticmethod
    def get_color(status: str) -> str:
        return PacketVisualizer.STATUS_COLORS.get(status.upper(), "#888888")

    @staticmethod
    def get_label(status: str) -> str:
        return PacketVisualizer.STATUS_LABELS.get(status.upper(), status)

    @staticmethod
    def summarize_snapshot(snapshot) -> Dict[str, Any]:
        """
        Returns a display-ready summary from a SimulationTickSnapshot.
        """
        return {
            "timestamp_ms": getattr(snapshot, "timestamp_ms", 0.0),
            "active": getattr(snapshot, "active_packets_count", 0),
            "delivered": getattr(snapshot, "packets_delivered", 0),
            "dropped": getattr(snapshot, "packets_dropped", 0),
            "pdr": getattr(snapshot, "pdr_percent", 0.0),
            "avg_delay": getattr(snapshot, "average_delay_ms", 0.0),
            "events": getattr(snapshot, "executed_events", []),
            "queue_depths": getattr(snapshot, "queue_depths", {}),
        }
