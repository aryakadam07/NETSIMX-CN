# NetSimX — Routing Engine & Algorithms Design
**Document ID:** NX-ARCH-005  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Routing Engine Architecture

The Routing Engine implements a Strategy Pattern to decouple algorithmic computation from the simulation core. Any algorithm can be selected at runtime to compute shortest paths across the active topology graph.

```
                         ┌─────────────────────────┐
                         │   RoutingEngine (Base)  │
                         └────────────┬────────────┘
                                      │ Strategy Interface
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ DijkstraStrategy │         │BellmanFordStrategy│         │DistanceVectorEng.│
│ (Link-State / LS)│         │(Distance-Vector) │         │(Distributed Table│
│  Min-Heap O(ElogV│         │  Relaxation O(VE)│         │    Exchanges)    │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

---

## 2. Algorithm 1 — Manual Dijkstra (Link-State Shortest Path)

### Theoretical Foundation
Dijkstra's algorithm solves the single-source shortest path problem on graphs with non-negative edge weights. In Computer Networks, this forms the mathematical basis of **OSPF (Open Shortest Path First)** and **IS-IS**.

### Manual Min-Heap Implementation Design
* **Priority Queue:** Implemented using Python's standard `heapq` module to achieve $O((V + E) \log V)$ time complexity.
* **State Arrays:**
  * `dist[u]`: Tentative minimal metric from source to node $u$. Initialized to $\infty$, with $\text{dist}[src] = 0$.
  * `prev[u]`: Predecessor map recording the optimal incoming hop for path reconstruction.
  * `visited`: Set of settled nodes whose shortest distance from source is finalized.

```python
def dijkstra_shortest_path(graph: dict[str, dict[str, float]], source: str, target: str) -> PathResult:
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0.0
    
    pq = [(0.0, source)]  # (cost, node_id)
    visited = set()
    
    while pq:
        current_cost, u = heapq.heappop(pq)
        
        if u in visited:
            continue
        visited.add(u)
        
        if u == target:
            break
            
        for neighbor, weight in graph[u].items():
            if neighbor in visited:
                continue
            new_cost = current_cost + weight
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = u
                heapq.heappush(pq, (new_cost, neighbor))
                
    # Path reconstruction
    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = prev[curr]
    path.reverse()
    
    return PathResult(
        source=source,
        destination=target,
        path=path if path and path[0] == source else [],
        total_cost=dist[target] if dist[target] != float('inf') else float('inf'),
        hop_count=len(path) - 1 if len(path) > 1 else 0,
        algorithm="Dijkstra",
        is_reachable=(dist[target] != float('inf'))
    )
```

---

## 3. Algorithm 2 — Manual Bellman-Ford

### Theoretical Foundation
Bellman-Ford iteratively relaxes all edges in the network $|V| - 1$ times. It forms the algorithmic foundation of the **Routing Information Protocol (RIP)**.

### Features Implemented
* **Edge Relaxation:** For every directed edge $(u, v)$ with weight $w$:
  $$\text{If } \text{dist}[u] + w < \text{dist}[v] \implies \text{dist}[v] \leftarrow \text{dist}[u] + w, \quad \text{prev}[v] \leftarrow u$$
* **Negative Cycle Detection (Academic Demonstration):** Performs an additional $|V|$-th iteration. If any distance strictly decreases, a negative-weight cycle exists. In NetSimX, negative cycles are flagged as an invalid topology configuration.
* **Time Complexity:** $O(|V| \cdot |E|)$.
* **Space Complexity:** $O(|V|)$.

---

## 4. Distance Vector Engine & Routing Table Mechanics

### Routing Table Data Structure (`RoutingEntry`)
Every router in NetSimX maintains a standard routing table:

| Destination Subnet / Host | Next Hop Router | Metric (Total Cost) | Outgoing Interface |
|---|---|---|---|
| `192.168.1.0/24` | `Direct` | 0 | `eth0` |
| `192.168.2.0/24` | `R2` | 5 | `eth1` |
| `10.0.0.0/8` | `R3` | 12 | `eth2` |

### Count-to-Infinity Problem & Mitigations
When a link breaks in a pure Distance Vector network, routers may exchange stale updates, creating a routing loop where metrics increment toward infinity ($\infty = 16$ in RIP).
NetSimX models:
1. **Split Horizon:** A router never advertises a route back out the same interface through which it learned that route.
2. **Poison Reverse:** A router advertises the route back out the learning interface with an infinite metric ($\infty$), immediately poisoning reverse loops.

---

## 5. Route Invalidation & Recalculation Flow

When a network component fails at runtime, NetSimX executes an event-driven convergence flow:

```
[ Failure Event Injected ] ──► (e.g. Link R1-R2 FAILS)
            │
            ▼
[ Topology State Updated ] ──► Link(R1, R2).status = DOWN
            │
            ▼
[ Invalidate Affected Routes ] ──► Any active flow whose path contains (R1, R2)
            │
            ▼
[ Re-execute Path Search ] ──► RoutingEngine.compute_shortest_path(src, dst)
            │                  (Excludes all links/nodes with status == DOWN)
            ▼
      ┌─────┴─────────────────────────────────┐
      │                                       │
      ▼ Alternate Path Found                  ▼ Network Partitioned
[ Assign Alternate Route ]              [ Incur Dropped Packets ]
New Path: PC1 -> R1 -> R3 -> R4 -> Server1  Status: DROPPED_NO_ROUTE
Packets resume via new route            Log: ICMP Destination Unreachable
            │                                 │
            └────────────────┬────────────────┘
                             ▼
                 [ Compute Recovery Time ]
         Δt_recovery = T_first_alt_pkt - T_failure
```
