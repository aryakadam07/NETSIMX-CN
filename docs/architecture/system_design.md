# NetSimX — System Design Document
**Document ID:** NX-ARCH-002  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. System States & State Transition Lifecycle

NetSimX enforces a deterministic Finite State Machine (FSM) to prevent illegal runtime operations (e.g., modifying link bandwidth during a running packet burst, or starting a simulation on an empty graph).

```
                      ┌─────────────────┐
                      │  INITIALIZING   │
                      └────────┬────────┘
                               │ App bootstrap & DB verify
                               ▼
 ┌────────────────────────►  READY  ◄─────────────────────────┐
 │                             │   ▲                          │
 │         Start Simulation    │   │ Stop / Reset             │
 │         (Validation Pass)   │   │                          │
 │                             ▼   │                          │
 │     ┌───────────────►  CONFIGURING                         │
 │     │ (Add/Edit Nodes,     │                               │
 │     │  Links, IP/Subnets)  ▼ (Done)                        │
 │     │                    READY                             │
 │     │                       │                              │
 │     │                       ▼                              │
 │     │                    RUNNING ◄──────────────┐          │
 │     │                    │     │                │          │
 │     │      Pause Action  │     │ Resume Action  │          │
 │     │                    ▼     │                │          │
 │     │                  PAUSED ─┘                │          │
 │     │                    │                      │          │
 │     │                    ▼                      │          │
 │     │          All Packets Processed /          │          │
 │     │          Critical Error                   │          │
 │     │                    │                      │          │
 │     │                    ▼                      │          │
 │     └──────────────  COMPLETED / FAILED ────────┴──────────┘
```

### State Definitions & Transition Rules

| Current State | Permitted Next States | Trigger Event | Invariants & Constraints |
|---|---|---|---|
| `INITIALIZING` | `READY`, `FAILED` | System startup, SQLite schema check. | UI is locked; splash screen shown. |
| `READY` | `CONFIGURING`, `RUNNING` | User selects "Edit Topology" OR clicks "Start Simulation". | Requires $\ge 2$ connected nodes and valid IP assignments before moving to `RUNNING`. |
| `CONFIGURING` | `READY` | User finishes node/link edits and triggers "Validate Network". | Simulation engine is offline; no packets exist. |
| `RUNNING` | `PAUSED`, `COMPLETED`, `FAILED`, `READY` (Stop) | Background clock ticks; step generator active. | Topology structure (adding/deleting nodes) is **LOCKED**. Link/Node status (UP/DOWN) can be toggled to simulate dynamic failures. |
| `PAUSED` | `RUNNING`, `READY` (Reset) | User clicks "Resume" or "Step" or "Reset". | Clock is halted; all packet queues and in-flight latencies freeze in place. |
| `COMPLETED` | `READY` | All scheduled packets delivered or dropped; experiment saved. | Metrics are locked and committed to SQLite; results rendered on Dashboard. |
| `FAILED` | `READY` | Unrecoverable engine error (e.g., database disk full). | Error dialog displayed with actionable debug context; logs flushed. |

---

## 2. Centralized Configuration Design (`config/settings.py`)

No hardcoded "magic numbers" exist in NetSimX. All defaults, thresholds, UI themes, and simulation physical constants are declared centrally.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SimulationDefaults:
    DEFAULT_PACKET_SIZE_BYTES: int = 1024
    DEFAULT_BANDWIDTH_MBPS: float = 100.0
    DEFAULT_PROPAGATION_DELAY_MS: float = 10.0
    DEFAULT_QUEUE_CAPACITY_PACKETS: int = 50
    DEFAULT_TTL: int = 64
    TICK_INTERVAL_MS: int = 50           # Clock granularity (20 Hz)
    SPEED_MULTIPLIER_DEFAULT: float = 1.0

@dataclass(frozen=True)
class PathConfig:
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DB_PATH: Path = DATA_DIR / "db" / "netsimx.db"
    SAMPLE_NETWORKS_DIR: Path = DATA_DIR / "sample_networks"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

@dataclass(frozen=True)
class TrafficPresets:
    LOW_BURST_COUNT: int = 100
    MEDIUM_BURST_COUNT: int = 500
    HIGH_BURST_COUNT: int = 1000
    DEFAULT_INTER_PACKET_GAP_MS: float = 20.0
```

---

## 3. Structured Logging Architecture (`utils/logger.py`)

NetSimX implements a non-intrusive logging architecture using standard library `logging` with structured formatting and asynchronous Qt signal bridge.

```
┌─────────────────────┐
│  Engine / Service   │ ──► logger.info("Node R2 transitioned to DOWN")
└─────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│               NetSimX Logging Subsystem                │
├──────────────────────────┬─────────────────────────────┤
│ 1. Rotating File Handler │ 2. UI Log Streamer Handler  │
│    (logs/netsimx.log)    │    (Emits Qt Signal to UI)  │
│    Max 5MB x 5 backups   │    Non-blocking to Canvas   │
└──────────────────────────┴─────────────────────────────┘
```

### Log Levels & Educational Transparency
* `DEBUG`: Internal algorithm steps (e.g., "Dijkstra: Relaxed neighbor R3 from tentative cost 14 to 9 via R2").
* `INFO`: Major lifecycle events (e.g., "Simulation started with 500 packets", "Route recalculated via alternate path").
* `WARNING`: Network anomalies (e.g., "Interface buffer on R1 exceeded 80% capacity", "Packet P1042 dropped due to congestion").
* `ERROR`: Critical failures (e.g., "Destination Server1 unreachable: no route available", "Invalid IP address syntax").

---

## 4. Standardized Error Handling & Exception Hierarchy

All custom domain exceptions inherit from a base `NetSimXError` to ensure clean separation between expected networking conditions (e.g., "No Route Exists") and fatal application bugs.

```python
class NetSimXError(Exception):
    """Base class for all NetSimX domain exceptions."""
    def __init__(self, message: str, error_code: str = "ERR_GENERIC"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class TopologyError(NetSimXError):
    """Raised on invalid network topology configurations (e.g., disconnected nodes)."""
    pass

class AddressingError(TopologyError):
    """Raised on invalid IPv4/CIDR configuration (e.g., IP conflict, invalid mask)."""
    pass

class RoutingError(NetSimXError):
    """Raised when routing algorithms fail (e.g., destination unreachable)."""
    pass

class SimulationError(NetSimXError):
    """Raised when the simulation runner encounters an illegal operation."""
    pass

class DatabaseError(NetSimXError):
    """Raised when SQLite operations fail."""
    pass
```

### Error Flow Handling Strategy
1. **Engine Level:** Catches low-level failures, wraps them in a typed `NetSimXError` with diagnostic context, and logs them at `ERROR` level.
2. **Application / Controller Level:** Intercepts `NetSimXError`, halts or safely transitions the simulation FSM to `PAUSED` or `READY`, and emits a clean failure notification to the UI.
3. **Presentation Level (PyQt6):** Renders a student-friendly alert modal explaining *why* the error happened (e.g., *"Cannot route from PC1 to Server1 because Link R1-R2 is DOWN and no alternate path exists. Please inspect routing tables."*).
