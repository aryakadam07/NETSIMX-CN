"""NetSimX — Integration Adapters Package (Member 4)"""
from .topology_adapter import TopologyAdapter
from .routing_adapter import RoutingAdapter
from .failure_adapter import FailureAdapter

try:
    from .simulation_adapter import SimulationAdapter
except Exception:
    SimulationAdapter = None  # Lazy loading fallback for headless CLI tests

__all__ = ["TopologyAdapter", "RoutingAdapter", "SimulationAdapter", "FailureAdapter"]
