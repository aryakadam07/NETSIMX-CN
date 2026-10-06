"""
NetSimX — Manual Bellman-Ford Shortest Path Engine (Member 2)
Implements Bellman-Ford edge relaxation algorithm with early termination and negative cycle detection.
Calculates shortest paths across networks with arbitrary edge weights.
"""

from typing import Dict, List, Optional, Tuple
from routing.dijkstra import PathResult
from routing.routing_table import RoutingTable, RoutingEntry


class NegativeCycleError(Exception):
    """Raised when a negative-weight cycle is detected during Bellman-Ford edge relaxation."""
    pass


def bellman_ford_shortest_path(
    graph: Dict[str, Dict[str, float]],
    source: str,
    target: str
) -> PathResult:
    """
    Computes single-source shortest paths using manual Bellman-Ford algorithm with negative cycle detection.
    
    Theoretical Foundation & Comparison with Dijkstra:
    ---------------------------------------------------
    1. Why Dijkstra CANNOT handle negative edge weights:
       Dijkstra uses a greedy selection strategy (popping the smallest tentative distance from a min-heap)
       and permanently marks nodes as finalized (`visited`). This greedy assumption requires that path costs
       monotonically increase as paths grow longer (all edge weights >= 0). If a negative edge exists, a longer
       path sequence could later yield a smaller cumulative cost, invalidating Dijkstra's finalized distances.
       
    2. Why Bellman-Ford CAN handle negative edge weights:
       Bellman-Ford does NOT make greedy choices or permanently finalize nodes. Instead, it systematically
       relaxes EVERY edge in the graph |V| - 1 times. Since a simple path in a graph with |V| vertices contains
       at most |V| - 1 edges, relaxing all edges |V| - 1 times guarantees convergence to optimal shortest path
       distances for all reachable nodes, regardless of negative edge weights.
       
    3. Negative Cycle Detection:
       If a graph contains a cycle whose total edge weight sum is negative (< 0), distances can be reduced
       indefinitely by traversing the cycle repeatedly. Bellman-Ford detects this by running a final |V|-th pass.
       If any edge can still be relaxed after |V| - 1 iterations, a negative cycle exists.
       
    Time Complexity: O(|V| * |E|) where V = vertices, E = edges.
    Space Complexity: O(|V|) for distance and predecessor maps.
    
    Args:
        graph (Dict[str, Dict[str, float]]): Active network adjacency list.
        source (str): Source node ID.
        target (str): Target destination node ID.
        
    Returns:
        PathResult: Detailed path findings, cost, hop sequence, and next hop.
        
    Raises:
        NegativeCycleError: If a negative-weight cycle is detected in the graph.
    """
    # Edge Case 1: Empty graph or invalid source/target nodes
    if not graph or source not in graph:
        return PathResult(
            source=source,
            destination=target,
            path=[],
            total_cost=float('inf'),
            hop_count=0,
            algorithm="Bellman-Ford",
            is_reachable=False,
            next_hop=None
        )

    if target not in graph:
        return PathResult(
            source=source,
            destination=target,
            path=[],
            total_cost=float('inf'),
            hop_count=0,
            algorithm="Bellman-Ford",
            is_reachable=False,
            next_hop=None
        )

    # Edge Case 2: Source equals Target
    if source == target:
        return PathResult(
            source=source,
            destination=target,
            path=[source],
            total_cost=0.0,
            hop_count=0,
            algorithm="Bellman-Ford",
            is_reachable=True,
            next_hop=source
        )

    # --------------------------------------------------------------------------
    # STEP 1: INITIALIZATION
    # --------------------------------------------------------------------------
    # Initialize distances to infinity and predecessors to None
    dist: Dict[str, float] = {node: float('inf') for node in graph}
    dist[source] = 0.0

    prev: Dict[str, Optional[str]] = {node: None for node in graph}

    # Extract all directed edges as a list of tuples: (u, v, weight)
    edges: List[Tuple[str, str, float]] = []
    for u in graph:
        for v, weight in graph[u].items():
            edges.append((u, v, weight))

    num_vertices = len(graph)

    # --------------------------------------------------------------------------
    # STEP 2: RELAXATION LOOP (|V| - 1 PASSES)
    # --------------------------------------------------------------------------
    # Relax every edge |V| - 1 times
    for iteration in range(num_vertices - 1):
        updated = False  # Early termination flag

        for u, v, weight in edges:
            if dist[u] != float('inf') and dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                prev[v] = u
                updated = True

        # Early Termination Optimization: Stop if no edge distance was updated during this pass
        if not updated:
            break

    # --------------------------------------------------------------------------
    # STEP 3: NEGATIVE-CYCLE DETECTION PASS (|V|-TH PASS)
    # --------------------------------------------------------------------------
    for u, v, weight in edges:
        if dist[u] != float('inf') and dist[u] + weight < dist[v]:
            # A distance can still be decreased! Negative cycle detected.
            raise NegativeCycleError(
                f"Negative cycle detected! Edge ({u} -> {v}) with weight {weight} "
                f"can still be relaxed (dist[{u}]={dist[u]}, dist[{v}]={dist[v]})."
            )

    # --------------------------------------------------------------------------
    # STEP 4: PATH RECONSTRUCTION
    # --------------------------------------------------------------------------
    if dist[target] == float('inf'):
        return PathResult(
            source=source,
            destination=target,
            path=[],
            total_cost=float('inf'),
            hop_count=0,
            algorithm="Bellman-Ford",
            is_reachable=False,
            next_hop=None
        )

    path: List[str] = []
    curr: Optional[str] = target
    while curr is not None:
        path.append(curr)
        curr = prev[curr]
    path.reverse()

    next_hop = path[1] if len(path) > 1 else source

    return PathResult(
        source=source,
        destination=target,
        path=path,
        total_cost=dist[target],
        hop_count=len(path) - 1,
        algorithm="Bellman-Ford",
        is_reachable=True,
        next_hop=next_hop
    )


def compute_bellman_ford_routing_table(
    graph: Dict[str, Dict[str, float]],
    router_id: str,
    node_ip_map: Optional[Dict[str, str]] = None
) -> RoutingTable:
    """
    Computes Bellman-Ford shortest paths from `router_id` to all accessible nodes in the graph
    and generates a populated RoutingTable instance.
    
    Args:
        graph (Dict[str, Dict[str, float]]): Active network adjacency list.
        router_id (str): Source router ID.
        node_ip_map (Optional[Dict[str, str]]): Optional mapping from node ID to IP string.
        
    Returns:
        RoutingTable: Populated routing table for the router.
    """
    rt = RoutingTable(router_id=router_id)
    if router_id not in graph:
        return rt

    for dest_node in graph:
        if dest_node == router_id:
            dest_ip = node_ip_map.get(router_id, router_id) if node_ip_map else router_id
            rt.add_route(RoutingEntry(
                destination=dest_ip,
                next_hop="Direct",
                metric=0.0,
                interface="loopback",
                protocol="CONNECTED"
            ))
            continue

        try:
            res = bellman_ford_shortest_path(graph, router_id, dest_node)
            if res.is_reachable and res.next_hop:
                dest_ip = node_ip_map.get(dest_node, dest_node) if node_ip_map else dest_node
                rt.add_route(RoutingEntry(
                    destination=dest_ip,
                    next_hop=res.next_hop,
                    metric=res.total_cost,
                    interface=f"link_{router_id}_{res.next_hop}",
                    protocol="BELLMAN_FORD"
                ))
        except NegativeCycleError:
            # Leave unreachable / skip invalid negative cycles
            continue

    return rt
