"""
NetSimX — Main Application Window (Member 4)
Central QMainWindow with tab navigation connecting all panels.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QMessageBox,
    QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QCloseEvent, QIcon

from integration.topology_adapter import TopologyAdapter
from integration.routing_adapter import RoutingAdapter
from integration.simulation_adapter import SimulationAdapter
from integration.failure_adapter import FailureAdapter
from database.database import Database
from experiments.experiment_manager import ExperimentManager
from config.settings import PATHS

from gui.dashboard import DashboardPanel
from gui.topology_view import TopologyView
from gui.routing_panel import RoutingPanel
from gui.traffic_panel import TrafficPanel
from gui.failure_panel import FailurePanel
from gui.monitoring_panel import MonitoringPanel
from gui.analytics_panel import AnalyticsPanel
from gui.experiments_panel import ExperimentsPanel

logger = logging.getLogger("MainWindow")


class MainWindow(QMainWindow):
    """
    Top-level application window.
    Owns all adapters, database, and experiment manager.
    Wires all panels together through signals and slots.
    """

    APP_TITLE = "NetSimX — Network Simulation & Analytics"

    def __init__(self):
        super().__init__()
        self._setup_services()
        self._setup_ui()
        self._connect_signals()
        self._update_status("Ready")
        logger.info("MainWindow initialized")

    # ------------------------------------------------------------------
    # Service initialization
    # ------------------------------------------------------------------

    def _setup_services(self) -> None:
        """Initialize all adapters and database services."""
        # Database
        db_path = str(PATHS.DB_PATH)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db = Database(db_path)
        self._db.initialize()

        # Adapters
        self._topo_adapter = TopologyAdapter()   # loads demo topology
        self._routing_adapter = RoutingAdapter(self._topo_adapter)
        self._sim_adapter = SimulationAdapter(self._topo_adapter)
        self._failure_adapter = FailureAdapter(self._topo_adapter, self._sim_adapter)

        # Experiment manager
        self._exp_manager = ExperimentManager(self._db)
        self._active_experiment_id: Optional[str] = None

        logger.info("Services initialized")

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setWindowTitle(self.APP_TITLE)
        self.resize(1280, 800)
        self.setMinimumSize(1024, 640)
        self.setStyleSheet("QMainWindow { background: #0F0F1A; }")

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("background: #0A0A18; border-bottom: 1px solid #333355;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        logo_lbl = QLabel("⬡ NetSimX")
        logo_font = QFont(); logo_font.setPointSize(14); logo_font.setBold(True)
        logo_lbl.setFont(logo_font)
        logo_lbl.setStyleSheet("color: #4A90D9;")

        subtitle_lbl = QLabel("Network Simulation & Performance Analysis")
        subtitle_lbl.setStyleSheet("color: #555577; font-size: 10px;")

        self._sim_status_lbl = QLabel("● IDLE")
        self._sim_status_lbl.setStyleSheet("color: #555577; font-size: 10px;")

        header_layout.addWidget(logo_lbl)
        header_layout.addWidget(subtitle_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self._sim_status_lbl)
        main_layout.addWidget(header)

        # ── Tab navigation ────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.West)
        self._tabs.setStyleSheet(
            "QTabWidget::pane { border: none; background: #1A1A2A; }"
            "QTabBar::tab { background: #0F0F18; color: #555577; "
            "padding: 12px 16px; border-right: 2px solid transparent; "
            "font-size: 10px; min-width: 110px; text-align: left; }"
            "QTabBar::tab:selected { color: #EEEEFF; "
            "border-right: 2px solid #4A90D9; background: #1A1A2A; }"
            "QTabBar::tab:hover { color: #AAAACC; background: #141424; }"
        )

        # Instantiate all panels
        self._dashboard       = DashboardPanel(self._topo_adapter, self._sim_adapter)
        self._topology_view   = TopologyView(self._topo_adapter)
        self._routing_panel   = RoutingPanel(self._topo_adapter, self._routing_adapter,
                                              self._topology_view)
        self._traffic_panel   = TrafficPanel(self._topo_adapter, self._sim_adapter)
        self._failure_panel   = FailurePanel(self._topo_adapter, self._failure_adapter,
                                              self._topology_view)
        self._monitoring      = MonitoringPanel(self._sim_adapter)
        self._analytics       = AnalyticsPanel()
        self._experiments     = ExperimentsPanel(self._exp_manager, self._analytics)

        # Add tabs with icons/labels
        tabs = [
            ("🏠  Dashboard",          self._dashboard),
            ("🗺  Topology",            self._topology_view),
            ("🔀  Routing",             self._routing_panel),
            ("📡  Traffic Sim",         self._traffic_panel),
            ("⚡  Failure Sim",         self._failure_panel),
            ("📊  Live Monitor",        self._monitoring),
            ("📈  Analytics",           self._analytics),
            ("🗄  Experiments",         self._experiments),
        ]
        for label, panel in tabs:
            self._tabs.addTab(panel, label)

        main_layout.addWidget(self._tabs)

        # ── Status bar ────────────────────────────────────────────────
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(
            "QStatusBar { background: #0A0A18; color: #555577; "
            "border-top: 1px solid #222233; font-size: 9px; }")
        self.setStatusBar(self._status_bar)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # Simulation tick → dashboard + monitoring
        self._sim_adapter.tick_received.connect(self._dashboard.update_metrics)
        self._sim_adapter.tick_received.connect(self._monitoring.on_tick)

        # Simulation finished → analytics + prompt to save
        self._sim_adapter.simulation_finished.connect(self._on_simulation_finished)

        # Simulation errors → dashboard alert
        self._sim_adapter.error_occurred.connect(
            lambda msg: self._dashboard.add_alert(f"Simulation error: {msg}", "critical"))

        # Routing result → topology highlight (already wired in RoutingPanel)
        # Failure events → dashboard alerts
        self._failure_panel.failure_occurred.connect(self._on_failure_occurred)
        self._failure_panel.recovery_occurred.connect(self._on_recovery_occurred)

        # Traffic panel start/stop → topology stats update
        self._traffic_panel.simulation_started.connect(self._on_sim_started)
        self._traffic_panel.simulation_stopped.connect(
            lambda: self._sim_status_lbl.setStyleSheet("color: #555577; font-size: 10px;"))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot(object)
    def _on_simulation_finished(self, stats) -> None:
        """Called when simulation completes. Load analytics and prompt save."""
        self._sim_status_lbl.setText("● COMPLETED")
        self._sim_status_lbl.setStyleSheet("color: #4A90D9; font-size: 10px;")
        self._dashboard.set_simulation_state("COMPLETED")

        # Load analytics charts
        snapshots = self._sim_adapter.get_snapshots()
        queue_history = self._sim_adapter.get_queue_history()
        self._analytics.load_snapshots(snapshots, queue_history)

        # Dashboard alert
        self._dashboard.add_alert(
            f"Simulation complete — Sent: {stats.packets_sent} | "
            f"Delivered: {stats.packets_delivered} | "
            f"PDR: {stats.pdr_percent:.1f}%", "success"
        )

        # Prompt to save
        self._prompt_save_experiment(stats, snapshots)
        self._update_status("Simulation completed")

    def _on_sim_started(self) -> None:
        self._sim_status_lbl.setText("● RUNNING")
        self._sim_status_lbl.setStyleSheet("color: #5CB85C; font-size: 10px;")
        self._dashboard.set_simulation_state("RUNNING")
        self._dashboard.reset_metrics()
        self._monitoring.start_monitoring()
        self._update_status("Simulation running...")

    @pyqtSlot(str, str)
    def _on_failure_occurred(self, ftype: str, target: str) -> None:
        self._dashboard.add_alert(
            f"FAILURE: {ftype} '{target}' is now OFFLINE", "critical")
        self._dashboard.update_topology_stats()
        self._update_status(f"Failure injected: {ftype} {target}")

    @pyqtSlot(str, str)
    def _on_recovery_occurred(self, ftype: str, target: str) -> None:
        self._dashboard.add_alert(
            f"RESTORED: {ftype} '{target}' is back ONLINE", "success")
        self._dashboard.update_topology_stats()

    # ------------------------------------------------------------------
    # Experiment save prompt
    # ------------------------------------------------------------------

    def _prompt_save_experiment(self, stats, snapshots: list) -> None:
        """Asks user if they want to save the completed simulation as an experiment."""
        cfg = self._sim_adapter.get_current_config()
        if not cfg:
            return

        reply = QMessageBox.question(
            self, "Save Experiment",
            "Simulation complete. Save results as an experiment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Get experiment name
        name, ok = QInputDialog.getText(
            self, "Experiment Name",
            "Enter a name for this experiment:",
            text=f"{cfg.get('algorithm','?')} {cfg.get('source','?')}→{cfg.get('destination','?')} "
                 f"{datetime.now().strftime('%H:%M')}"
        )
        if not ok or not name.strip():
            return

        try:
            exp_id = self._exp_manager.create_experiment(
                name=name.strip(),
                algorithm=cfg.get("algorithm", "Dijkstra"),
                source=cfg.get("source", ""),
                destination=cfg.get("destination", ""),
                traffic_level=cfg.get("traffic_level", "LOW"),
                packet_count=stats.packets_sent,
            )
            self._exp_manager.start_experiment(exp_id)
            self._exp_manager.save_results(exp_id, stats, snapshots)
            self._exp_manager.stop_experiment(exp_id)
            self._experiments.refresh_table()
            self._dashboard.add_alert(f"Experiment '{name}' saved.", "success")
            self._update_status(f"Experiment saved: {name}")
            QMessageBox.information(self, "Saved", f"Experiment '{name}' saved successfully.")
        except Exception as exc:
            logger.error(f"Failed to save experiment: {exc}")
            QMessageBox.warning(self, "Save Failed", f"Could not save experiment:\n{exc}")

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """Clean shutdown: stop simulation, close DB."""
        if self._sim_adapter.is_running():
            self._sim_adapter.stop()
        try:
            self._db.close()
        except Exception:
            pass
        logger.info("Application closed")
        event.accept()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_status(self, msg: str) -> None:
        self._status_bar.showMessage(f"  {msg}", 5000)
