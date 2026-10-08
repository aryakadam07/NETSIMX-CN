"""
NetSimX — Routing Adapter (Member 4)
Wraps Member 2's routing engine for use by the GUI.
"""

from typing import List, Dict, Any, Optional
import logging

from routing.routing_engine import RoutingEngine
from routing.dijkstra import PathResult
from .topology_adapter import TopologyAdapter

logger = logging.getLogger("RoutingAdapter")

# Canonical algorithm name -> RoutingEngine alias
ALGO_MAP: Dict[str, str] = {
    "Dijkstra":       "Dijkstra",
    "Bellman-Ford":   "Bellman-Ford",
    "Distance Vector": "Distance-Vector",
}


class RoutingAdapter:
    """
    Thin facade over RoutingEngine.
    Returns plain dicts so GUI code has no dependency on PathResult internals.
    """

    def __init__(self, topology_adapter: TopologyAdapter):
        self._topo = topology_adapter
        self._engine = RoutingEngine(default_algorithm="Dijkstra")
        self._last_result: Optional[PathResult] = None

    # ------------------------------------------------------------------
    # Algorithm registry
    # ------------------------------------------------------------------

    def get_available_algorithms(self) -> List[str]:
        return list(ALGO_MAP.keys())

    # ------------------------------------------------------------------
    # Route finding
    # ------------------------------------------------------------------

    def find_route(self, source: str, destination: str,
                   algorithm: str = "Dijkstra") -> Dict[str, Any]:
        """
        Calculates the shortest path using the requested algorithm.

        Returns dict with keys:
            path, cost, hops, algorithm, reachable, error, next_hop
        """
        algo_key = ALGO_MAP.get(algorithm, algorithm)
        network = self._topo.get_topology()

        try:
            result = self._engine.find_path(
                network=network,
                source=source,
                destination=destination,
                algorithm=algo_key,
                split_horizon=True,
                poison_reverse=False,
            )
            self._last_result = result
        except Exception as exc:
            logger.error(f"Routing error: {exc}")
            return {
                "path": [], "cost": float("inf"), "hops": 0,
                "algorithm": algorithm, "reachable": False,
                "error": str(exc), "next_hop": None,
            }

        if not result.is_reachable:
            return {
                "path": [], "cost": float("inf"), "hops": 0,
                "algorithm": result.algorithm, "reachable": False,
                "error": f"No route from {source} to {destination}",
                "next_hop": None,
            }

        return {
            "path": result.path,
            "cost": result.total_cost,
            "hops": result.hop_count,
            "algorithm": result.algorithm,
            "reachable": True,
            "error": None,
            "next_hop": result.next_hop,
        }

    # ------------------------------------------------------------------
    # Routing table generation
    # ------------------------------------------------------------------

    def build_routing_table(self, router_id: str,
                            algorithm: str = "Dijkstra") -> List[Dict[str, Any]]:
        """Returns routing table entries as a list of dicts."""
        algo_key = ALGO_MAP.get(algorithm, algorithm)
        network = self._topo.get_topology()
        try:
            table = self._engine.generate_table_for_router(
                network, router_id, algorithm=algo_key)
            return [
                {
                    "destination": e.destination,
                    "next_hop": e.next_hop,
                    "metric": e.metric,
                    "interface": e.interface or "",
                    "protocol": e.protocol,
                }
                for e in table.get_all_routes()
            ]
        except Exception as exc:
            logger.error(f"Routing table error for {router_id}: {exc}")
            return []

    def get_last_result(self) -> Optional[PathResult]:
        return self._last_result
