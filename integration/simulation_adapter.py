"""
NetSimX — Simulation Adapter (Member 4)
Wraps SimulationEngine in a QThread worker so the GUI never blocks.
Integrates SimulationTickSnapshot and register_tick_listener().
"""

import logging
from typing import Optional, Dict, Any, List

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from core.simulation import SimulationEngine, SimulationStats, SimulationTickSnapshot
from core.event_manager import EventManager
from traffic.generator import TrafficGenerator
from traffic.flow import FlowConfig
from core.packet import ProtocolType
from routing.routing_engine import RoutingEngine
from failures.failure_manager import FailureManager
from .topology_adapter import TopologyAdapter
from config.settings import SIM_DEFAULTS

logger = logging.getLogger("SimulationAdapter")


# ======================================================================
# Worker — runs inside QThread
# ======================================================================

class SimulationWorker(QObject):
    """
    Runs the simulation loop in a background thread.
    Emits Qt signals for each tick snapshot and final completion.
    """
    tick_received = pyqtSignal(object)          # SimulationTickSnapshot
    simulation_finished = pyqtSignal(object)    # SimulationStats
    error_occurred = pyqtSignal(str)

    def __init__(self, engine: SimulationEngine,
                 max_steps: int = 2000,
                 tick_interval_ms: float = 50.0):
        super().__init__()
        self._engine = engine
        self._max_steps = max_steps
        self._tick_ms = tick_interval_ms
        self._running = True

    def stop(self) -> None:
        self._running = False

    @pyqtSlot()
    def run(self) -> None:
        """Main simulation loop. Called by QThread.started signal."""
        try:
            logger.info("SimulationWorker: starting loop")
            for _ in range(self._max_steps):
                if not self._running:
                    break
                active = [p for p in self._engine.packets if p.is_active]
                if not active:
                    break
                snapshot = self._engine.step_clock(self._tick_ms)
                self.tick_received.emit(snapshot)

            final_stats = self._engine.stats
            logger.info(
                f"SimulationWorker: finished — sent={final_stats.packets_sent} "
                f"delivered={final_stats.packets_delivered} "
                f"dropped={final_stats.packets_dropped}"
            )
            self.simulation_finished.emit(final_stats)
        except Exception as exc:
            logger.error(f"SimulationWorker error: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))


# ======================================================================
# Adapter — public API for the GUI
# ======================================================================

class SimulationAdapter(QObject):
    """
    Public facade for running simulations.
    Manages QThread lifecycle and exposes Qt signals.
    """
    tick_received = pyqtSignal(object)
    simulation_finished = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, topology_adapter: TopologyAdapter):
        super().__init__()
        self._topo = topology_adapter
        self._routing_engine = RoutingEngine()
        self._engine: Optional[SimulationEngine] = None
        self._failure_manager: Optional[FailureManager] = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[SimulationWorker] = None
        self._snapshots: List[SimulationTickSnapshot] = []
        self._config: Dict[str, Any] = {}
        self._is_running = False

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, source: str, destination: str,
                  algorithm: str = "Dijkstra",
                  packet_count: int = 100,
                  packet_size: int = 1024,
                  traffic_level: str = "LOW") -> None:
        """Prepare the simulation engine without starting it."""
        self._config = {
            "source": source,
            "destination": destination,
            "algorithm": algorithm,
            "packet_count": packet_count,
            "packet_size": packet_size,
            "traffic_level": traffic_level,
        }
        logger.info(f"Simulation configured: {source}→{destination} "
                    f"[{algorithm}] {traffic_level} {packet_count}pkts")

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Builds the simulation engine and launches the worker thread."""
        if self._is_running:
            logger.warning("Simulation already running")
            return

        cfg = self._config
        if not cfg:
            self.error_occurred.emit("Simulation not configured. Call configure() first.")
            return

        network = self._topo.get_topology()
        source = cfg["source"]
        destination = cfg["destination"]
        algorithm = cfg["algorithm"]
        traffic_level = cfg.get("traffic_level", "LOW")
        packet_count = cfg.get("packet_count", 100)
        packet_size = cfg.get("packet_size", 1024)

        # Route
        try:
            result = self._routing_engine.find_path(
                network, source, destination, algorithm=algorithm)
        except Exception as exc:
            self.error_occurred.emit(f"Routing failed: {exc}")
            return

        if not result.is_reachable:
            self.error_occurred.emit(
                f"No route from {source} to {destination} using {algorithm}.")
            return

        route = result.path

        # Failure manager
        self._failure_manager = FailureManager(network)
        reroute_cb = self._routing_engine.create_reroute_handler(network, algorithm)

        # Simulation engine
        self._engine = SimulationEngine(network=network)
        self._engine.on_route_failed = reroute_cb

        # Register tick listener for snapshot collection
        self._snapshots = []

        def _collect_snapshot(snap: SimulationTickSnapshot) -> None:
            self._snapshots.append(snap)

        self._engine.register_tick_listener(_collect_snapshot)

        # Generate traffic
        flow_id = f"FLOW_{source}_{destination}"
        if traffic_level.upper() in ("LOW", "MEDIUM", "HIGH"):
            packets = TrafficGenerator.generate_preset(
                traffic_level, source, destination, route, flow_id=flow_id)
        else:
            # Custom
            from traffic.flow import FlowConfig
            flow_cfg = FlowConfig(
                flow_id=flow_id,
                source_id=source,
                destination_id=destination,
                packet_count=packet_count,
                packet_size_bytes=packet_size,
            )
            packets = TrafficGenerator.generate_flow(flow_cfg, route)

        self._engine.load_packets(packets)

        # Build and start thread
        self._thread = QThread()
        tick_ms = SIM_DEFAULTS.TICK_INTERVAL_MS
        self._worker = SimulationWorker(self._engine, max_steps=5000, tick_interval_ms=tick_ms)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.tick_received.connect(self.tick_received)
        self._worker.simulation_finished.connect(self._on_finished)
        self._worker.error_occurred.connect(self.error_occurred)

        self._is_running = True
        self._thread.start()
        logger.info("Simulation thread started")

    def stop(self) -> None:
        """Signals the worker to stop and waits for the thread to finish."""
        if not self._is_running:
            return
        if self._worker:
            self._worker.stop()
        if self._thread:
            self._thread.quit()
            self._thread.wait(3000)
        self._is_running = False
        logger.info("Simulation stopped")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @pyqtSlot(object)
    def _on_finished(self, stats: SimulationStats) -> None:
        self._is_running = False
        if self._thread:
            self._thread.quit()
            self._thread.wait(3000)
        self.simulation_finished.emit(stats)

    # ------------------------------------------------------------------
    # State accessors
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        return self._is_running

    def get_snapshots(self) -> List[SimulationTickSnapshot]:
        return list(self._snapshots)

    def get_current_stats(self) -> Dict[str, Any]:
        if self._engine is None:
            return {"packets_sent": 0, "packets_delivered": 0, "packets_dropped": 0}
        s = self._engine.stats
        return {
            "packets_sent": s.packets_sent,
            "packets_delivered": s.packets_delivered,
            "packets_dropped": s.packets_dropped,
            "pdr_percent": round(s.pdr_percent, 2),
            "plr_percent": round(s.plr_percent, 2),
            "average_delay_ms": round(s.average_delay_ms, 3),
            "average_hops": round(s.average_hops, 2),
        }

    def get_queue_history(self) -> Dict[str, list]:
        """Returns {link_id: List[QueueSample]} from all interface queues."""
        if self._engine is None:
            return {}
        return {
            link_id: list(q.history)
            for link_id, q in self._engine.interface_queues.items()
        }

    def get_failure_manager(self) -> Optional[FailureManager]:
        return self._failure_manager

    def get_current_config(self) -> Dict[str, Any]:
        return dict(self._config)
