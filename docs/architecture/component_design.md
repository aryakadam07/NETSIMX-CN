# NetSimX — Component Design Document
**Document ID:** NX-ARCH-003  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Component Overview & Interaction Matrix

NetSimX decomposes the simulation platform into 9 cohesive components across the Application, Domain, and Engine layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION CONTROLLER                        │
└─────┬──────────────┬─────────────┬─────────────┬─────────────┬─────────┘
      │              │             │             │             │
      ▼              ▼             ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌────────────┐
│ Topology  │  │  Routing  │  │  Traffic  │  │  Failure  │  │ Experiment │
│  Manager  │  │  Engine   │  │  Engine   │  │  Manager  │  │  Manager   │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬──────┘
      │              │              │              │              │
      └──────────────┴──────────────┼──────────────┴──────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Packet Simulation  │
                         │       Engine        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Metrics Engine    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Database Repository │
                         └─────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Component 1 — Topology Manager (`core/network.py`)
* **Primary Responsibility:** Manages in-memory graph representation of the network topology, enforces device constraints, validates IP/subnet boundaries, and provides adjacency representations.
* **Key Functions:**
  * `create_network(name: str) -> NetworkTopology`
  * `add_node(node: Node) -> None`
  * `remove_node(node_id: str) -> None`
  * `add_link(link: Link) -> None`
  * `remove_link(link_id: str) -> None`
  * `set_node_status(node_id: str, status: DeviceStatus) -> None`
  * `set_link_status(link_id: str, status: DeviceStatus) -> None`
  * `validate_topology() -> ValidationResult`
  * `to_adjacency_dict(active_only: bool = True) -> dict[str, dict[str, float]]`
* **Inputs:** Raw node and link configurations from GUI canvas or JSON files.
* **Outputs:** Validated `NetworkTopology` instance and filtered graph representations for routing.

---

### 2.2 Component 2 — Routing Engine (`routing/`)
* **Primary Responsibility:** Executes shortest-path algorithms on the active network topology, maintains router routing tables, and computes alternate routes upon topology changes.
* **Algorithms Implemented:**
  1. **Manual Dijkstra:** Min-heap priority queue ($O((V+E)\log V)$), computes optimal link-cost paths from single source to all destinations.
  2. **Manual Bellman-Ford:** Iterative edge-relaxation ($O(VE)$), tracks predecessor pointers, detects negative cycles (used as academic demonstration).
  3. **Distance Vector Engine:** Models periodic vector advertisement, calculates distance updates, and handles count-to-infinity mitigation via Split Horizon and Poison Reverse.
* **Key Functions:**
  * `compute_shortest_path(source: str, destination: str, algorithm: str) -> PathResult`
  * `build_routing_table(router_id: str, algorithm: str) -> list[RoutingEntry]`
  * `recalculate_on_failure(failed_element_id: str) -> RecalculationReport`
* **Inputs:** Adjacency weight matrix from Topology Manager, source node ID, destination node ID.
* **Outputs:** `PathResult` (ordered list of nodes, total cost, hop count, algorithm name).

---

### 2.3 Component 3 — Packet Simulation Engine (`core/simulation.py`)
* **Primary Responsibility:** Drives the discrete-event clock, steps packets forward along their assigned paths, computes hop-by-hop latency components, evaluates drop triggers, and tracks in-transit state.
* **Key Functions:**
  * `initialize_run(experiment: ExperimentConfig) -> None`
  * `tick(delta_time_ms: float) -> SimulationTickEvent`
  * `step_packet(packet: Packet) -> PacketStepResult`
  * `deliver_packet(packet: Packet) -> None`
  * `drop_packet(packet: Packet, reason: DropReason) -> None`
* **Inputs:** Generated packets from Traffic Engine, routes from Routing Engine, physical link parameters (bandwidth, propagation delay, loss rate).
* **Outputs:** Real-time stream of `PacketEvent` items (delivered, in-transit, dropped) and clock ticks.

---

### 2.4 Component 4 — Traffic Engine (`traffic/generator.py`)
* **Primary Responsibility:** Creates simulated network traffic flows according to user-selected profiles without blocking the main application thread.
* **Traffic Levels:**
  * **Low:** 100 packets, spaced at 20 ms intervals.
  * **Medium:** 500 packets, spaced at 10 ms intervals.
  * **High (Congestion Stress):** 1000 packets, spaced at 2 ms intervals (exceeding link serialization capacity).
  * **Custom:** User-defined packet count, size (bytes), inter-packet interval (ms), and protocol (TCP/UDP/ICMP).
