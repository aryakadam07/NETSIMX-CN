# NetSimX — Member 4 Implementation Report
**Branch:** `member4-dashboard`  
**Status:** ✅ Complete — 73/73 tests passing

---

## 1. Files Created

### Application Entry Point
| File | Purpose |
|------|---------|
| `app.py` | Main entry point. Initialises Qt, creates database, launches MainWindow. |

### Database Layer (`database/`)
| File | Purpose |
|------|---------|
| `database/__init__.py` | Package exports |
| `database/schema.py` | All DDL `CREATE TABLE` statements + WAL/FK pragmas |
| `database/database.py` | Thread-local SQLite connection manager with WAL mode |
| `database/models.py` | Repository classes + record dataclasses (ExperimentRepository, MetricsRepository, EventRepository, TopologyRepository) |

### Analytics (`analytics/`)
| File | Purpose |
|------|---------|
| `analytics/__init__.py` | Package exports |
| `analytics/metrics.py` | MetricsCalculator: PDR, PLR, throughput, latency, jitter, utilization. All division-by-zero safe. |
| `analytics/comparison.py` | ExperimentComparator: side-by-side experiment comparison tables |

### Integration Adapters (`integration/`)
| File | Purpose |
|------|---------|
| `integration/__init__.py` | Package exports |
| `integration/topology_adapter.py` | Wraps NetworkTopology. Provides node/link dicts, stats, demo topology factory. |
| `integration/routing_adapter.py` | Wraps RoutingEngine. Calls Dijkstra/Bellman-Ford/DV. Returns plain dicts. |
| `integration/simulation_adapter.py` | QObject + QThread worker. Wraps SimulationEngine, emits tick_received/simulation_finished Qt signals. |
| `integration/failure_adapter.py` | Wraps FailureManager. fail_node/link, restore_node/link, query failures. |

### Experiments (`experiments/`)
| File | Purpose |
|------|---------|
| `experiments/__init__.py` | Package exports |
| `experiments/experiment_manager.py` | Full lifecycle: create→start→save_results→stop→export. Uses all repositories. |

### Export (`export/`)
| File | Purpose |
|------|---------|
| `export/__init__.py` | Package exports |
| `export/csv_exporter.py` | CSV export of metrics, events, full experiment |
| `export/json_exporter.py` | JSON export with metadata header |

### Visualization (`visualization/`)
| File | Purpose |
|------|---------|
| `visualization/__init__.py` | Package exports |
| `visualization/topology_visualizer.py` | NetworkX spring_layout → node positions. Node/link color helpers. |
| `visualization/charts.py` | MatplotlibCanvas (FigureCanvasQTAgg). line, multi-line, bar chart methods. |
| `visualization/packet_visualizer.py` | Packet status → color/label mapping |

### GUI Widgets (`gui/widgets/`)
| File | Purpose |
|------|---------|
| `gui/widgets/__init__.py` | Package exports |
| `gui/widgets/metric_card.py` | MetricCard: styled KPI card with title/value/unit + status colouring |
| `gui/widgets/alert_widget.py` | AlertWidget: scrollable timestamped alert feed (info/warning/critical/success) |

### GUI Panels (`gui/`)
| File | Purpose |
|------|---------|
| `gui/__init__.py` | Package marker |
| `gui/dashboard.py` | DashboardPanel: 16 live metric cards + alert feed. Consumes SimulationTickSnapshot. |
| `gui/topology_view.py` | TopologyView: QGraphicsScene canvas. Nodes as circles, links as lines. Route highlighting. Zoom/pan. |
| `gui/routing_panel.py` | RoutingPanel: source/dest/algo dropdowns, Calculate button, path display, routing table viewer |
| `gui/traffic_panel.py` | TrafficPanel: traffic configuration + Start/Stop simulation controls |
| `gui/failure_panel.py` | FailurePanel: node/link failure injection and restore with event log |
| `gui/monitoring_panel.py` | MonitoringPanel: live tick-by-tick metric cards + queue depth display + event log |
| `gui/analytics_panel.py` | AnalyticsPanel: 5 Matplotlib charts (Throughput, Latency, Loss, PDR, Queue Depth) |
| `gui/experiments_panel.py` | ExperimentsPanel: experiment history table, detail view, comparison table, CSV/JSON export |
| `gui/main_window.py` | MainWindow: central QMainWindow. Tab navigation (8 panels). Wires all signals. Prompt-to-save. Clean shutdown. |

