"""
NetSimX — Routing Subsystem (Member 2)
Provides path selection algorithms, routing tables, and strategy interfaces.
"""

from routing.routing_table import RoutingEntry, RoutingTable
from routing.dijkstra import PathResult, dijkstra_shortest_path, compute_dijkstra_routing_table
from routing.bellman_ford import bellman_ford_shortest_path, compute_bellman_ford_routing_table, NegativeCycleError
from routing.distance_vector import DistanceVectorEngine
from routing.routing_engine import RoutingEngine

__all__ = [
    "RoutingEntry",
    "RoutingTable",
    "PathResult",
    "dijkstra_shortest_path",
    "compute_dijkstra_routing_table",
    "bellman_ford_shortest_path",
    "compute_bellman_ford_routing_table",
    "NegativeCycleError",
    "DistanceVectorEngine",
    "RoutingEngine",
]
