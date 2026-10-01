# NetSimX — Module Interfaces & API Contracts
**Document ID:** NX-ARCH-010  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Internal Service Interface Contracts

NetSimX uses Python's structural subtyping (`typing.Protocol`) and abstract base classes (`abc.ABC`) to define immutable contracts between layers. Developers can implement or test modules independently using mock objects conforming to these protocols.

```
┌────────────────────────────────────────────────────────┐
│                   PyQt6 GUI Views                      │
└──────────────────────────┬─────────────────────────────┘
                           │ Calls Protocol Methods
                           ▼
┌────────────────────────────────────────────────────────┐
│             Application Service Protocols              │
├──────────────────────────┬─────────────────────────────┤
│ • ITopologyService       │ • IRoutingService           │
│ • ISimulationService     │ • ITrafficService           │
│ • IFailureService        │ • IAnalyticsService         │
│ • IDatabaseService       │ • IEventManager             │
└──────────────────────────┴─────────────────────────────┘
```

---

## 2. Protocol Definitions

### 2.1 Topology Service Interface (`ITopologyService`)
```python
from typing import Protocol, Optional
from core.node import Node, DeviceStatus
from core.link import Link
from core.network import NetworkTopology

class ITopologyService(Protocol):
    def create_network(self, name: str) -> NetworkTopology: ...
    def get_current_network(self) -> NetworkTopology: ...
    def add_node(self, node: Node) -> None: ...
    def remove_node(self, node_id: str) -> None: ...
    def add_link(self, link: Link) -> None: ...
    def remove_link(self, link_id: str) -> None: ...
    def update_node_status(self, node_id: str, status: DeviceStatus) -> None: ...
    def update_link_status(self, link_id: str, status: DeviceStatus) -> None: ...
    def validate_network(self) -> tuple[bool, list[str]]: ...
    def export_to_json(self, filepath: str) -> None: ...
    def import_from_json(self, filepath: str) -> NetworkTopology: ...
```

### 2.2 Routing Service Interface (`IRoutingService`)
```python
from typing import Protocol
from routing.routing_table import RoutingEntry
from dataclasses import dataclass

@dataclass(frozen=True)
class PathResult:
    source: str
    destination: str
    path: list[str]
    total_cost: float
    hop_count: int
    algorithm: str
    is_reachable: bool

class IRoutingService(Protocol):
    def calculate_path(self, source: str, destination: str, algorithm: str) -> PathResult: ...
    def get_routing_table(self, router_id: str, algorithm: str) -> list[RoutingEntry]: ...
    def invalidate_and_recalculate(self, failed_element_id: str) -> dict[str, PathResult]: ...
```

### 2.3 Traffic Service Interface (`ITrafficService`)
```python
from typing import Protocol
from core.packet import Packet, ProtocolType

class ITrafficService(Protocol):
    def configure_burst(
        self,
        source: str,
        destination: str,
        count: int,
        packet_size_bytes: int = 1024,
        interval_ms: float = 20.0,
        protocol: ProtocolType = ProtocolType.TCP
    ) -> list[Packet]: ...
    
    def generate_preset_flow(self, level: str, source: str, destination: str) -> list[Packet]: ...
```

### 2.4 Simulation Service Interface (`ISimulationService`)
```python
from typing import Protocol, Callable
from analytics.metrics import SimulationMetricsSnapshot

class ISimulationService(Protocol):
    def load_run(self, packets: list[Packet], algorithm: str) -> None: ...
    def start(self) -> None: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def stop(self) -> None: ...
    def step_single_tick(self) -> None: ...
    def set_speed(self, multiplier: float) -> None: ...
    def register_tick_listener(self, callback: Callable[[SimulationMetricsSnapshot], None]) -> None: ...
```

### 2.5 Failure Service Interface (`IFailureService`)
```python
from typing import Protocol

class IFailureService(Protocol):
    def fail_router(self, router_id: str) -> None: ...
    def restore_router(self, router_id: str) -> None: ...
    def fail_link(self, link_id: str) -> None: ...
    def restore_link(self, link_id: str) -> None: ...
    def schedule_event(self, timestamp_ms: float, event_type: str, target_id: str) -> None: ...
    def get_last_recovery_time_ms(self) -> float: ...
```

### 2.6 Analytics & Database Interfaces (`IAnalyticsService`, `IDatabaseService`)
```python
from typing import Protocol
import pandas as pd

class IAnalyticsService(Protocol):
    def get_current_metrics(self) -> SimulationMetricsSnapshot: ...
    def compare_runs(self, experiment_ids: list[str]) -> pd.DataFrame: ...
    def export_run_to_csv(self, experiment_id: str, filepath: str) -> None: ...

class IDatabaseService(Protocol):
    def initialize_schema(self) -> None: ...
    def save_network(self, network: NetworkTopology) -> None: ...
    def load_network(self, network_id: str) -> Optional[NetworkTopology]: ...
    def save_experiment_results(self, snapshot: SimulationMetricsSnapshot) -> str: ...
    def get_recent_experiments(self, limit: int = 10) -> list[dict]: ...
```
