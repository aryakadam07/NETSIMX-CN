"""
NetSimX — Scheduled Event Manager (Member 3)
Provides a discrete-event timeline for pre-programmed faults, traffic changes, and recovery.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from failures.failure_manager import FailureManager
from utils.logger import get_logger

logger = get_logger("EventManager")


class EventType(str, Enum):
    """Supported simulation timeline event categories."""
    ROUTER_DOWN = "ROUTER_DOWN"
    ROUTER_UP = "ROUTER_UP"
    LINK_DOWN = "LINK_DOWN"
    LINK_UP = "LINK_UP"
    TRAFFIC_SPIKE = "TRAFFIC_SPIKE"
    ROUTE_RECALCULATED = "ROUTE_RECALCULATED"


@dataclass(order=True)
class ScheduledEvent:
    """An event scheduled to trigger at a specific simulation clock timestamp."""
    trigger_time_ms: float
    event_id: str = field(compare=False)
    event_type: EventType = field(compare=False)
    target_id: str = field(compare=False)
    parameters: Dict[str, Any] = field(default_factory=dict, compare=False)
    executed: bool = field(default=False, compare=False)
    executed_at_ms: Optional[float] = field(default=None, compare=False)


class EventManager:
    """
    Maintains a chronological queue of simulation events.
    Fires due events during clock ticks and executes actions via FailureManager.
    """

    def __init__(self, failure_manager: Optional[FailureManager] = None):
        self.failure_manager = failure_manager
        self.events: List[ScheduledEvent] = []
        self._custom_handlers: Dict[EventType, Callable[[ScheduledEvent, float], None]] = {}

    def schedule(
        self,
        trigger_time_ms: float,
        event_type: EventType,
        target_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None
    ) -> ScheduledEvent:
        """Schedules a new event in chronological order."""
        if not event_id:
            event_id = f"EVT_{len(self.events) + 1:04d}_{event_type.value}"

        evt = ScheduledEvent(
            trigger_time_ms=trigger_time_ms,
            event_id=event_id,
            event_type=event_type,
            target_id=target_id,
            parameters=parameters or {}
        )
        self.events.append(evt)
        # Keep events sorted chronologically by trigger_time_ms
        self.events.sort(key=lambda e: e.trigger_time_ms)
        logger.info(f"Scheduled {event_type.value} on '{target_id}' at t={trigger_time_ms} ms")
        return evt

    def register_handler(self, event_type: EventType, handler: Callable[[ScheduledEvent, float], None]) -> None:
        """Registers a custom callback for custom event types (e.g., TRAFFIC_SPIKE)."""
        self._custom_handlers[event_type] = handler

    def process_due_events(self, current_time_ms: float) -> List[ScheduledEvent]:
        """
        Evaluates and executes all events whose trigger_time_ms <= current_time_ms.
        Returns the list of events executed during this check.
        """
        executed_events: List[ScheduledEvent] = []

        for evt in self.events:
            if not evt.executed and evt.trigger_time_ms <= current_time_ms:
                self._execute_single_event(evt, current_time_ms)
                evt.executed = True
                evt.executed_at_ms = current_time_ms
                executed_events.append(evt)

        return executed_events

    def _execute_single_event(self, evt: ScheduledEvent, current_time_ms: float) -> None:
        """Dispatches event execution to the FailureManager or custom handler."""
        logger.info(f"[TIMELINE TRIGGER] {evt.event_type.value} on target '{evt.target_id}' at t={current_time_ms} ms")

        # 1. Custom Handlers (if registered)
        if evt.event_type in self._custom_handlers:
            self._custom_handlers[evt.event_type](evt, current_time_ms)
            return

        # 2. Standard Failure/Recovery Handlers
        if not self.failure_manager:
            return

        if evt.event_type == EventType.LINK_DOWN:
            self.failure_manager.fail_link(evt.target_id, current_time_ms)
        elif evt.event_type == EventType.LINK_UP:
            self.failure_manager.restore_link(evt.target_id, current_time_ms)
        elif evt.event_type == EventType.ROUTER_DOWN:
            self.failure_manager.fail_node(evt.target_id, current_time_ms)
        elif evt.event_type == EventType.ROUTER_UP:
            self.failure_manager.restore_node(evt.target_id, current_time_ms)

    def get_pending_events(self) -> List[ScheduledEvent]:
        """Returns all events that have not yet fired."""
        return [e for e in self.events if not e.executed]

    def get_executed_events(self) -> List[ScheduledEvent]:
        """Returns all events that have already been fired."""
        return [e for e in self.events if e.executed]
