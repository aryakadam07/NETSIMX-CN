"""
NetSimX — Distance-Vector Routing Protocol Engine (Member 2)
Implements distributed Bellman-Ford Distance Vector routing with Split Horizon,
Poison Reverse, and Count-to-Infinity protection.
"""

from typing import Dict, List, Optional, Set
from routing.dijkstra import PathResult
from routing.routing_table import RoutingTable, RoutingEntry


class DistanceVectorEngine:
    """
    Simulates a distributed Distance-Vector (DV) routing protocol.
    
    Mathematical Principle (Bellman-Ford Equation):
    --------------------------------------------------
    Each router x maintains a distance vector D_x where for every destination y:
    
        D_x(y) = min_v { c(x,v) + D_v(y) }
        
    where:
    - x = current router
    - y = target destination
    - v = neighbor of router x
    - c(x,v) = link cost between router x and neighbor v
    - D_v(y) = neighbor v's advertised distance to destination y
    
    Loop Prevention & Convergence Mitigations:
    -------------------------------------------
    1. Standard Distance Vector: Exposes network to two-node/multi-node loops during link failure (Count-to-Infinity).
    2. Split Horizon: A router does NOT advertise a route for destination Y back out to neighbor V
       if router learned the route to Y THROUGH neighbor V.
    3. Poison Reverse: A router DOES advertise destination Y back to neighbor V, but sets the metric to INFINITY (16.0),
       explicitly poisoning any reverse loops immediately.
    """

    def __init__(
        self,
        graph: Optional[Dict[str, Dict[str, float]]] = None,
        split_horizon: bool = False,
        poison_reverse: bool = False,
        max_metric: float = 16.0
    ):
        """
        Args:
            graph (Optional[Dict[str, Dict[str, float]]]): Adjacency list representation of active topology.
            split_horizon (bool): Enables Split Horizon loop prevention rule.
            poison_reverse (bool): Enables Poison Reverse loop prevention rule (takes precedence over split_horizon).
            max_metric (float): Value representing infinity (RIP protocol standard = 16.0).
        """
        self.split_horizon = split_horizon
        self.poison_reverse = poison_reverse
        self.max_metric = max_metric

        # distance_vectors[x][y] = cost from router x to destination y
        self.distance_vectors: Dict[str, Dict[str, float]] = {}

        # next_hops[x][y] = next hop router ID from x to destination y
        self.next_hops: Dict[str, Dict[str, Optional[str]]] = {}

        # Original topology graph
        self.graph: Dict[str, Dict[str, float]] = {}

        if graph:
            self.initialize(graph)

    def initialize(self, graph: Dict[str, Dict[str, float]]) -> None:
        """
        Initializes distance vectors and next-hop entries for all routers in the graph.
        
        Initialization Rules:
        - D_x(x) = 0.0 (distance to self)
        - D_x(v) = c(x,v) for direct neighbors v
        - D_x(y) = max_metric (infinity) for all non-adjacent nodes y
        """
        self.graph = graph
        all_nodes = list(graph.keys())

        self.distance_vectors = {u: {v: self.max_metric for v in all_nodes} for u in all_nodes}
        self.next_hops = {u: {v: None for v in all_nodes} for u in all_nodes}

        for u in all_nodes:
            # Self-distance is 0
            self.distance_vectors[u][u] = 0.0
            self.next_hops[u][u] = u

            # Direct neighbor distances
            for v, weight in graph[u].items():
                if v in all_nodes:
                    self.distance_vectors[u][v] = weight
                    self.next_hops[u][v] = v

    def create_advertisement(self, router_id: str, to_neighbor: str) -> Dict[str, float]:
        """
        Constructs the Distance Vector advertisement emitted from `router_id` to `to_neighbor`.
        Applies Split Horizon or Poison Reverse rules based on configuration.
        
        Args:
            router_id (str): Advertising router ID.
            to_neighbor (str): Destination neighbor receiving the vector update.
            
        Returns:
            Dict[str, float]: Advertised vector {destination: metric}.
        """
        raw_vector = self.distance_vectors[router_id]
        advertisement: Dict[str, float] = {}

        for dest, metric in raw_vector.items():
            learned_via = self.next_hops[router_id].get(dest)

            # Check if this route was learned through `to_neighbor`
            is_learned_from_neighbor = (learned_via is not None and learned_via == to_neighbor)

            if is_learned_from_neighbor:
                if self.poison_reverse:
                    # Poison Reverse: Advertise back with infinite metric (16.0)
                    advertisement[dest] = self.max_metric
                elif self.split_horizon:
                    # Split Horizon: Do NOT advertise this route back to neighbor
                    continue
                else:
                    # Standard DV (No mitigation)
                    advertisement[dest] = metric
            else:
                advertisement[dest] = metric

        return advertisement

    def step_exchange(self) -> bool:
        """
        Simulates one synchronous iteration of vector exchange between all adjacent routers.
        
        Returns:
            bool: True if at least one router's distance vector was updated, False if network converged.
        """
        changed = False
        all_nodes = list(self.graph.keys())

        # Temporary storage to prevent intra-step order dependencies
        new_vectors: Dict[str, Dict[str, float]] = {u: dict(self.distance_vectors[u]) for u in all_nodes}
        new_next_hops: Dict[str, Dict[str, Optional[str]]] = {u: dict(self.next_hops[u]) for u in all_nodes}

        for u in all_nodes:
            for v, link_cost in self.graph[u].items():
                if v not in self.graph:
                    continue

                # Get vector advertised from neighbor v to router u
                advertised_vector = self.create_advertisement(router_id=v, to_neighbor=u)

                for dest, metric_from_v in advertised_vector.items():
                    if metric_from_v >= self.max_metric:
                        # If route was poisoned or unreachable from v
                        # Check if u currently uses v as next hop for dest
                        if new_next_hops[u].get(dest) == v:
                            if new_vectors[u][dest] != self.max_metric:
                                new_vectors[u][dest] = self.max_metric
                                changed = True
                        continue

                    candidate_cost = link_cost + metric_from_v

                    # Cap metric at max_metric (infinity)
                    if candidate_cost >= self.max_metric:
                        candidate_cost = self.max_metric

                    current_cost = new_vectors[u].get(dest, self.max_metric)

                    # Update condition: cheaper cost discovered OR update from current next-hop router
                    if candidate_cost < current_cost or (new_next_hops[u].get(dest) == v and candidate_cost != current_cost):
                        new_vectors[u][dest] = candidate_cost
                        new_next_hops[u][dest] = v if candidate_cost < self.max_metric else None
                        changed = True

        self.distance_vectors = new_vectors
        self.next_hops = new_next_hops

        return changed

    def run_to_convergence(self, max_iterations: int = 100) -> int:
        """
        Executes exchange steps repeatedly until distance vectors reach a stable equilibrium
        or `max_iterations` threshold is exceeded (preventing infinite loops in count-to-infinity).
        
        Returns:
            int: Number of exchange iterations executed until convergence.
        """
        iterations = 0
        while iterations < max_iterations:
            iterations += 1
            changed = self.step_exchange()
            if not changed:
                break
        return iterations

    def get_path(self, source: str, destination: str) -> PathResult:
        """
        Traces path from source to destination using converged next-hop tables.
        Handles loops and unreachable destinations safely.
        """
        if source not in self.distance_vectors or destination not in self.distance_vectors:
            return PathResult(
                source=source,
                destination=destination,
                path=[],
                total_cost=float('inf'),
                hop_count=0,
                algorithm="Distance-Vector",
                is_reachable=False,
                next_hop=None
            )

        cost = self.distance_vectors[source].get(destination, self.max_metric)
        if cost >= self.max_metric:
            return PathResult(
                source=source,
                destination=destination,
                path=[],
                total_cost=float('inf'),
                hop_count=0,
                algorithm="Distance-Vector",
                is_reachable=False,
                next_hop=None
            )

        path: List[str] = [source]
        curr = source
        visited: Set[str] = {source}

        while curr != destination:
            next_node = self.next_hops[curr].get(destination)
            if not next_node or next_node in visited or next_node not in self.graph:
                # Loop detected or dead-end next hop
                return PathResult(
                    source=source,
                    destination=destination,
                    path=[],
                    total_cost=float('inf'),
                    hop_count=0,
                    algorithm="Distance-Vector",
                    is_reachable=False,
                    next_hop=None
                )
            path.append(next_node)
            visited.add(next_node)
            curr = next_node

        next_hop = path[1] if len(path) > 1 else source

        return PathResult(
            source=source,
            destination=destination,
            path=path,
            total_cost=cost,
            hop_count=len(path) - 1,
            algorithm="Distance-Vector",
            is_reachable=True,
            next_hop=next_hop
        )

    def get_routing_table(self, router_id: str) -> RoutingTable:
        """
        Generates a RoutingTable object for the specified router containing its DV state.
        """
        rt = RoutingTable(router_id=router_id)
        if router_id not in self.distance_vectors:
            return rt

        for dest, cost in self.distance_vectors[router_id].items():
            if dest == router_id:
                rt.add_route(RoutingEntry(
                    destination=dest,
                    next_hop="Direct",
                    metric=0.0,
                    interface="loopback",
                    protocol="CONNECTED"
                ))
            elif cost < self.max_metric:
                next_h = self.next_hops[router_id].get(dest, "Unknown")
                rt.add_route(RoutingEntry(
                    destination=dest,
                    next_hop=next_h if next_h else "Unknown",
                    metric=cost,
                    interface=f"link_{router_id}_{next_h}",
                    protocol="DISTANCE_VECTOR"
                ))

        return rt
