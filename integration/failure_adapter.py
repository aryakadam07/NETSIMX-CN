"""
NetSimX — Failure Adapter (Member 4)
Wraps Member 3's FailureManager for GUI use.
"""

import logging
from typing import List, Optional, TYPE_CHECKING

from failures.failure_manager import FailureManager
from .topology_adapter import TopologyAdapter

if TYPE_CHECKING:
    from .simulation_adapter import SimulationAdapter

logger = logging.getLogger("FailureAdapter")


class FailureAdapter:
    """
    Bridges the GUI failure panel to FailureManager.
    Gets the FailureManager instance from SimulationAdapter when a simulation is active,
    or creates a standalone one for pre-simulation topology editing.
    """

    def __init__(self, topology_adapter: TopologyAdapter,
                 simulation_adapter: Optional['SimulationAdapter'] = None):
        self._topo = topology_adapter
        self._sim = simulation_adapter
        self._standalone_fm: Optional[FailureManager] = None

    def _get_fm(self) -> FailureManager:
        """Returns the active FailureManager (from sim if running, else standalone)."""
        if self._sim is not None:
            fm = getattr(self._sim, "get_failure_manager", lambda: None)()
            if fm is not None:
                return fm
        if self._standalone_fm is None:
            self._standalone_fm = FailureManager(self._topo.get_topology())
        return self._standalone_fm

    # ------------------------------------------------------------------
    # Failure actions
    # ------------------------------------------------------------------

    def fail_node(self, node_id: str) -> bool:
        """Marks a node as DOWN. Returns True on success."""
        if node_id not in self._topo.get_topology().nodes:
            logger.warning(f"fail_node: unknown node '{node_id}'")
            return False
        result = self._get_fm().fail_node(node_id, timestamp_ms=self._current_time())
        if result:
            logger.info(f"Node '{node_id}' marked DOWN")
        return result

    def restore_node(self, node_id: str) -> bool:
        """Restores a node to UP. Returns True on success."""
        result = self._get_fm().restore_node(node_id, timestamp_ms=self._current_time())
        if result:
            logger.info(f"Node '{node_id}' restored to UP")
        return result

    def fail_link(self, link_id: str) -> bool:
        """Marks a link as DOWN. Returns True on success."""
        if link_id not in self._topo.get_topology().links:
            logger.warning(f"fail_link: unknown link '{link_id}'")
            return False
        result = self._get_fm().fail_link(link_id, timestamp_ms=self._current_time())
        if result:
            logger.info(f"Link '{link_id}' marked DOWN")
        return result

    def restore_link(self, link_id: str) -> bool:
        """Restores a link to UP. Returns True on success."""
        result = self._get_fm().restore_link(link_id, timestamp_ms=self._current_time())
        if result:
            logger.info(f"Link '{link_id}' restored to UP")
        return result

    # ------------------------------------------------------------------
    # Status queries
    # ------------------------------------------------------------------

    def get_failed_nodes(self) -> List[str]:
        return [nid for nid, n in self._topo.get_topology().nodes.items()
                if not n.is_up]

    def get_failed_links(self) -> List[str]:
        return [lid for lid, l in self._topo.get_topology().links.items()
                if not l.is_up]

    def get_event_log(self) -> list:
        fm = self._get_fm()
        return list(fm.event_log)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_time(self) -> float:
        """Returns simulation clock time if running, else 0."""
        if self._sim and hasattr(self._sim, "_engine") and self._sim._engine:
            return self._sim._engine.current_time_ms
        return 0.0
