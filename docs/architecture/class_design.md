# NetSimX — Class Design Document
**Document ID:** NX-ARCH-008  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 1. Class Diagram Architecture & Relationships

NetSimX uses strict object-oriented modeling with clear inheritance hierarchies for network devices and a Strategy pattern for routing algorithms.

```mermaid
classDiagram
    %% Device Inheritance Hierarchy
    class Node {
        <<abstract>>
        +str node_id
        +str name
        +NodeType node_type
        +str ip_address
        +str subnet_mask
        +Optional[str] gateway
        +DeviceStatus status
        +float pos_x
        +float pos_y
        +list[str] interfaces
        +is_up() bool
    }

    class Router {
        +RoutingTable routing_table
        +dict[str, DropTailQueue] interface_queues
        +lookup_next_hop(str dst_ip) Optional[str]
    }

    class Switch {
        +dict[str, str] mac_table
        +forward_frame(str in_port, str dst_mac) str
    }

    class EndDevice {
        <<abstract>>
        +str mac_address
        +Optional[str] default_gateway
    }

    class PC {
        +generate_ping(str target_ip) Packet
    }

    class Server {
        +list[str] hosted_services
    }

    Node <|-- Router : Inheritance
    Node <|-- Switch : Inheritance
    Node <|-- EndDevice : Inheritance
    EndDevice <|-- PC : Inheritance
    EndDevice <|-- Server : Inheritance

    %% Link & Queues
    class Link {
        +str link_id
        +str source
        +str destination
        +float cost
        +float bandwidth_mbps
        +float delay_ms
        +float loss_probability
        +DeviceStatus status
        +int queue_capacity
        +calculate_serialization_delay(int size_bytes) float
    }

    class DropTailQueue {
        +int max_size
        +list[Packet] buffer
        +enqueue(Packet p) bool
        +dequeue() Optional[Packet]
        +is_full() bool
        +get_occupancy() int
    }

    Link *-- DropTailQueue : Composition

    %% Network Topology Container
    class NetworkTopology {
        +str network_id
        +str name
        +dict[str, Node] nodes
        +dict[str, Link] links
        +add_node(Node n) void
        +remove_node(str node_id) void
        +add_link(Link l) void
        +remove_link(str link_id) void
        +to_adjacency_dict(bool active_only) dict
        +validate() ValidationReport
    }

    NetworkTopology o-- Node : Aggregation
    NetworkTopology o-- Link : Aggregation

    %% Packet Model
    class Packet {
        +str packet_id
        +str flow_id
        +str source_id
        +str destination_id
        +int size_bytes
        +ProtocolType protocol
        +int ttl
        +float created_time_ms
        +str current_node
        +list[str] route
        +PacketStatus status
        +float accumulated_delay_ms
        +int hops_traveled
        +decrement_ttl() bool
        +mark_delivered(float timestamp) void
        +mark_dropped(DropReason reason) void
    }

    %% Routing Algorithms (Strategy Pattern)
    class RoutingAlgorithm {
        <<interface>>
        +compute_path(dict graph, str src, str dst)* PathResult
    }

    class DijkstraStrategy {
        +compute_path(dict graph, str src, str dst) PathResult
    }

    class BellmanFordStrategy {
        +compute_path(dict graph, str src, str dst) PathResult
        +detect_negative_cycle(dict graph) bool
    }

    class DistanceVectorEngine {
        +compute_path(dict graph, str src, str dst) PathResult
        +exchange_tables() void
    }

    RoutingAlgorithm <|.. DijkstraStrategy : Implements
    RoutingAlgorithm <|.. BellmanFordStrategy : Implements
    RoutingAlgorithm <|.. DistanceVectorEngine : Implements

    class RoutingEngine {
        -RoutingAlgorithm _strategy
        +set_strategy(RoutingAlgorithm strategy) void
        +find_path(NetworkTopology net, str src, str dst) PathResult
        +generate_table_for_router(NetworkTopology net, str router_id) list[RoutingEntry]
    }

    RoutingEngine o-- RoutingAlgorithm : Strategy Association

    %% Simulation Engine
    class SimulationEngine {
        +NetworkTopology network
        +RoutingEngine routing_engine
        +float current_time_ms
        +bool is_running
        +tick(float dt_ms) SimulationTickResult
        +inject_packet(Packet p) void
    }

    SimulationEngine --> NetworkTopology : Uses
    SimulationEngine --> RoutingEngine : Uses
    SimulationEngine --> Packet : Coordinates
```

---

## 2. Design Patterns Utilized

1. **Strategy Pattern:** For `RoutingEngine` $\rightarrow$ `RoutingAlgorithm` (`DijkstraStrategy`, `BellmanFordStrategy`). Allows dynamic switching between Link-State and Distance-Vector protocols without modifying simulation code.
2. **Repository Pattern:** `DatabaseRepository` isolates SQL queries behind clean entity interfaces (`NetworkRepository`, `ExperimentRepository`).
3. **Observer / EventBus Pattern:** `EventManager` and `SimulationEngine` publish typed events (`PacketEvent`, `NodeStateEvent`), consumed asynchronously by the GUI and `MetricsEngine`.
4. **Composite / Container Pattern:** `NetworkTopology` safely encapsulates devices and bidirectional links while exposing graph theory views.
