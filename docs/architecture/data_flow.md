# NetSimX — Data Flow & Sequence Diagrams
**Document ID:** NX-ARCH-009  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Data Flow Diagrams (DFD)

### 1.1 DFD Level 0 (Context Level)

```
                       ┌────────────────────────────────┐
                       │          Student / User        │
                       └───────────────┬────────────────┘
                                       │
                         1. Topology   │  4. Real-time Telemetry,
                            Config &   │     Graphs, Alerts,
                            Commands   │     Comparison Results
                                       ▼
                       ┌────────────────────────────────┐
                       │            NetSimX             │
                       │     Simulation Platform        │
                       └───────┬────────────────┬───────┘
                               │                │
            2. Persist Run     │                │ 3. Read/Write
               & Metrics       ▼                ▼    Topology Files
                       ┌───────────────┐ ┌───────────────┐
                       │    SQLite     │ │  Local File   │
                       │   Database    │ │    System     │
                       └───────────────┘ └───────────────┘
```

### 1.2 DFD Level 1 (Component Data Flow)

```mermaid
flowchart TD
    User([User / GUI]) -->|1. Node/Link Config| TM[Topology Manager]
    TM -->|2. Active Graph Adjacency| RE[Routing Engine]
    User -->|3. Flow Parameters| TE[Traffic Engine]
    TE -->|4. Packets Enqueued| SE[Simulation Engine]
    RE -->|5. Optimal Path Vectors| SE
    User -->|6. Trigger Faults| FM[Failure Manager]
    FM -->|7. Invalidate Node/Link| TM
    TM -->|8. Graph Mutation Event| RE
    RE -->|9. Alternate Path Result| SE
    SE -->|10. Stream Packet State Changes| ME[Metrics Engine]
    ME -->|11. Real-time Aggregates| User
    ME -->|12. Final Experiment Data| DB[(SQLite Database)]
```

---

## 2. Sequence Diagrams

### 2.1 Sequence 1 — Start Simulation Run

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant GUI as MainWindow / Dashboard
    participant Ctrl as ApplicationController
    participant RE as RoutingEngine
    participant TE as TrafficGenerator
    participant Sim as SimulationEngine
    participant ME as MetricsEngine

    User->>GUI: Click "Start Simulation" (Algo: Dijkstra, Traffic: 500 pkts)
    GUI->>Ctrl: start_simulation(config)
    Ctrl->>RE: compute_shortest_path(src="PC1", dst="Server1", algo="Dijkstra")
    RE-->>Ctrl: PathResult(["PC1", "R1", "R2", "R4", "Server1"], cost=12, hops=4)
    Ctrl->>TE: generate_burst(count=500, src="PC1", dst="Server1")
    TE-->>Ctrl: list[Packet] (P1..P500 with assigned path)
    Ctrl->>Sim: initialize_run(packets, path)
    Ctrl->>Sim: start_clock(interval_ms=50)
    
    loop Every Simulation Tick (50ms)
        Sim->>Sim: step_packets_forward()
        Sim->>ME: record_packet_events(tick_events)
        ME-->>GUI: emit_telemetry_snapshot(PDR, Throughput, Delay)
        GUI->>GUI: update_canvas_glyphs_and_cards()
    end
```

### 2.2 Sequence 2 — Router Failure & Route Recalculation

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant GUI as Canvas / FailureView
    participant FM as FailureManager
    participant TM as TopologyManager
    participant RE as RoutingEngine
    participant Sim as SimulationEngine
    participant ME as MetricsEngine

    User->>GUI: Click "Fail Router R2"
    GUI->>FM: inject_node_failure("R2")
    FM->>FM: start_convergence_timer()
    FM->>TM: set_node_status("R2", DOWN)
    TM->>TM: set_incident_links_status("R2", DOWN)
    FM->>RE: invalidate_routes_containing("R2")
    
    RE->>TM: get_active_adjacency_matrix()
    TM-->>RE: Active Graph (Excludes R2)
    RE->>RE: dijkstra_shortest_path("PC1", "Server1")
    RE-->>FM: New Path: ["PC1", "R1", "R3", "R4", "Server1"], cost=16
    
    FM->>Sim: update_in_flight_routes(old_node="R2", new_path)
    Sim->>Sim: reroute_queued_packets()
    Sim->>Sim: packet_delivered_via_alternate_path()
    FM->>FM: stop_convergence_timer()
    FM->>ME: record_convergence_event(target="R2", recovery_time_ms=85)
    ME-->>GUI: alert("R2 Failed. Rerouted via R3. Convergence: 85 ms")
```

### 2.3 Sequence 3 — Packet Hop-by-Hop Transmission & Congestion Drop

```mermaid
sequenceDiagram
    autonumber
    participant P as Packet (P42)
    participant R1 as Router R1 (Queue)
    participant Link as Link (R1 -> R2)
    participant R2 as Router R2
    participant ME as MetricsEngine

    Note over R1: Packet arrives at R1 egress buffer
    alt Queue Depth < Q_max (50 packets)
        R1->>R1: enqueue(P42)
        Note over R1: Experienced Queuing Delay = D_queue
        R1->>Link: transmit(P42)
        Note over Link: Experienced Serialization + Prop Delay
        Link->>R2: receive(P42)
        Note over R2: TTL decremented to 63
        R2->>ME: emit(FORWARDED, node="R2", latency=18ms)
    else Queue Depth >= Q_max
        R1->>ME: emit(DROPPED_CONGESTION, node="R1")
        Note over P: Packet P42 Destroyed (Drop-Tail Overflow)
    end
```
