# NetSimX — System Architecture Document
**Document ID:** NX-ARCH-001  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Status:** Approved Architectural Baseline  

---

## 1. System Objective & Overview

NetSimX is an educational yet production-grade Computer Networks design, simulation, and performance-analysis platform. It is engineered to solve a fundamental dilemma in undergraduate Computer Science pedagogy:

1. **Commercial Network Simulators (e.g., Cisco Packet Tracer, GNS3):** Feature-rich but act as "black boxes" regarding algorithm execution, queuing mechanics, and low-level performance math. They do not allow students to inspect intermediate relaxation matrices of Bellman-Ford, link-state priority queues in Dijkstra, or measure millisecond-resolution convergence timelines across custom loss distributions.
2. **Abstract Code Snippets:** Isolated scripts run algorithms on static graphs without simulating physical packet dynamics (serialization delay, drop-tail buffers, TTL expiration, traffic bursts, link recovery).

NetSimX combines:
* **Pillar 1 — Real Cisco Packet Tracer Labs:** Demonstrating realistic protocol behavior (OSPF, RIP, VLANs, NAT, DHCP, Cisco IOS CLI).
* **Pillar 2 — Custom Python Simulation & Analytics Platform:** A fully transparent, glass-box discrete-event simulation engine with a modern PyQt6 graphical interface, an SQLite experimental telemetry database, and statistical visualization tools.

---

## 2. Level 1 — Context Diagram (System Level)

The Level 1 Context Diagram establishes the operational boundary of NetSimX, its external actors, and the external data stores.

```
                                  ┌─────────────────────────┐
                                  │      Student / User     │
                                  │   (Network Designer)    │
                                  └────────────┬────────────┘
                                               │
                                               │ GUI Inputs (Topology, Traffic,
                                               │ Failures, Algorithm Selection)
                                               │ Live Telemetry & Visual Feedback
                                               ▼
┌─────────────────────────┐       ┌─────────────────────────┐       ┌─────────────────────────┐
│   Cisco Packet Tracer   │       │         NetSimX         │       │    Local File System    │
│   (External Standalone  │       │       Application       │◄─────►│ (Topology JSON Export,  │
│   Validation Suite)     │       │   (PyQt6 + Simulation)  │       │  Lab Runbooks, CSV/Logs)│
└─────────────────────────┘       └────────────┬────────────┘       └─────────────────────────┘
             ▲                                 │
             │ Independent                     │ Structured Transactions
             │ Manual Comparison               ▼ (WAL Mode)
             │                    ┌─────────────────────────┐
             └───────────────────►│     SQLite Database     │
               Empirical Data     │      (netsimx.db)       │
                                  └─────────────────────────┘
```

### External Actors & Boundary Contracts
1. **Student / User:** Interacts exclusively through the PyQt6 Presentation Layer. Designs topologies, adjusts device parameters (IPs, subnets, link bandwidth, delay, costs), triggers traffic bursts, injects failures, and inspects metrics.
2. **SQLite Database (`netsimx.db`):** Embedded relational storage storing persistent network configurations, experiment execution runs, packet-level traces, telemetry metrics, and fault events.
3. **Local File System:** Stores declarative network topology files (`.json`), configuration runbooks, and logging outputs.
4. **Cisco Packet Tracer (External Platform):** Independent, parallel verification environment. Topologies developed in NetSimX are mirrored in `.pkt` lab topologies to observe real-world Cisco IOS protocol convergence (RIP, OSPF, STP). **NetSimX does not execute fake IPC calls to Packet Tracer.**

---

## 3. Level 2 — High-Level Layered Architecture

NetSimX follows a strict 5-layer Clean Architecture pattern. Dependencies point **strictly downward**. No lower layer may ever import or depend upon a higher layer.

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION LAYER (PyQt6 UI)                                       │
│    • MainWindow & Central Navigation                                   │
│    • Topology Canvas (QGraphicsScene/View, Drag & Drop, Node Glyphs)   │
│    • Dashboard & Telemetry Cards (Sent, Delivered, Loss %, PDR, Delays)│
│    • Routing Inspector & Table Matrix Visualizer                       │
│    • Traffic & Congestion Controls (Sliders, Flow Profiles)            │
│    • Failure Injection & Event Timeline Panel                          │
│    • Analytics Charts (Matplotlib / PyQtGraph Canvas Integration)      │
│    • Experiment History & Comparison Screen                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Calls Controller Actions
                                    │ Observes State via Qt Signals
┌───────────────────────────────────▼────────────────────────────────────┐
│ 2. APPLICATION / CONTROLLER LAYER (Use Cases & Orchestration)          │
│    • ApplicationController (Central State Coordinator)                 │
│    • TopologyService (CRUD on Network Models, Subnet Validation)       │
│    • RoutingService (Path Calculation Requests, Routing Table Queries) │
│    • SimulationService (Thread Lifecycle, Play, Pause, Step, Stop)     │
│    • TrafficService (Flow Generation, Rate Shaping Profiles)           │
│    • FailureService (Fault Injection, Node/Link State Toggling)        │
│    • AnalyticsService (Metric Reductions, Comparative Studies)         │
│    • EventBus (Decoupled Global Observer Pattern)                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Invokes Core Engines
                                    │ Queries Repositories
