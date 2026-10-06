"""
NetSimX — Manual Dijkstra Shortest Path Engine (Member 2)
Implements Dijkstra's link-state single-source shortest path algorithm using a min-heap priority queue.
Calculates minimum cost paths, hop sequences, and next-hop forwarding entries.
"""

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from routing.routing_table import RoutingTable, RoutingEntry


@dataclass
class PathResult:
    """
    Standardized container representing the output of a routing path search.
    
    Attributes:
        source (str): Starting node ID.
        destination (str): Target node ID.
        path (List[str]): Ordered list of node IDs from source to destination.
        total_cost (float): Accumulated routing metric along the path.
        hop_count (int): Number of intermediate edges/links traversed.
        algorithm (str): Name of the routing strategy ('Dijkstra', 'Bellman-Ford', 'Distance-Vector').
        is_reachable (bool): True if a valid path exists, False if partitioned/unreachable.
        next_hop (Optional[str]): Immediate next-hop node ID from source.
    """
    source: str
    destination: str
    path: List[str] = field(default_factory=list)
    total_cost: float = float('inf')
    hop_count: int = 0
    algorithm: str = "Dijkstra"
    is_reachable: bool = False
    next_hop: Optional[str] = None

    def __post_init__(self):
        if self.next_hop is None and self.path:
            if len(self.path) > 1:
                self.next_hop = self.path[1]
            elif len(self.path) == 1 and self.source == self.destination:
                self.next_hop = self.source


def dijkstra_shortest_path(
    graph: Dict[str, Dict[str, float]],
    source: str,
    target: str
) -> PathResult:
    """
    Computes the shortest path from source to target using a manual Min-Heap Dijkstra algorithm.
    
    Algorithm Overview & Time Complexity:
    - Uses Python standard library `heapq` for priority queue operations.
    - Graph representation: Adjacency dictionary `{node_id: {neighbor_id: edge_cost}}`.
    - Time Complexity: O((V + E) * log V) where V = number of vertices, E = number of edges.
    - Space Complexity: O(V) for distance map, predecessor map, and priority queue.
    
    Args:
        graph (Dict[str, Dict[str, float]]): Active network adjacency list.
        source (str): Source router/host node ID.
        target (str): Destination router/host node ID.
        
    Returns:
        PathResult: Detailed path findings, cost, hop sequence, and next hop.
    """
    # Edge Case 1: Empty graph or invalid source/target nodes
    if not graph or source not in graph:
        return PathResult(
            source=source,
            destination=target,
            path=[],
            total_cost=float('inf'),
            hop_count=0,
            algorithm="Dijkstra",
            is_reachable=False,
            next_hop=None
        )

    # Edge Case 2: Target not in graph
    if target not in graph:
        return PathResult(
            source=source,
            destination=target,
            path=[],
            total_cost=float('inf'),
            hop_count=0,
            algorithm="Dijkstra",
            is_reachable=False,
            next_hop=None
        )

    # Edge Case 3: Source equals Target
    if source == target:
        return PathResult(
            source=source,
            destination=target,
            path=[source],
            total_cost=0.0,
            hop_count=0,
            algorithm="Dijkstra",
            is_reachable=True,
            next_hop=source
        )

    # --------------------------------------------------------------------------
    # STEP 1: INITIALIZATION
    # --------------------------------------------------------------------------
    # dist[u] stores the tentative minimal path cost from source to node u.
    # Initialized to infinity for all nodes, except dist[source] = 0.0.
    dist: Dict[str, float] = {node: float('inf') for node in graph}
    dist[source] = 0.0

    # prev[u] records the optimal predecessor of node u along the shortest path.
    prev: Dict[str, Optional[str]] = {node: None for node in graph}

    # visited set maintains nodes whose shortest distance from source has been finalized.
    visited: Set[str] = set()

    # Priority Queue (Min-Heap): Stores tuples of (tentative_cost, node_id).
    # Smallest tentative cost is popped first.
    pq: List[tuple[float, str]] = [(0.0, source)]

    # --------------------------------------------------------------------------
    # STEP 2: MIN-HEAP RELAXATION LOOP
    # --------------------------------------------------------------------------
    while pq:
        # Extract the node with the minimum tentative distance from source
        current_cost, u = heapq.heappop(pq)

        # Skip if node is already finalized (handles duplicate heap entries)
        if u in visited:
            continue

        # Mark current node as finalized
        visited.add(u)

        # Early Termination Optimization: Stop if we popped target node
        if u == target:
            break

        # Inspect all outgoing links / neighbors of node u
        for neighbor, weight in graph[u].items():
            # Skip if neighbor is already finalized
            if neighbor in visited:
                continue

            # Ignore negative edge weights for Dijkstra stability
            if weight < 0:
                continue

            # Compute candidate new cost to reach neighbor via node u
            new_cost = current_cost + weight

            # RELAXATION STEP: If new path via u is cheaper than previously known path to neighbor
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = u
                heapq.heappush(pq, (new_cost, neighbor))

    # --------------------------------------------------------------------------
    # STEP 3: PATH RECONSTRUCTION
    # --------------------------------------------------------------------------
    # Backtrack from target to source using predecessor map `prev`
    if dist[target] == float('inf'):
        # Target was never reached (graph is disconnected/partitioned)
        return PathResult(
            source=source,
            destination=target,
            path=[],
            total_cost=float('inf'),
            hop_count=0,
            algorithm="Dijkstra",
            is_reachable=False,
            next_hop=None
        )

    path: List[str] = []
    curr: Optional[str] = target
    while curr is not None:
        path.append(curr)
        curr = prev[curr]
    path.reverse()

    # Determine next hop (second node in reconstructed path sequence)
    next_hop = path[1] if len(path) > 1 else source

    return PathResult(
        source=source,
        destination=target,
        path=path,
        total_cost=dist[target],
        hop_count=len(path) - 1,
        algorithm="Dijkstra",
        is_reachable=True,
        next_hop=next_hop
    )


def compute_dijkstra_routing_table(
    graph: Dict[str, Dict[str, float]],
    router_id: str,
    node_ip_map: Optional[Dict[str, str]] = None
) -> RoutingTable:
    """
    Computes Dijkstra shortest paths from `router_id` to all accessible nodes in the graph
    and generates a populated RoutingTable instance.
    
    Args:
        graph (Dict[str, Dict[str, float]]): Active network adjacency list.
        router_id (str): Source router ID.
        node_ip_map (Optional[Dict[str, str]]): Optional mapping from node ID to IP/CIDR string.
        
    Returns:
        RoutingTable: Populated routing table for the router.
    """
    rt = RoutingTable(router_id=router_id)
    if router_id not in graph:
        return rt

    for dest_node in graph:
        if dest_node == router_id:
            # Self route (connected)
            dest_ip = node_ip_map.get(router_id, router_id) if node_ip_map else router_id
            rt.add_route(RoutingEntry(
                destination=dest_ip,
                next_hop="Direct",
                metric=0.0,
                interface="loopback",
                protocol="CONNECTED"
            ))
            continue

        res = dijkstra_shortest_path(graph, router_id, dest_node)
        if res.is_reachable and res.next_hop:
            dest_ip = node_ip_map.get(dest_node, dest_node) if node_ip_map else dest_node
            rt.add_route(RoutingEntry(
                destination=dest_ip,
                next_hop=res.next_hop,
                metric=res.total_cost,
                interface=f"link_{router_id}_{res.next_hop}",
                protocol="DIJKSTRA"
            ))

    return rt
