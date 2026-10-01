# NetSimX — Failure & Recovery Engine Design
**Document ID:** NX-ARCH-006  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Centralized Failure Management Architecture

The Failure & Recovery Engine provides deterministic fault injection and automatic route re-convergence tracking. Faults can be triggered interactively by the user via the GUI or pre-programmed as timed events in an experiment script.

```
       ┌───────────────────────────────┐
       │     Interactive GUI Buttons   │
       │    (Fail Router / Fail Link)  │
       └───────────────┬───────────────┘
                       │ Manual Injection
                       ▼
       ┌───────────────────────────────┐        ┌───────────────────────────────┐
       │   Scheduled Timeline Events   │───────►│    Central Failure Manager    │
       │ (e.g. at t=5.0s, LINK_DOWN)   │ Event  │  (Status Mutation & Recovery) │
       └───────────────────────────────┘        └──────────────┬────────────────┘
                                                               │
                                       ┌───────────────────────┴───────────────────────┐
                                       ▼                                               ▼
                         ┌───────────────────────────┐                   ┌───────────────────────────┐
                         │   Topology State Update   │                   │    Convergence Tracker    │
                         │  (Node/Link UP <-> DOWN)  │                   │ (Records T_fail, T_recov) │
                         └─────────────┬─────────────┘                   └───────────────────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │   Global Event Dispatch   │
                         │ (ROUTE_INVALIDATION Event)│
                         └─────────────┬─────────────┘
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
   ┌───────────────────────────┐               ┌───────────────────────────┐
   │     Simulation Engine     │               │      Routing Engine       │
   │   (Purges/Reroutes In-    │               │  (Computes Alternative    │
   │    Flight & Queued Pkts)  │               │   Paths on Active Graph)  │
   └───────────────────────────┘               └───────────────────────────┘
```

---

## 2. Event Types & State Mutation Rules

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class NetworkEventType(str, Enum):
    ROUTER_DOWN = "ROUTER_DOWN"
    ROUTER_UP = "ROUTER_UP"
    LINK_DOWN = "LINK_DOWN"
    LINK_UP = "LINK_UP"
    TRAFFIC_SPIKE = "TRAFFIC_SPIKE"
    ROUTE_RECALCULATED = "ROUTE_RECALCULATED"

@dataclass
class ScheduledEvent:
    event_id: str
    trigger_time_ms: float
    event_type: NetworkEventType
    target_id: str                          # Node ID or Link ID
    parameters: Optional[dict] = None
    executed: bool = False
```

### Mutation Semantics
1. **`ROUTER_DOWN(target="R2")`:**
   * Node `R2` status is updated to `DeviceStatus.DOWN`.
   * **All links incident to `R2`** (e.g. `(R1, R2)`, `(R2, R4)`) are immediately flagged as inactive in the routing adjacency matrix.
   * Active packets queued inside `R2` are destroyed.
2. **`LINK_DOWN(target="L_R1_R2")`:**
   * Link `(R1, R2)` status is updated to `DeviceStatus.DOWN`.
   * Nodes `R1` and `R2` remain UP, but direct adjacency is severed.
3. **`ROUTER_UP` / `LINK_UP` (Recovery):**
   * Element status returns to `UP`.
   * Adjacency matrix is restored.
   * `RoutingEngine` recalculates optimal paths (which may revert to the restored, lower-cost path).

---

## 3. In-Flight & Buffer Packet Policy

To reflect realistic IP router behavior:
* **Packets on Severed Links:** Dropped immediately. Reason: `DROPPED_NO_ROUTE`.
* **Packets Queued at Upstream Router ($u$):**
  * If an alternate path from $u$ to destination exists, the packet's path is dynamically patched with the new sub-path:
    $$\text{path} \leftarrow [u, \dots, \text{new hops}, D]$$
    and transmission continues.
  * If no alternate path exists, the packet is discarded with reason `DROPPED_NO_ROUTE`.

---

## 4. Recovery Time Measurement Formulation

**Convergence / Recovery Time ($\Delta t_{recovery}$)** is defined as the elapsed time from fault occurrence until regular packet delivery resumes along the alternate path.

$$\Delta t_{recovery} = T_{\text{first\_alternate\_delivered}} - T_{\text{failure\_injected}}$$

```
Time Axis (ms):
───[ t = 2000 ms ]─────────────────────────[ t = 2085 ms ]──────────────────►
         │                                         │
   Failure Occurs:                          First Packet Delivered
   Link (R1, R2) Down                       via Alternate Path
   T_failure = 2000 ms                      (R1 -> R3 -> R4)
                                            T_recovery = 2085 ms
                                            
   ══════════════════════════════════════════════════════════════════════════
   Calculated Convergence Time: Δt_recovery = 2085 - 2000 = 85 ms
   ══════════════════════════════════════════════════════════════════════════
```

This metric is logged directly to the SQLite `metrics` table for empirical analysis.
