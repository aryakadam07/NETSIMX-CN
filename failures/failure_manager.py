"""
NetSimX — Failure & Recovery Manager (Member 3)
Controls dynamic network faults (nodes/links), recovery, and convergence time measurement.
"""

from typing import Optional, Dict
from dataclasses import dataclass
from core.network import NetworkTopology
from core.node import DeviceStatus


@dataclass
class FailureEventRecord:
    """Historical log entry for a fault or restoration event."""
    target_id: str
    target_type: str                   # "NODE" or "LINK"
    action: str                        # "FAIL" or "RESTORE"
    timestamp_ms: float
    recovery_time_ms: Optional[float] = None


class FailureManager:
    """
    Manages operational state changes for nodes and links.
    Measures network re-convergence times upon link cutoff.
    """

    def __init__(self, network: NetworkTopology):
        self.network = network
        self.last_failure_time_ms: Optional[float] = None
        self.last_recovery_time_ms: Optional[float] = None
        self.event_log: list[FailureEventRecord] = []
        self._active_failures: Dict[str, float] = {}   # {target_id: failure_timestamp_ms}

    def fail_node(self, node_id: str, timestamp_ms: float = 0.0) -> bool:
        """Sets a node to DOWN status and records the failure event."""
        if node_id not in self.network.nodes:
            return False
        self.network.set_node_status(node_id, DeviceStatus.DOWN)
        self.last_failure_time_ms = timestamp_ms
        self._active_failures[node_id] = timestamp_ms

        self.event_log.append(
            FailureEventRecord(
                target_id=node_id,
                target_type="NODE",
                action="FAIL",
                timestamp_ms=timestamp_ms
            )
        )
        return True

    def restore_node(self, node_id: str, timestamp_ms: float = 0.0) -> bool:
        """Restores a node to UP status."""
        if node_id not in self.network.nodes:
            return False
        self.network.set_node_status(node_id, DeviceStatus.UP)
        fail_time = self._active_failures.pop(node_id, None)
        recov_time = (timestamp_ms - fail_time) if fail_time is not None else 0.0

        self.event_log.append(
            FailureEventRecord(
                target_id=node_id,
                target_type="NODE",
                action="RESTORE",
                timestamp_ms=timestamp_ms,
                recovery_time_ms=recov_time
            )
        )
        return True

    def fail_link(self, link_id: str, timestamp_ms: float = 0.0) -> bool:
        """Sets a link to DOWN status."""
        if link_id not in self.network.links:
            return False
        self.network.set_link_status(link_id, DeviceStatus.DOWN)
        self.last_failure_time_ms = timestamp_ms
        self._active_failures[link_id] = timestamp_ms

        self.event_log.append(
            FailureEventRecord(
                target_id=link_id,
                target_type="LINK",
                action="FAIL",
                timestamp_ms=timestamp_ms
            )
        )
        return True

    def restore_link(self, link_id: str, timestamp_ms: float = 0.0) -> bool:
        """Restores a link to UP status."""
        if link_id not in self.network.links:
            return False
        self.network.set_link_status(link_id, DeviceStatus.UP)
        fail_time = self._active_failures.pop(link_id, None)
        recov_time = (timestamp_ms - fail_time) if fail_time is not None else 0.0

        self.event_log.append(
            FailureEventRecord(
                target_id=link_id,
                target_type="LINK",
                action="RESTORE",
                timestamp_ms=timestamp_ms,
                recovery_time_ms=recov_time
            )
        )
        return True

    def record_successful_reroute(self, timestamp_ms: float) -> Optional[float]:
        """
        Invoked when the first packet successfully traverses an alternate path
        after a failure. Computes and returns the convergence time Delta t_recovery.
        """
        if self.last_failure_time_ms is not None:
            self.last_recovery_time_ms = timestamp_ms - self.last_failure_time_ms
            return self.last_recovery_time_ms
        return None