* **Inputs:** Source ID, destination ID, profile settings.
* **Outputs:** Sequenced stream of `Packet` objects enqueued into the Simulation Engine.

---

### 2.5 Component 5 — Congestion & Queue System (`traffic/queue_model.py`)
* **Primary Responsibility:** Emulates a physical router egress interface buffer. Implements standard Drop-Tail FIFO queuing logic.
* **Physics & Mathematics:**
  * Each directed link $(u, v)$ has an egress buffer of capacity $Q_{max}$ (default 50 packets).
  * Ingress rate $\lambda$ (packets/sec) vs Egress Service Rate $\mu = \frac{\text{Bandwidth (bps)}}{\text{Packet Size (bits)}}$.
  * If $\lambda > \mu$, queue depth $Q(t)$ expands linearly.
  * If $Q(t) \ge Q_{max}$, incoming packets are dropped with reason `DROPPED_CONGESTION`.
* **Inputs:** Packets arriving at intermediate router interfaces.
* **Outputs:** Queue occupancy metrics, queuing delay per packet, dropped packet signals.

---

### 2.6 Component 6 — Failure & Recovery Manager (`failures/failure_manager.py`)
* **Primary Responsibility:** Controls dynamic network faults, manages the scheduled event timeline, coordinates route invalidation, and measures network recovery convergence.
* **Supported Events:**
  * `ROUTER_DOWN`: Marks router as DOWN; all incident links are severed.
  * `ROUTER_UP`: Restores router to UP state.
  * `LINK_DOWN`: Marks specific directed/undirected link as DOWN.
  * `LINK_UP`: Restores link to UP state.
* **Convergence Measurement:** Records timestamp $T_{failure}$ when a link/node fails, triggers Routing Engine recalculation, and records $T_{recovery}$ when the first subsequent packet successfully traverses the alternate route. $\Delta t_{recovery} = T_{recovery} - T_{failure}$.
* **Inputs:** User manual failure buttons OR scheduled simulation timeline events.
* **Outputs:** Updated topology state, invalidation notices, recovery time metrics.

---

### 2.7 Component 7 — Metrics Engine (`analytics/metrics.py`)
* **Primary Responsibility:** Mathematical reduction of raw packet logs into standard networking performance indicators. Completely decoupled from the GUI.
* **Calculated Metrics:**
  * **Packet Delivery Ratio (PDR %):** $\frac{\text{Packets Delivered}}{\text{Packets Sent}} \times 100$
  * **Packet Loss Ratio (PLR %):** $\frac{\text{Packets Dropped}}{\text{Packets Sent}} \times 100$
  * **Throughput:** $\frac{\sum \text{Delivered Payload Bits}}{\text{Total Elapsed Time (s)}} \times 10^{-6}\text{ (Mbps)}$
  * **Average End-to-End Delay:** $\frac{\sum (\text{Delivery Time} - \text{Creation Time})}{\text{Packets Delivered}}\text{ (ms)}$
  * **Average Hop Count:** $\frac{\sum \text{Hop Count of Delivered Packets}}{\text{Packets Delivered}}$
  * **Network Utilization (%):** $\frac{\text{Active Bandwidth Used}}{\text{Total Available Bandwidth}} \times 100$
* **Inputs:** Stream of `Packet` lifecycle transitions from Simulation Engine.
* **Outputs:** `MetricSnapshot` emitted periodically to GUI and persisted to SQLite.

---

### 2.8 Component 8 — Experiment Manager (`analytics/comparison.py`)
* **Primary Responsibility:** Encapsulates complete test runs (Network + Algorithm + Traffic + Faults) into reproducible experiment objects, facilitating side-by-side comparative analysis (e.g., Dijkstra vs Bellman-Ford under 10% packet loss).
* **Inputs:** Simulation parameters and finished `MetricSnapshot`.
* **Outputs:** Historical records and comparative delta tables.

---

### 2.9 Component 9 — Database Repository Manager (`database/`)
* **Primary Responsibility:** Provides thread-safe, transactional data persistence to SQLite. Uses the Repository Pattern so the storage engine can be migrated to PostgreSQL/MySQL without altering application logic.
* **Repositories:**
  * `NetworkRepository`: Stores and retrieves network topologies and node/link coordinates.
  * `ExperimentRepository`: Stores experiment metadata, algorithm used, and traffic level.
  * `MetricsRepository`: Stores aggregate telemetry snapshots.
  * `EventRepository`: Stores failure and recovery timestamps.
