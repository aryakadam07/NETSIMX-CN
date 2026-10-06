"""
NetSimX — Unified Routing Engine & Strategy Subsystem (Member 2)
Implements Strategy Pattern decoupling path calculation algorithms from network simulation logic.
Integrates Dijkstra, Bellman-Ford, and Distance-Vector engines with NetworkTopology.
"""

from typing import Dict, List, Optional, Callable
from core.network import NetworkTopology
from core.packet import Packet
from routing.dijkstra import PathResult, dijkstra_shortest_path, compute_dijkstra_routing_table
from routing.bellman_ford import bellman_ford_shortest_path, compute_bellman_ford_routing_table, NegativeCycleError
from routing.distance_vector import DistanceVectorEngine
from routing.routing_table import RoutingTable, RoutingEntry


class RoutingEngine:
    """
    Central strategy controller for routing algorithm execution across NetSimX network topologies.
    
    Supported Strategies:
    - "Dijkstra": Link-State Min-Heap algorithm (OSPF baseline)
    - "Bellman-Ford": Edge relaxation algorithm (supports negative weights / cycle check)
    - "Distance-Vector": Distributed Bellman-Ford equation with Split Horizon / Poison Reverse
    """

    def __init__(self, default_algorithm: str = "Dijkstra"):
        self.default_algorithm = default_algorithm

    def find_path(
        self,
        network: NetworkTopology,
        source: str,
        destination: str,
        algorithm: Optional[str] = None,
        split_horizon: bool = False,
        poison_reverse: bool = False
    ) -> PathResult:
        """
        Calculates the optimal path from source to destination using the selected algorithm.
        Automatically filters out inactive (DOWN) nodes and links from `network`.
        
        Args:
            network (NetworkTopology): The live network topology.
            source (str): Source node ID.
            destination (str): Target destination node ID.
            algorithm (Optional[str]): Routing algorithm ('Dijkstra', 'Bellman-Ford', 'Distance-Vector').
            split_horizon (bool): Enables Split Horizon for Distance-Vector mode.
            poison_reverse (bool): Enables Poison Reverse for Distance-Vector mode.
            
        Returns:
            PathResult: Detailed shortest path output.
        """
        algo = (algorithm or self.default_algorithm).lower()
        active_graph = network.get_active_adjacency_dict()

        if algo in ("dijkstra", "ls", "link-state"):
            return dijkstra_shortest_path(active_graph, source, destination)

        elif algo in ("bellman-ford", "bellmanford", "bf"):
            try:
                return bellman_ford_shortest_path(active_graph, source, destination)
            except NegativeCycleError:
                # Fall back to unreachable path result if negative cycle exists
                return PathResult(
                    source=source,
                    destination=destination,
                    path=[],
                    total_cost=float('inf'),
                    hop_count=0,
                    algorithm="Bellman-Ford",
                    is_reachable=False,
                    next_hop=None
                )

        elif algo in ("distance-vector", "distancevector", "dv"):
            dv_engine = DistanceVectorEngine(
                graph=active_graph,
                split_horizon=split_horizon,
                poison_reverse=poison_reverse
            )
            dv_engine.run_to_convergence()
            return dv_engine.get_path(source, destination)

        else:
            # Default fallback: Dijkstra
            return dijkstra_shortest_path(active_graph, source, destination)

    def generate_table_for_router(
        self,
        network: NetworkTopology,
        router_id: str,
        algorithm: Optional[str] = None
    ) -> RoutingTable:
        """
        Computes and populates a complete RoutingTable for the given router.
        """
        algo = (algorithm or self.default_algorithm).lower()
        active_graph = network.get_active_adjacency_dict()

        # Map node_ids to IP addresses where available
        node_ip_map = {nid: n.ip_address for nid, n in network.nodes.items() if hasattr(n, 'ip_address')}

        if algo in ("bellman-ford", "bellmanford", "bf"):
            return compute_bellman_ford_routing_table(active_graph, router_id, node_ip_map)
        elif algo in ("distance-vector", "distancevector", "dv"):
            dv_engine = DistanceVectorEngine(graph=active_graph, split_horizon=True, poison_reverse=True)
            dv_engine.run_to_convergence()
            return dv_engine.get_routing_table(router_id)
        else:
            return compute_dijkstra_routing_table(active_graph, router_id, node_ip_map)

    def invalidate_and_recalculate(
        self,
        network: NetworkTopology,
        failed_element_id: str,
        algorithm: Optional[str] = None
    ) -> Dict[str, PathResult]:
        """
        Recomputes paths across all active nodes when a link or node failure occurs.
        """
        results: Dict[str, PathResult] = {}
        active_nodes = [nid for nid, n in network.nodes.items() if n.is_up]

        for u in active_nodes:
            for v in active_nodes:
                if u != v:
                    key = f"{u}->{v}"
                    results[key] = self.find_path(network, u, v, algorithm=algorithm)
        return results

    def create_reroute_handler(
        self,
        network: NetworkTopology,
        algorithm: Optional[str] = None
    ) -> Callable[[Packet, str], Optional[List[str]]]:
        """
        Returns a callback function matching SimulationEngine.on_route_failed signature.
        Used for autonomous dynamic in-flight rerouting when a link or router fails.
        """
        def reroute_callback(packet: Packet, current_node: str) -> Optional[List[str]]:
            res = self.find_path(
                network=network,
                source=current_node,
                destination=packet.destination_id,
                algorithm=algorithm
            )
            if res.is_reachable and len(res.path) > 0:
                return res.path
            return None

        return reroute_callback