### Tests (`tests/member4/`)
| File | Tests |
|------|-------|
| `tests/member4/__init__.py` | Package marker |
| `tests/member4/test_analytics.py` | 23 tests: PacketLoss, PDR, Throughput, Latency, Jitter, Utilization, from_sim_stats |
| `tests/member4/test_database.py` | 14 tests: ExperimentRepository, MetricsRepository, EventRepository, TopologyRepository |
| `tests/member4/test_experiments.py` | 12 tests: full lifecycle, start/stop, save_results, delete, export CSV, export JSON |
| `tests/member4/test_integration.py` | 24 tests: TopologyAdapter, RoutingAdapter (all 3 algorithms), FailureAdapter |

---

## 2. Existing Modules Integrated

| Module (Members 1-3) | Used By | How |
|---|---|---|
| `core/node.py` — Node, NodeType, DeviceStatus, Router, Switch, PC, Server | TopologyAdapter, demo topology | Creates nodes for demo topology; reads node fields |
| `core/link.py` — Link | TopologyAdapter, demo topology | Creates links for demo topology; reads link fields |
| `core/network.py` — NetworkTopology | TopologyAdapter, SimulationAdapter, FailureAdapter | All topology operations |
| `core/packet.py` — Packet, PacketStatus, ProtocolType | SimulationAdapter | Consumed indirectly through TrafficGenerator |
| `core/simulation.py` — SimulationEngine, SimulationStats, **SimulationTickSnapshot** | SimulationAdapter | Full simulation execution; tick listener registration |
| `core/event_manager.py` — EventManager | SimulationAdapter | Passed to SimulationEngine |
| `routing/routing_engine.py` — RoutingEngine | RoutingAdapter, SimulationAdapter | find_path(), generate_table_for_router(), create_reroute_handler() |
| `routing/dijkstra.py` — dijkstra_shortest_path, PathResult | RoutingAdapter (via RoutingEngine) | Dijkstra routing |
| `routing/bellman_ford.py` — bellman_ford_shortest_path | RoutingAdapter (via RoutingEngine) | Bellman-Ford routing |
| `routing/distance_vector.py` — DistanceVectorEngine | RoutingAdapter (via RoutingEngine) | Distance Vector routing |
| `routing/routing_table.py` — RoutingTable, RoutingEntry | RoutingAdapter | Routing table display |
| `traffic/generator.py` — TrafficGenerator | SimulationAdapter | generate_preset(), generate_flow() |
| `traffic/flow.py` — FlowConfig | SimulationAdapter | Custom traffic configuration |
| `traffic/queue_model.py` — DropTailQueue, **QueueSample** | SimulationAdapter | queue.history consumed for analytics charts |
| `failures/failure_manager.py` — FailureManager | FailureAdapter, SimulationAdapter | fail_node/link, restore_node/link, event_log |
| `config/settings.py` — PATHS, SIM_DEFAULTS, TRAFFIC_PRESETS | app.py, SimulationAdapter, TopologyAdapter | DB path, tick interval, packet presets |
| `utils/logger.py` — get_logger | app.py, adapters | Structured logging throughout |

---

## 3. Integration Points Used

### `SimulationTickSnapshot` (Member 3)
Fields consumed:
- `timestamp_ms` — tick time display, chart x-axis
- `active_packets_count` — live monitoring card
- `packets_delivered` — dashboard + monitoring cards
- `packets_dropped` — dashboard + monitoring cards
- `pdr_percent` — dashboard + monitoring cards
- `average_delay_ms` — latency card + jitter calculation
- `executed_events` — monitoring panel event log
- `queue_depths` — monitoring queue display + analytics chart

### `register_tick_listener()` (Member 3)
Used in `SimulationAdapter.start()`:
```python
self._engine.register_tick_listener(_collect_snapshot)
```
Snapshots are collected and emitted via Qt signals:
```python
self._worker.tick_received.connect(self.tick_received)
```
Connected in MainWindow to:
- `self._dashboard.update_metrics`
- `self._monitoring.on_tick`

