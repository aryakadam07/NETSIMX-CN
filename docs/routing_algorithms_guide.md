# NetSimX — Member 2 Routing Algorithms & Routing Tables Complete Technical Guide
**Document ID:** NX-M2-DOC-001  
**Author:** Member 2 — Graph Theory, Routing Algorithms & Routing Tables  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Executive Summary & Module Overview

Member 2 is responsible for the graph-theoretic pathfinding layer, distributed routing protocol engines, router routing tables, and longest-prefix matching mechanics in NetSimX.

### Primary Responsibilities & Source Files:
- **`routing/dijkstra.py`**: Manual Link-State shortest path algorithm using a Min-Heap priority queue ($\mathcal{O}((V+E)\log V)$).
- **`routing/bellman_ford.py`**: Manual Distance-Vector edge relaxation algorithm with early termination and negative-cycle detection ($\mathcal{O}(VE)$).
- **`routing/distance_vector.py`**: Distributed Bellman-Ford Distance Vector engine implementing **Split Horizon** and **Poison Reverse** loop prevention.
- **`routing/routing_table.py`**: Routing table abstraction (`RoutingEntry`, `RoutingTable`) supporting **Longest-Prefix Matching (LPM)** via Python `ipaddress`.
- **`routing/routing_engine.py`**: Strategy Pattern controller integrating pathfinding strategies with `NetworkTopology` and `SimulationEngine`.
- **`tests/test_routing.py`**: 34 unit test cases covering all edge cases, negative cycles, LPM lookups, and protocol exchanges.

---

## 2. Theoretical Foundations & Algorithm Comparison

### 2.1 Dijkstra's Shortest Path Algorithm (Link-State / OSPF Basis)
- **Algorithm Type:** Single-source shortest path for graphs with non-negative edge weights ($w(u,v) \ge 0$).
- **Core Mechanics:**
  - Maintains tentative distance map `dist[u]`, predecessor map `prev[u]`, and settled set `visited`.
  - Uses Python `heapq` (Min-Heap) to greedily extract node $u$ with minimum tentative cost.
  - Relaxes outgoing edges: if $\text{dist}[u] + w(u,v) < \text{dist}[v]$, updates $\text{dist}[v]$ and pushes $(new\_cost, v)$ to priority queue.
- **Time Complexity:** $\mathcal{O}((V + E) \log V)$
- **Space Complexity:** $\mathcal{O}(V)$

### 2.2 Bellman-Ford Edge Relaxation Algorithm (RIP Basis)
- **Algorithm Type:** Single-source shortest path supporting arbitrary (including negative) edge weights.
- **Core Mechanics:**
  - Systematically relaxes all edges $|V| - 1$ times: $\text{dist}[v] = \min(\text{dist}[v], \text{dist}[u] + w(u,v))$.
  - Includes **Early Termination**: stops early if no distance update occurs during an iteration.
  - Performs a final $|V|$-th pass for **Negative-Cycle Detection**: raises `NegativeCycleError` if any edge can still be relaxed.
- **Time Complexity:** $\mathcal{O}(|V| \cdot |E|)$
- **Space Complexity:** $\mathcal{O}(V)$

### 2.3 Why Dijkstra Cannot Handle Negative Edge Weights (Mathematical Justification)
Dijkstra uses a **greedy choice property** where nodes popped from the Min-Heap are permanently marked as finalized (`visited`). This greedy strategy requires path costs to monotonically increase as paths grow longer (non-negative edge weights). If negative edge weights exist, a longer hop sequence could later yield a smaller cumulative cost, invalidating Dijkstra's finalized distance.

Bellman-Ford does **not** make greedy choices or permanently finalize nodes. By systematically relaxing all edges $|V| - 1$ times, it guarantees convergence to optimal shortest paths for all reachable vertices without greedy assumptions.

---

## 3. Distance Vector Engine, Split Horizon & Poison Reverse

### 3.1 Bellman-Ford Equation
Each router $x$ maintains a distance vector $D_x$ where for every destination $y$:
$$D_x(y) = \min_v \{ c(x,v) + D_v(y) \}$$

### 3.2 Count-to-Infinity Problem
When a link fails in a pure Distance Vector network, adjacent routers may exchange stale updates, creating a two-node routing loop where metrics increment indefinitely toward infinity ($\infty = 16.0$ in RIP).

### 3.3 Loop Prevention Mechanisms
1. **Split Horizon:** A router $X$ does **NOT** advertise a route for destination $Y$ back out to neighbor $V$ if $X$ learned the route to $Y$ through neighbor $V$.
2. **Poison Reverse:** A router $X$ **DOES** advertise destination $Y$ back to neighbor $V$, but sets the metric to $\infty$ ($16.0$), immediately poisoning reverse loops.

---

## 4. Routing Table & Longest-Prefix Matching (LPM)

### 4.1 Routing Table Structure (`RoutingEntry`)
| Field | Type | Description |
|---|---|---|
| `destination` | `str` | Network CIDR (`192.168.1.0/24`), Host IP (`10.0.0.1/32`), or Node ID (`Server1`) |
| `prefix_length` | `int` | Prefix mask length (e.g. `24` for `/24`) |
| `next_hop` | `str` | Next-hop router ID or IP address |
| `metric` | `float` | Cumulative path cost |
| `interface` | `Optional[str]` | Outgoing link/interface identifier |
| `protocol` | `str` | Source protocol (`CONNECTED`, `STATIC`, `DIJKSTRA`, `BELLMAN_FORD`, `DV`) |

### 4.2 Longest-Prefix Matching Selection Logic
When performing `RoutingTable.lookup(destination_ip)`:
1. Parse destination IP using Python `ipaddress`.
2. Filter entries whose subnet range contains `destination_ip`.
3. **Sort Candidates:**
   - **Priority 1:** Highest `prefix_length` (e.g. `/24` over `/16` over `/8`).
   - **Priority 2:** Lowest `metric` (if prefix lengths are equal).
   - **Priority 3:** Lexicographical tie-breaker on `next_hop`.
4. **Fallback:** Returns Default Route (`0.0.0.0/0`) if no specific subnet matches, or `None` if unreachable.

---

## 5. Link-State vs Distance-Vector Comparison Matrix

| Feature | Link-State (Dijkstra / OSPF) | Distance-Vector (Bellman-Ford / RIP) |
|---|---|---|
| **Topology Knowledge** | Full topology map known by every router | Knowledge only of direct neighbors & advertised vectors |
| **Algorithm** | Manual Min-Heap Dijkstra | Distributed Bellman-Ford |
| **Convergence Speed** | Fast ($\mathcal{O}((V+E)\log V)$ local computation) | Slower (iterative exchange rounds) |
| **Loop Prevention** | Naturally loop-free (SPF tree) | Requires Split Horizon / Poison Reverse / Hold-down |
| **Bandwidth Overhead** | Periodic / Event LSAs | Full routing vector exchanges |

---

## 6. Demonstration Scenarios & Terminal Commands

Run the Member 2 interactive terminal demo:

```powershell
python demo_routing_cli.py
```

### Scenario Breakdown:
- **Demo 1:** Dijkstra Shortest Path Calculation
- **Demo 2:** Bellman-Ford Shortest Path & Negative Cycle Check
- **Demo 3:** Distance Vector Iterative Exchange & Convergence
- **Demo 4:** Split Horizon Loop Prevention
- **Demo 5:** Poison Reverse Infinite Metric Advertisement
- **Demo 6:** Dynamic Link Failure & Alternate Path Failover
- **Demo 7:** Longest-Prefix Matching Routing Table Lookup
