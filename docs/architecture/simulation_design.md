# NetSimX — Simulation & Packet Engine Design
**Document ID:** NX-ARCH-004  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Packet Lifecycle & State Machine

Every packet traveling through NetSimX is modeled as an active finite state automaton. The diagram below illustrates every valid state and transition:

```
                            ┌───────────────┐
                            │    CREATED    │
                            └───────┬───────┘
                                    │ Packets enqueued into source buffer
                                    ▼
                            ┌───────────────┐
                     ┌─────►│    QUEUED     │
                     │      └───────┬───────┘
                     │              │ Egress bandwidth available & serialization starts
                     │              ▼
                     │      ┌───────────────┐
                     │      │ TRANSMITTING  │
                     │      └───────┬───────┘
                     │              │
      Hop Complete   │              ├──────────────────────────────────┐
    (Not Destination)│              │                                  │
                     │              ▼ Successful Propagation           ▼ Failure / Drop Trigger
                     │      ┌───────────────┐                  ┌───────────────┐
                     └──────┤   FORWARDED   │                  │    DROPPED    │
                            └───────┬───────┘                  └───────────────┘
                                    │ Destination Reached              ▲
                                    ▼                                  │
                            ┌───────────────┐                          │
                            │   DELIVERED   │                          │
                            └───────────────┘                          │
                                                                       │
                         ROUTE INVALIDATION BRANCH                     │
                         ┌─────────────────────┐                       │
                         │  TRANSMITTING /     │                       │
                         │      QUEUED         │                       │
                         └──────────┬──────────┘                       │
                                    │ Intermediate Link/Node Fails     │
                                    ▼                                  │
                         ┌─────────────────────┐                       │
                         │  ROUTE_UNAVAILABLE  │                       │
                         └──────────┬──────────┘                       │
                                    │ Trigger Route Recalculator       │
                                    ▼                                  │
                         ┌─────────────────────┐                       │
                         │ ROUTE_RECALCULATION │                       │
                         └──────┬───────────┬──┘                       │
                                │           │                          │
        Alternate Path Found    │           │ No Alternate Path Exists │
                                ▼           └──────────────────────────┘
                         ┌───────────────┐    (Drop Reason: NO_ROUTE)
                         │   FORWARDED   │
                         │ (via New Path)│
                         └───────────────┘
```

### State Definitions & Drop Categorization

| State | Detailed Operational Semantics |
|---|---|
| `CREATED` | Packet instantiated by `TrafficGenerator` with unique UUID, payload size, source, destination, and initial TTL (64). |
| `QUEUED` | Packet residing in the interface FIFO buffer (`DropTailQueue`) awaiting link availability. Experiences queuing delay. |
| `TRANSMITTING` | Packet undergoing serialization ($S/C$) and physical propagation across link $(u, v)$ with latency $D_p$. |
| `FORWARDED` | Packet has cleanly crossed link $(u, v)$ and arrived at intermediate router $v$. TTL is decremented ($TTL \leftarrow TTL - 1$). |
| `DELIVERED` | Packet has arrived at destination host ($v == \text{destination}$). Latency and hop count are permanently locked. |
| `ROUTE_UNAVAILABLE` | Next hop along pre-computed path has failed while packet was en route or queued at node $u$. |
| `ROUTE_RECALCULATION` | Node $u$ consults Routing Engine for an alternate path to the destination avoiding the severed element. |
| `DROPPED` | Terminal state for lost packets. Drop reason is permanently recorded. |

### Drop Reasons
1. `DROPPED_CONGESTION`: Interface buffer depth $Q(t) \ge Q_{max}$ at arrival time (Drop-Tail overflow).
2. `DROPPED_LOSS`: Link bit error simulation ($rand() < P_{loss}$).
3. `DROPPED_NO_ROUTE`: No viable path exists to destination (network partition or severed link with no alternative).
4. `DROPPED_TTL`: Hop count exceeded 64 (loop prevention).

---

## 2. In-Flight Packet Handling Policy During Failure

