# NetSimX — Team Ownership & Viva Defense Matrix
**Document ID:** NX-ARCH-011  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Work Allocation & Equal Contribution Breakdown

NetSimX is structured so that each of the 4 team members has complete technical autonomy over a core networking pillar, while sharing integration, unit testing, and documentation responsibilities.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        4-MEMBER OWNERSHIP MATRIX                       │
├───────────────────┬───────────────────┬───────────────────┬────────────┤
│     MEMBER 1      │     MEMBER 2      │     MEMBER 3      │  MEMBER 4  │
│  Topology, CIDR,  │  Routing Engines  │  Packet Engine,   │ GUI, Dash, │
│  Addressing & CPT │  & Path Selection │  Traffic & Failure│ SQLite, BI │
└───────────────────┴───────────────────┴───────────────────┴────────────┘
```

---

## 2. Member Profiles & Responsibilities

### Member 1 — Network Architecture, Addressing & Cisco Packet Tracer
* **Core Technical Responsibilities:**
  * Network topology models (`core/node.py`, `core/link.py`, `core/network.py`).
  * IPv4 CIDR addressing verification, subnet boundary calculations, gateway validation (`utils/validators.py`).
  * Creation of all 9 Cisco Packet Tracer `.pkt` topologies and Cisco IOS configuration files.
* **Primary Source Files:** `core/node.py`, `core/link.py`, `core/network.py`, `utils/validators.py`, `packet_tracer/*`.
* **Viva Defense Specialization:**
  1. *Subnetting Math:* Explain how a `/28` subnet mask yields 14 usable host IPs, broadcast, and network addresses.
  2. *VLAN Trunking:* Explain 802.1Q encapsulation, access vs trunk ports in Packet Tracer.
  3. *OSPF in Cisco IOS:* Explain Router IDs, Area 0 (Backbone Area), and neighbor formation states (`INIT`, `2-WAY`, `EXSTART`, `FULL`).
  4. *CPT Boundary:* Why can't Python directly control Packet Tracer, and how do their results validate each other?

---

### Member 2 — Graph Theory, Routing Algorithms & Routing Tables
* **Core Technical Responsibilities:**
  * Manual implementation of Dijkstra's algorithm using priority queue / min-heap (`routing/dijkstra.py`).
  * Manual implementation of Bellman-Ford algorithm with negative-cycle detection (`routing/bellman_ford.py`).
  * Distance-Vector routing table exchanges with Split Horizon & Poison Reverse (`routing/distance_vector.py`).
  * Router routing table formatting and prefix-matching logic (`routing/routing_table.py`).
* **Primary Source Files:** `routing/*`, `tests/test_routing.py`.
* **Viva Defense Specialization:**
  1. *Algorithmic Complexity:* Contrast Dijkstra's $O((V+E)\log V)$ with Bellman-Ford's $O(V \cdot E)$.
  2. *Negative Weights:* Why are negative edge weights mathematically invalid in real-world network metrics (delay/cost)?
  3. *Count-to-Infinity:* Explain the counting-to-infinity problem in Distance Vector protocols and how Split Horizon prevents two-node loops.
  4. *Link-State vs Distance-Vector:* Compare Link-State link advertisements (LSAs) with Distance Vector full routing table sharing.

---

### Member 3 — Packet Lifecycle, Queuing, Congestion & Failure Management
* **Core Technical Responsibilities:**
  * Packet model and discrete-event forwarding engine (`core/packet.py`, `core/simulation.py`).
  * Interface Drop-Tail FIFO buffer and queue congestion mechanics (`traffic/queue_model.py`).
  * Traffic burst generation and profiles (Low, Medium, High, Custom) (`traffic/generator.py`).
  * Fault injection manager and alternate route convergence stopwatch (`failures/*`).
* **Primary Source Files:** `core/packet.py`, `core/simulation.py`, `traffic/*`, `failures/*`, `tests/test_packet.py`, `tests/test_failures.py`.
* **Viva Defense Specialization:**
  1. *Delay Breakdown:* Derive total hop delay: $D_{hop} = D_{proc} + D_{queue} + D_{trans} + D_{prop}$.
  2. *Buffer Overflow:* Explain how Drop-Tail queuing causes packet drops during bursty traffic when arrival rate $\lambda > \text{service rate } \mu$.
  3. *In-flight Packet Policy:* What happens to packets queued at a router when its outgoing link suddenly fails?
  4. *Convergence Time:* How does NetSimX mathematically measure recovery time ($\Delta t_{recovery}$)?

---

### Member 4 — Presentation, Dashboard, Analytics & Database Persistence
* **Core Technical Responsibilities:**
  * Modern PyQt6 graphical user interface (`gui/*`).
  * Interactive canvas for topology editing and real-time packet movement visualization (`gui/topology_view.py`).
  * Performance analytics calculations (PDR, Throughput, Latency, Utilization) (`analytics/metrics.py`).
  * Matplotlib / PyQtGraph comparative charting (`analytics/graphs.py`).
  * SQLite schema, WAL mode, transaction pooling, and repository pattern (`database/*`).
* **Primary Source Files:** `gui/*`, `analytics/*`, `database/*`, `app.py`.
* **Viva Defense Specialization:**
  1. *Performance Formulas:* State and derive Packet Delivery Ratio (PDR %) and Throughput (Mbps).
  2. *Thread Safety:* Why must the simulation clock run in a `QThread` rather than blocking the Qt GUI event loop?
  3. *Database Architecture:* Explain the ER schema and why SQLite Write-Ahead Logging (WAL) is necessary for high-frequency packet telemetry.
  4. *Comparative Analysis:* Walk through how NetSimX experimentally compares Dijkstra vs Bellman-Ford under simulated link failure.

---

## 3. Git Branch & Collaboration Workflow

```
main (Tagged Production Releases: v0.1, v0.5, v1.0)
 └── develop (Continuous Integration)
      ├── feat/m1-topology-cpt        (Member 1)
      ├── feat/m2-routing-algos       (Member 2)
      ├── feat/m3-simulation-core     (Member 3)
      └── feat/m4-gui-analytics-db    (Member 4)
```

* **Integration Rule:** No member merges directly into `main`. All PRs target `develop` and require all unit tests (`pytest`) to pass cleanly.
* **Mock Testing:** Members 2, 3, and 4 test their modules against mock data classes defined in `core/` before final system assembly.