### `queue.history` (Member 3 — `DropTailQueue.history: List[QueueSample]`)
Used in `SimulationAdapter.get_queue_history()`:
```python
return {link_id: list(q.history) for link_id, q in self._engine.interface_queues.items()}
```
Consumed by `AnalyticsPanel.plot_queue_depth()` to render Queue Depth vs Time charts.

---

## 4. Database Schema

**File:** `database/schema.py`

```
experiments       — id, name, created_at, topology(JSON), algorithm, source,
                    destination, duration_ms, packet_count, traffic_level, status
metrics           — id, experiment_id(FK), timestamp_ms, packets_sent/delivered/dropped,
                    throughput_mbps, avg_latency_ms, jitter_ms, utilization_pct,
                    pdr_percent, plr_percent, avg_hops
events            — id, experiment_id(FK), timestamp_ms, event_type, target, description
topology_nodes    — id, experiment_id(FK), node_id, node_name, node_type, ip_address,
                    status, pos_x, pos_y
topology_links    — id, experiment_id(FK), link_id, source, destination, cost,
                    bandwidth_mbps, delay_ms, status
```

Indexes: `idx_metrics_exp`, `idx_events_exp`, `idx_tnodes_exp`, `idx_tlinks_exp`
WAL mode: `PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA foreign_keys = ON;`

---

## 5. Test Results

```
73 passed, 0 failed  (0.78s)
```

| Test File | Tests | Result |
|---|---|---|
| test_analytics.py | 23 | ✅ All passed |
| test_database.py | 14 | ✅ All passed |
| test_experiments.py | 12 | ✅ All passed |
| test_integration.py | 24 | ✅ All passed |

---

## 6. Commands

### Run the Application
```bash
cd c:\Users\Swara\NETSIMX-CN
python app.py
```

### Run Member 4 Tests
```bash
cd c:\Users\Swara\NETSIMX-CN
python -m pytest tests\member4\ -v
```

### Run All Project Tests
```bash
cd c:\Users\Swara\NETSIMX-CN
python -m pytest tests\ -v
```

---

## 7. GUI Navigation

| Tab | Description |
|---|---|
| 🏠 Dashboard | 16 live KPI cards + alert feed. Updates on every simulation tick. |
| 🗺 Topology | Interactive QGraphicsScene. Zoom/pan. Route highlighting. Node/link status colours. |
| 🔀 Routing | Source/dest/algo selection. Calculate route. Path + cost + hops display. Routing table viewer. |
| 📡 Traffic Sim | Configure and start/stop simulations. LOW/MEDIUM/HIGH/CUSTOM traffic levels. |
| ⚡ Failure Sim | Inject node/link failures and restore. Updates topology canvas live. |
| 📊 Live Monitor | Tick-by-tick metric cards. Queue depth display. Simulation event log. |
| 📈 Analytics | 5 Matplotlib charts: Throughput, Latency, Packet Loss, PDR, Queue Depth. |
| 🗄 Experiments | Experiment history table. View details. Compare side-by-side. Export CSV/JSON. Delete. |

---

## 8. Known Limitations

1. **No topology editor UI** — the GUI uses the built-in demo topology (PC1→SW1→R1→R2/R3→R4→Server1). Loading custom topologies from file is not implemented in this version.
2. **Packet animation** — packets are not animated frame-by-frame on the topology canvas. Packet state is shown via status counters and the monitoring panel.
3. **PyQt6 requires display** — `app.py` requires a screen/display. Running headless (e.g. CI without virtual display) will fail. Tests that don't use Qt widgets work headless.
4. **Simulation speed** — very large packet counts (HIGH preset = 1000 pkts) may take several seconds. The UI remains responsive via QThread.
5. **Cisco Packet Tracer integration** — no direct Python↔Packet Tracer bridge (as documented in project specs). Results can be manually entered as experiments.

---

## 9. Git Status
```
Branch:        member4-dashboard
Committed:     NO  (awaiting your review)
Pushed:        NO  (awaiting your decision)
Main modified: NO
```