┌───────────────────────────────────▼────────────────────────────────────┐
│ 3. DOMAIN LAYER (Pure Business Entities & Value Objects)               │
│    • NetworkTopology, Node (Router, Switch, PC, Server), Link          │
│    • Packet, ProtocolType, PacketStatus, DropReason                    │
│    • RoutingTable, RoutingEntry, PathResult                            │
│    • ExperimentRun, SimulationConfig, MetricSnapshot, NetworkEvent     │
│    • Custom Exceptions (TopologyError, RoutingError, SimulationError)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Executes Domain Logic
                                    │ State Mutation
┌───────────────────────────────────▼────────────────────────────────────┐
│ 4. ENGINE / CORE COMPUTATIONAL LAYER (Algorithms & Physics)            │
│    • RoutingEngine:                                                    │
│        - DijkstraStrategy (Min-Heap Link-State, $O((V+E)\log V)$)      │
│        - BellmanFordStrategy (Distance-Vector Relaxation, $O(VE)$)     │
│        - DistanceVectorEngine (Distributed Matrix Exchanges)           │
│    • SimulationEngine:                                                 │
│        - Discrete-Event Clock / Step Generator                         │
│        - Hop-by-Hop Transmission & Propagation Delay Math              │
│    • Traffic & Queue Engine:                                           │
│        - Drop-Tail Finite Interface Buffer ($Q_{max}$)                 │
│        - Bandwidth Serialization Delay Evaluator                       │
│    • Failure & Recovery Engine:                                        │
│        - Link/Node Failure Invalidation Listener                       │
│        - Convergence Time ($\Delta t_{recovery}$) Stopwatch           │
│    • Metrics Engine:                                                   │
│        - Real-Time Accumulators (PDR %, Loss %, Throughput, Latency)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Persists / Reads Data
                                    │ Emits Structured Logs
┌───────────────────────────────────▼────────────────────────────────────┐
│ 5. INFRASTRUCTURE LAYER (Storage, Config & System Utilities)           │
│    • SQLite Database Manager (Connection Pooling, Schema Migrations)   │
│    • Repositories: NetworkRepo, ExperimentRepo, MetricRepo, EventRepo  │
│    • File Storage (JSON Serializer/Deserializer for Topologies)        │
│    • Logging Subsystem (Rotating File Logger + UI Log Streamer)        │
│    • AppConfig & System Constants (Defaults, Colors, Bandwidth presets)│
└────────────────────────────────────────────────────────────────────────┘
```

### Justification of Architectural Layers
1. **Presentation Layer:** Isolates UI mechanics (Qt event loop, paint events, geometry) from simulation mathematics. Can be replaced with a Web UI or CLI test runner without altering a single line of networking logic.
2. **Application Layer:** Orchestrates multi-step workflows (e.g., "Inject link failure $\rightarrow$ invalidate affected routes $\rightarrow$ trigger recalculation $\rightarrow$ log event $\rightarrow$ notify UI").
3. **Domain Layer:** Clean, framework-agnostic Python dataclasses. Contains zero Qt imports and zero SQL queries.
4. **Engine Layer:** Implements standard Computer Networks mathematics and graph theory algorithms. Written for maximum clarity and educational transparency.
5. **Infrastructure Layer:** Manages persistence, transactions, and I/O. Uses standard SQLite with Write-Ahead Logging (WAL) to guarantee zero UI lockups during packet logging.

---

## 4. Formal Architecture Review

| Dimension | Architectural Assessment | Mitigation / Architectural Decision |
|---|---|---|
| **Coupling** | **Extremely Low:** Modules communicate via abstract protocols (`typing.Protocol`) and an `EventBus`. | The Simulation Engine does not hold a reference to `MainWindow`; it emits decoupled dataclass snapshots (`SimulationTickEvent`). |
| **Cohesion** | **High:** Single Responsibility Principle applied strictly. | Routing algorithms only compute paths; they do not know what a packet or queue is. The Traffic Engine generates packets; it does not forward them. |
| **Circular Dependencies** | **Zero:** Verified by unidirectional dependency hierarchy. | Application depends on Domain and Infrastructure; Domain depends on nothing; UI depends on Application. |
| **Scalability** | **Extensible via Strategy Pattern:** | New routing algorithms (e.g., AODV, OSPF Multi-Area, RIPv2) can be plugged in by inheriting from `RoutingAlgorithm` without touching the simulation core. |
| **Testability** | **100% Headless:** | All algorithms, queue mechanics, failure rerouting, and metrics math run in automated `pytest` suites without launching a GUI. |
| **Concurrency & Performance** | **Thread-Safe:** | The simulation clock runs in a dedicated background worker (`QThread` / `threading.Thread`) and posts thread-safe events to the Qt UI thread. |
