# NetSimX — Intelligent Network Design, Simulation & Performance Analysis System

<div align="center">

![NetSimX Banner](https://img.shields.io/badge/NetSimX-v1.0--Architecture--Freeze-0A84FF?style=for-the-badge&logo=cisco&logoColor=white)
<br/>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![GUI PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52.svg?style=flat-square&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![Graph NetworkX](https://img.shields.io/badge/Graph-NetworkX-gray.svg?style=flat-square&logo=networkx&logoColor=white)](https://networkx.org/)
[![Storage SQLite3](https://img.shields.io/badge/Storage-SQLite3-003B57.svg?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Visualization Matplotlib](https://img.shields.io/badge/Visualization-Matplotlib-11557c.svg?style=flat-square)](https://matplotlib.org/)
[![Academic Project](https://img.shields.io/badge/Academic-B.Tech%20CSE%20Capstone%20(20%20Marks)-orange.svg?style=flat-square)](#team-allocation--viva-defense-matrix)

**An interactive Computer Networks simulation, dynamic routing, traffic congestion, fault-recovery, and quantitative telemetry platform.**

[Architecture Blueprint](docs/architecture/system_architecture.md) • [System Design](docs/architecture/system_design.md) • [Component Design](docs/architecture/component_design.md) • [Quickstart Guide](#quickstart--installation) • [Packet Tracer Labs](#cisco-packet-tracer-lab-suite) • [Demo Walkthrough](#end-to-end-demonstration-storyline)

</div>

---

## 📌 Executive Summary

Modern Computer Networks curricula frequently present an educational gap:
* **Black-Box Enterprise Simulators (e.g., Cisco Packet Tracer):** Excellent for practicing Cisco IOS syntax, but conceal low-level algorithmic behavior (e.g., priority-queue state in Dijkstra, matrix updates in Bellman-Ford, interface buffer overflows, and millisecond convergence timelines).
* **Abstract Code Snippets:** Run shortest-path algorithms on static, idealized mathematical graphs without simulating real-world packet physics (serialization delay, finite buffer drop-tail queues, propagation latency, and dynamic in-transit rerouting).

**NetSimX resolves this problem through a Dual-Pillar Framework:**
1. **Pillar 1 — Real Cisco Packet Tracer Lab Suite:** Provides protocol verification (.pkt topologies, OSPF/RIP convergence, VLAN trunking, DHCP, and Cisco IOS CLI runbooks).
2. **Pillar 2 — Custom Python Simulation & Telemetry Platform:** A glass-box discrete-event simulator with an interactive PyQt6 canvas, customizable traffic generation, drop-tail buffer modeling, fault injection, SQLite telemetry logging, and comparative graphing.

> [!IMPORTANT]
> **Technical Honesty Declaration:** NetSimX does not use hidden APIs or unsupported IPC to automate Cisco Packet Tracer. Packet Tracer serves as the external industry-standard verification baseline, while our Python engine provides custom algorithmic stress-testing and empirical telemetry analytics.

---

## 🚀 Key System Features

```
Network Design  ──►  IP/CIDR Config  ──►  Routing Selection (Dijkstra/Bellman-Ford/DV)
        ▲                                                                │
        │                                                                ▼
Dashboard  ◄──  SQLite Analytics  ◄──  Failure Recovery  ◄──  Packet & Queue Sim
```

### 1. Interactive Topology Studio
* **Device Classes:** Routers, Layer-2 Switches, End-User PCs, and Enterprise Servers.
* **Link Parameterization:** Duplex channels with configurable Link Cost (metric), Bandwidth ($C$ in Mbps), Propagation Delay ($D_p$ in ms), and Baseline Packet Loss Rate ($P_{loss}$).
* **IPv4 & CIDR Engine:** Subnetting support from `/24` to `/30`, gateway validation, and duplicate IP collision checks.

### 2. Glass-Box Routing Algorithms (Manual Implementations)
* **Link-State (Manual Dijkstra):** Min-heap priority queue ($O((V+E)\log V)$) showing step-by-step neighbor relaxation.
* **Distance-Vector (Manual Bellman-Ford):** Iterative edge relaxation ($O(VE)$) with negative-cycle detection for academic demonstration.
* **Distance Vector Routing Tables:** Periodic vector advertisements with **Split Horizon** and **Poison Reverse** to eliminate the count-to-infinity loop problem.

### 3. Discrete-Event Packet Engine & Queue Dynamics
* **Packet Lifecycle:** `CREATED` $\rightarrow$ `QUEUED` $\rightarrow$ `TRANSMITTING` $\rightarrow$ `FORWARDED` $\rightarrow$ `DELIVERED` (or `DROPPED`).
* **Realistic Delay Physics:** Accurately derives transmission/serialization delay ($D_{trans} = \frac{S \times 8}{C}$), physical propagation delay ($D_{prop}$), and queuing wait time ($D_{queue}$).
* **Drop-Tail Congestion Model:** Finite router interface buffers ($Q_{max}$). Packets are dropped with reason `DROPPED_CONGESTION` when incoming traffic exceeds link bandwidth capacity.

### 4. Dynamic Failure & Autonomous Recovery
* **Fault Injection:** Instant or timeline-scheduled `ROUTER_DOWN`, `ROUTER_UP`, `LINK_DOWN`, and `LINK_UP` events.
* **In-Flight Rerouting:** Upstream routers automatically detect severed routes, consult the routing engine, and dynamically patch packet paths if an alternate route exists.
* **Convergence Measurement:** Mathematically records recovery time:
  $$\Delta t_{recovery} = T_{\text{first\_alternate\_delivered}} - T_{\text{failure\_injected}}$$

### 5. Telemetry, Analytics & Persistence
* **Live Dashboard Cards:** Real-time counters for Sent, Delivered, Dropped, Packet Delivery Ratio (PDR %), Average Delay (ms), Throughput (Mbps), and Interface Utilization (%).
* **Comparative Charts:** Integrated Matplotlib/PyQtGraph plots comparing algorithms side-by-side.
* **SQLite Relational Storage:** Embedded database with Write-Ahead Logging (WAL) storing topologies, experiments, packet-level traces, and convergence events.

---

## 📐 System Architecture

NetSimX follows a strict 5-layer **Clean Architecture** pattern. Internal communication uses decoupled Python typing protocols (`typing.Protocol`) and an asynchronous `EventBus`.

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION LAYER (PyQt6 UI)                                       │
│    MainWindow | Topology Canvas | Dashboard Cards | Routing Visualizer │
│    Traffic Sliders | Failure Injection Panel | Matplotlib Charts        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Calls Controller Actions
                                    │ Observes State via Qt Signals
┌───────────────────────────────────▼────────────────────────────────────┐
│ 2. APPLICATION / CONTROLLER LAYER (Use Cases & Orchestration)          │
│    AppController | TopologyService | RoutingService | SimService       │
│    TrafficService | FailureService | AnalyticsService | EventBus        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Invokes Core Engines
┌───────────────────────────────────▼────────────────────────────────────┐
│ 3. DOMAIN LAYER (Pure Business Entities & Value Objects)               │
│    Node (Router, Switch, PC, Server) | Link | Packet | RoutingTable     │
│    ExperimentRun | MetricSnapshot | NetworkEvent | Custom Exceptions   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Executes Domain Logic
┌───────────────────────────────────▼────────────────────────────────────┐
│ 4. ENGINE / CORE COMPUTATIONAL LAYER (Algorithms & Physics)            │
│    RoutingEngine (Dijkstra, Bellman-Ford, DV) | SimulationEngine       │
│    Traffic & Queue Engine (DropTail) | FailureManager | MetricsEngine  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Persists / Reads Data
┌───────────────────────────────────▼────────────────────────────────────┐
│ 5. INFRASTRUCTURE LAYER (Storage, Config & System Utilities)           │
│    SQLite Database (WAL Mode) | Repositories | File IO | Logger         │
└────────────────────────────────────────────────────────────────────────┘
```

Detailed architectural blueprints are documented in:
* [`docs/architecture/system_architecture.md`](docs/architecture/system_architecture.md) — Layer specifications & architectural reviews.
* [`docs/architecture/system_design.md`](docs/architecture/system_design.md) — Finite State Machine, configuration, and logging hierarchy.
* [`docs/architecture/component_design.md`](docs/architecture/component_design.md) — Inputs, outputs, and duties of all 9 core components.
* [`docs/architecture/module_interfaces.md`](docs/architecture/module_interfaces.md) — Typed interfaces and service contracts.
* [`docs/architecture/simulation_design.md`](docs/architecture/simulation_design.md) — Packet state machine and queuing math.
* [`docs/architecture/routing_design.md`](docs/architecture/routing_design.md) — Algorithmic specs for Dijkstra, Bellman-Ford, and Distance Vector.
* [`docs/architecture/failure_recovery_design.md`](docs/architecture/failure_recovery_design.md) — Dynamic rerouting and convergence tracking.
* [`docs/architecture/database_design.md`](docs/architecture/database_design.md) — Entity-Relationship schema and SQL DDL.
* [`docs/architecture/data_flow.md`](docs/architecture/data_flow.md) — DFD Level 0, Level 1, and Sequence Diagrams.
* [`docs/architecture/class_design.md`](docs/architecture/class_design.md) — OOP class diagrams, inheritance, and design patterns.
* [`docs/architecture/team_ownership.md`](docs/architecture/team_ownership.md) — 4-member breakdown and viva defense guide.

---

## 📊 Scientific & Mathematical Formulations

NetSimX implements textbook Computer Networks formulas directly in Python:

| Metric | Mathematical Formula | Meaning / Educational Significance |
|---|---|---|
| **Packet Delivery Ratio (PDR)** | $\text{PDR} = \frac{\text{Packets Delivered}}{\text{Packets Sent}} \times 100\%$ | Quantifies end-to-end network reliability under load. |
| **Packet Loss Ratio (PLR)** | $\text{PLR} = \frac{\text{Packets Dropped}}{\text{Packets Sent}} \times 100\%$ | Measures drops caused by buffer overflow or severed links. |
| **Throughput** | $\text{Throughput} = \frac{\sum \text{Delivered Payload Bits}}{\Delta t \times 10^6}\text{ (Mbps)}$ | Effective transmission rate of useful data over elapsed time. |
| **Serialization Delay** | $D_{trans} = \frac{\text{Size (bits)}}{\text{Bandwidth (bps)}} \times 1000\text{ (ms)}$ | Time required to push packet bits onto the physical wire. |
| **Hop Delay** | $D_{hop} = D_{proc} + D_{queue} + D_{trans} + D_{prop}$ | Total latency experienced across a single router hop. |
| **Drop-Tail Overflow** | $\text{Drop if } \text{Queue Depth } Q(t) \ge Q_{max}$ | Physical FIFO queue overflow model causing congestion loss. |
| **Convergence Time** | $\Delta t_{recovery} = T_{\text{first\_alt\_delivered}} - T_{\text{failure\_injected}}$ | Millisecond duration required to detect failure and reroute. |

---

## 👥 Team Allocation & Viva Defense Matrix

The project is structured for a **4-member B.Tech CSE team (20 Marks total, 5 marks per member)**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        4-MEMBER OWNERSHIP MATRIX                       │
├───────────────────┬───────────────────┬───────────────────┬────────────┤
│     MEMBER 1      │     MEMBER 2      │     MEMBER 3      │  MEMBER 4  │
│  Topology, CIDR,  │  Routing Engines  │  Packet Engine,   │ GUI, Dash, │
│  Addressing & CPT │  & Path Selection │  Traffic & Failure│ SQLite, BI │
└───────────────────┴───────────────────┴───────────────────┴────────────┘
```

| Member | Technical Domain & Source Files | Deliverables | Viva Defense Topics |
|---|---|---|---|
| **Member 1** | **Network Architecture, Addressing & Packet Tracer**<br/>`core/node.py`, `core/link.py`, `core/network.py`, `utils/validators.py`, `packet_tracer/*` | Topology graph, IPv4 validation, Subnetting engine, 9 Cisco Packet Tracer labs (.pkt) & CLI configs. | • CIDR subnet math (`/24` to `/30`).<br/>• 802.1Q VLAN trunking.<br/>• OSPF neighbor states (`INIT` $\rightarrow$ `FULL`).<br/>• Why CPT cannot be automated via Python. |
| **Member 2** | **Graph Theory & Routing Algorithms**<br/>`routing/dijkstra.py`, `routing/bellman_ford.py`, `routing/distance_vector.py`, `routing/routing_table.py` | Min-heap Dijkstra, Bellman-Ford with negative cycle check, DV with Split Horizon, routing tables. | • Time complexity ($O((V+E)\log V)$ vs $O(VE)$).<br/>• Negative weight implications in networking.<br/>• Count-to-infinity & Poison Reverse.<br/>• Link-State vs Distance-Vector comparison. |
| **Member 3** | **Packet Simulation, Queuing & Failure Engine**<br/>`core/packet.py`, `core/simulation.py`, `traffic/*`, `failures/*` | Discrete-event clock, Drop-tail queue buffer, traffic burst generator, route recovery stopwatch. | • 4 components of packet delay.<br/>• Buffer overflow drops ($\lambda > \mu$).<br/>• In-flight packet policy during link cuts.<br/>• Mathematical measurement of convergence time. |
| **Member 4** | **PyQt6 GUI, Dashboard, Analytics & Database**<br/>`gui/*`, `analytics/metrics.py`, `analytics/graphs.py`, `database/*`, `app.py` | Canvas UI, live metric cards, Matplotlib charts, SQLite WAL repository, experiment comparison. | • PDR and Throughput formula derivations.<br/>• Qt event loop & `QThread` concurrency.<br/>• SQLite Write-Ahead Logging (WAL).<br/>• Algorithmic comparison chart methodology. |

---

## 🛠️ Cisco Packet Tracer Lab Suite

NetSimX includes 9 lab experiments matching the Python simulation scenarios:

1. **Lab 01 — Basic IP Connectivity:** Peer-to-peer and switch-based LAN verification (ARP, ICMP ping).
2. **Lab 02 — IPv4 Subnetting & Addressing:** VLSM subnet planning across multiple departments.
3. **Lab 03 — VLANs & Inter-VLAN Routing:** Router-on-a-Stick (802.1Q encapsulation) and Access/Trunk ports.
4. **Lab 04 — Static Routing:** Manual route entry with default gateways and floating static routes.
5. **Lab 05 — RIP (Routing Information Protocol):** Distance-vector dynamic routing configuration and convergence.
6. **Lab 06 — OSPF (Open Shortest Path First):** Single-area Link-State routing with wildcard masks and cost tuning.
7. **Lab 07 — Packet Transmission in Simulation Mode:** Hop-by-hop PDU inspection through OSI layers.
8. **Lab 08 — Link & Router Failure Simulation:** Administrative shutdown of interfaces to observe failover.
9. **Lab 09 — Dynamic Convergence & Alternate Route Validation:** Comparing RIP vs OSPF convergence times.

All lab writeups, IOS commands, and `.pkt` files reside in [`packet_tracer/`](packet_tracer/).

---

## 🎬 End-to-End Demonstration Storyline

During the final project evaluation, the team executes the following 16-step demonstration script:

```
[ Step 1: Launch NetSimX ] ──► [ Step 2: Load Campus Topology ] ──► [ Step 3: View Adjacency Graph ]
                                                                             │
[ Step 6: Stream Live Packets ] ◄── [ Step 5: Select PC1 -> Server ] ◄── [ Step 4: Select Dijkstra ]
         │
         ▼
[ Step 7: Inspect Telemetry (PDR, Throughput, Delay) ] ──► [ Step 8: Spike Traffic (Show Congestion) ]
                                                                             │
[ Step 11: Alternate Path Computed via R3 ] ◄── [ Step 10: Invalidation ] ◄── [ Step 9: Fail Router R2 ]
         │
         ▼
[ Step 12: Record Convergence (85 ms) ] ──► [ Step 13: Compare Dijkstra vs Bellman-Ford Charts ]
                                                                             │
[ Step 16: Verify Cisco Packet Tracer Lab ] ◄── [ Step 15: View SQLite History ] ◄── [ Step 14 ]
```

---

## 💻 Quickstart & Installation

### Prerequisites
* **Python 3.11+** installed ([python.org](https://www.python.org/downloads/))
* **Git** installed ([git-scm.com](https://git-scm.com/))
* Optional: **Cisco Packet Tracer v8.2+** for opening `.pkt` lab files.

### 1. Clone Repository & Create Virtual Environment
```bash
# Clone the repository
git clone https://github.com/aryakadam07/NETSIMX-CN.git
cd NETSIMX-CN

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run Automated Architecture & Smoke Tests
```bash
pytest -v
```

### 4. Launch NetSimX Application
```bash
python app.py
```

---

## 📂 Repository Directory Layout

```text
NETSIMX-CN/
├── app.py                         # Application entry point & bootstrap
├── requirements.txt               # Locked dependencies (PyQt6, NetworkX, Matplotlib, pytest)
├── README.md                      # Primary project presentation & documentation
├── config/
│   ├── __init__.py
│   └── settings.py                # Centralized physical constants, defaults, and colors
├── core/
│   ├── __init__.py
│   ├── node.py                    # Router, Switch, PC, and Server models
│   ├── link.py                    # Bandwidth, Delay, Loss, and Link objects
│   ├── network.py                 # Topology graph manager & CIDR validation
│   ├── packet.py                  # Packet state machine & TTL tracking
│   ├── simulation.py              # Discrete-event clock & forwarding runner
│   └── event_manager.py           # Scheduled fault timeline engine
├── routing/
│   ├── __init__.py
│   ├── dijkstra.py                # Min-heap Dijkstra implementation
│   ├── bellman_ford.py            # Bellman-Ford with negative-cycle check
│   ├── distance_vector.py         # DV table exchanges & Split Horizon
│   └── routing_table.py           # Router routing table models
├── traffic/
│   ├── __init__.py
│   ├── generator.py               # Burst & rate-limited traffic profiles
│   ├── queue_model.py             # Drop-Tail FIFO queue buffer
│   └── flow.py                    # Traffic flow configuration
├── failures/
│   ├── __init__.py
│   ├── failure_manager.py         # Node/Link state toggling & recalculator triggers
│   └── recovery.py                # Convergence stopwatch & alternate path selector
├── analytics/
│   ├── __init__.py
│   ├── metrics.py                 # PDR, Throughput, Delay, Utilization math
│   ├── graphs.py                  # Matplotlib & PyQtGraph canvas wrappers
│   └── comparison.py              # Cross-algorithm comparative matrices
├── database/
│   ├── __init__.py
│   ├── db.py                      # SQLite connection pool & WAL mode init
│   └── models.py                  # Repository pattern CRUD operations
├── gui/
│   ├── __init__.py
│   ├── main_window.py             # Main PyQt6 window & navigation tabs
│   ├── topology_view.py           # Interactive QGraphicsScene topology canvas
│   ├── dashboard_view.py          # Metric stat cards & live indicators
│   ├── routing_view.py            # Routing table visualizer & path highlight
│   ├── traffic_view.py            # Flow configuration dialogs & sliders
│   ├── failure_view.py            # Interactive failure triggers & event schedule
│   └── comparison_view.py         # Side-by-side algorithm comparison screen
├── utils/
│   ├── __init__.py
│   ├── validators.py              # IPv4, CIDR, and link sanity checkers
│   └── logger.py                  # Rotating file and UI logging streamer
├── data/
│   ├── sample_networks/           # Sample topology JSON templates
│   └── db/                        # SQLite storage directory (netsimx.db)
├── packet_tracer/
│   ├── configs/                   # Cisco IOS router/switch configuration scripts
│   ├── topologies/                # Cisco Packet Tracer lab files (.pkt)
│   └── lab_manuals/               # Step-by-step guides for Labs 01 through 09
├── docs/
│   └── architecture/              # Complete 11-document architecture specifications
└── tests/
    ├── test_topology.py           # Node, link, and graph integrity tests
    ├── test_routing.py            # Dijkstra, Bellman-Ford, and DV correctness
    ├── test_packet.py             # Packet state machine and delay tests
    ├── test_traffic.py            # Queue overflow and drop tests
    ├── test_failures.py           # Route invalidation and convergence tests
    └── test_metrics.py            # Telemetry calculation tests
```

---

## ⚖️ License & Academic Integrity

This project is developed as part of the **B.Tech Computer Science & Engineering (CSE) Computer Networks Capstone Project**. All source code is authored under the **MIT License**. Third-party libraries (`PyQt6`, `NetworkX`, `Matplotlib`, `pytest`) remain under their respective open-source licenses.
