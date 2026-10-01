"""
Unit Tests for Scheduled Event Manager (Member 3)
"""

import pytest
from core.node import Router
from core.link import Link
from core.network import NetworkTopology
from core.event_manager import EventManager, EventType
from failures.failure_manager import FailureManager


def test_event_manager_chronological_scheduling():
    """Verifies that events are stored and sorted chronologically."""
    mgr = EventManager()
    e3 = mgr.schedule(trigger_time_ms=300.0, event_type=EventType.LINK_UP, target_id="L1")
    e1 = mgr.schedule(trigger_time_ms=100.0, event_type=EventType.LINK_DOWN, target_id="L1")
    e2 = mgr.schedule(trigger_time_ms=200.0, event_type=EventType.ROUTER_DOWN, target_id="R1")

    pending = mgr.get_pending_events()
    assert pending[0].trigger_time_ms == 100.0
    assert pending[1].trigger_time_ms == 200.0
    assert pending[2].trigger_time_ms == 300.0


def test_event_manager_execution_at_timestamp():
    """Verifies that events only fire when current_time_ms >= trigger_time_ms."""
    net = NetworkTopology(network_id="NET1", name="Test Net")
    r1 = Router(node_id="R1", name="Router 1", ip_address="10.0.0.1")
    net.add_node(r1)
    l1 = Link(link_id="L1", source="R1", destination="R2", cost=1.0)
    net.add_link(l1)

    fail_mgr = FailureManager(net)
    event_mgr = EventManager(failure_manager=fail_mgr)

    event_mgr.schedule(trigger_time_ms=150.0, event_type=EventType.LINK_DOWN, target_id="L1")
    event_mgr.schedule(trigger_time_ms=300.0, event_type=EventType.LINK_UP, target_id="L1")

    # At t=100ms, no event should fire
    fired_100 = event_mgr.process_due_events(current_time_ms=100.0)
    assert len(fired_100) == 0
    assert l1.is_up is True

    # At t=150ms, LINK_DOWN should fire
    fired_150 = event_mgr.process_due_events(current_time_ms=150.0)
    assert len(fired_150) == 1
    assert fired_150[0].event_type == EventType.LINK_DOWN
    assert l1.is_up is False

    # At t=300ms, LINK_UP should fire
    fired_300 = event_mgr.process_due_events(current_time_ms=300.0)
    assert len(fired_300) == 1
    assert fired_300[0].event_type == EventType.LINK_UP
    assert l1.is_up is True