When a link $(u, v)$ or router $v$ fails during an active simulation run:
1. **Packets Queued at Node $u$ (About to enter $(u, v)$):**
   * Transmission is halted immediately.
   * Node $u$ invalidates its routing table entry for destination $D$.
   * `RoutingEngine.recalculate_route(source=u, destination=D)` is invoked on the remaining active topology.
   * **If an alternate route exists:** The packet's planned route is updated dynamically: $\text{route} \leftarrow [u, \dots, \text{new hops}, D]$, state transitions to `FORWARDED`, and the packet continues toward the destination.
   * **If no alternate route exists:** The packet is dropped immediately with drop reason `DROPPED_NO_ROUTE` (simulating an ICMP Destination Unreachable event).
2. **Packets Currently in Transit on Failed Link $(u, v)$:**
   * Physically destroyed on the wire; marked as `DROPPED_NO_ROUTE`.

---

## 3. Congestion & Queuing Mathematical Model

NetSimX emulates real-world interface queuing behavior using a discrete Drop-Tail FIFO queue per directed interface.

```
Incoming Packets (λ)
       │
       ▼
 ┌───────────┐      Buffer Capacity Q_max = 50 packets
 │ Drop-Tail │
 │   Queue   │ ──── [ P5 ] [ P4 ] [ P3 ] [ P2 ] [ P1 ] ───► Egress Serialization (μ)
 └─────┬─────┘                                              Bandwidth C (Mbps)
       │ If Current Depth >= Q_max
       ▼
  DROPPED_CONGESTION
```

### Mathematical Formulations

1. **Serialization / Transmission Delay ($D_{trans}$):**
   $$D_{trans} = \frac{\text{Packet Size (bits)}}{\text{Bandwidth (bps)}} = \frac{S \times 8}{C \times 10^6} \times 1000\text{ ms}$$
   * *Example:* 1024-byte packet on a 10 Mbps link:
     $$D_{trans} = \frac{1024 \times 8}{10 \times 10^6} \times 1000 = 0.8192\text{ ms}$$

2. **Propagation Delay ($D_{prop}$):**
   Configured per link (physical distance / signal velocity), typically 5 ms – 25 ms.

3. **Queuing Delay ($D_{queue}$):**
   For packet $k$ arriving when $N$ packets are ahead in the buffer:
   $$D_{queue} = \sum_{i=1}^{N} D_{trans}(P_i)$$

4. **Total Hop Latency:**
   $$D_{hop} = D_{queue} + D_{trans} + D_{prop}$$

5. **Drop-Tail Condition:**
   $$\text{If } \text{len}(Queue) \ge Q_{max} \implies \text{Drop incoming packet } P_{k}$$

6. **Interface Utilization ($U$):**
   $$U(t) = \frac{\text{Bits Transmitted over Interval } \Delta t}{C \times \Delta t \times 10^6} \times 100\%$$

---

## 4. Simulation Clock Loop (Discrete-Event Mechanics)

The simulation engine advances in discrete ticks of $\Delta t$ (default 50 ms):

```python
class SimulationEngine:
    def tick(self, delta_t_ms: float) -> SimulationTickResult:
        # 1. Process Event Manager (Check for scheduled node/link failures)
        self.event_manager.process_due_events(self.current_time_ms)
        
        # 2. Ingress Generator (Release new packets scheduled for this tick)
        new_packets = self.traffic_generator.get_packets_due(self.current_time_ms)
        for packet in new_packets:
            self.enqueue_packet(packet)
            
        # 3. Process All Active Interface Queues & Link Transmissions
        for link in self.network.get_active_links():
            link.process_tick(delta_t_ms, self.current_time_ms)
            
        # 4. Advance System Clock
        self.current_time_ms += delta_t_ms
        
        # 5. Compute Real-Time Telemetry Snapshot
        snapshot = self.metrics_engine.compute_snapshot(self.current_time_ms)
        return SimulationTickResult(snapshot=snapshot, active_packets=self.get_active_packet_count())
```
