"""
NetSimX — Main Application Window (Member 4 / Redesign)
Central QMainWindow shell featuring a left navigation sidebar, top header bar,
and dark charcoal & emerald design system.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QStatusBar, QMessageBox,
    QInputDialog, QApplication, QPushButton, QFrame, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QFont, QCloseEvent, QIcon

from integration.topology_adapter import TopologyAdapter
from integration.routing_adapter import RoutingAdapter
from integration.simulation_adapter import SimulationAdapter
from integration.failure_adapter import FailureAdapter
from database.database import Database
from experiments.experiment_manager import ExperimentManager
from config.settings import PATHS

from gui.styles import (
    MAIN_BG, SIDEBAR_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR,
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE,
    ACCENT_CORAL, get_application_stylesheet, get_button_stylesheet, get_secondary_button_stylesheet
)
from gui.dashboard import DashboardPanel
from gui.topology_view import TopologyView
from gui.routing_panel import RoutingPanel
from gui.traffic_panel import TrafficPanel
from gui.failure_panel import FailurePanel
from gui.monitoring_panel import MonitoringPanel
from gui.analytics_panel import AnalyticsPanel
from gui.experiments_panel import ExperimentsPanel
from gui.packet_tracer_panel import PacketTracerPanel
from gui.about_panel import AboutPanel

logger = logging.getLogger("MainWindow")


class MainWindow(QMainWindow):
    """
    Top-level application window shell.
    Features a left navigation sidebar, top header bar, and central QStackedWidget.
    Owns all adapters, database, and experiment manager services.
    """

    APP_TITLE = "NETSIMX — Network Simulation & Performance Analysis Studio"

    PAGES = [
        ("🏠", "Dashboard", "Overview metrics, topology summary & live alerts"),
        ("🗺", "Network Topology", "Interactive network canvas & layout design"),
        ("🔀", "Routing Algorithms", "Dijkstra, Bellman-Ford & Distance Vector analysis"),
        ("📡", "Traffic Simulation", "Discrete-event packet generator & traffic profiles"),
        ("⚡", "Failure & Recovery", "Fault injection, interface shutdown & failover rerouting"),
        ("📊", "Live Monitor", "Real-time packet stream & interface queue occupancy"),
        ("📈", "Performance Analytics", "Matplotlib throughput, latency, loss & queue charts"),
        ("🗄", "Experiment History", "SQLite experiment repository & side-by-side comparison"),
        ("📦", "Packet Tracer Labs", "Cisco Packet Tracer lab manual suite & IOS runbooks"),
        ("⚙️", "Settings & About", "System architecture specs & 4-member ownership matrix"),
    ]

    def __init__(self):
        super().__init__()
        self._setup_services()
        self._setup_ui()
        self._connect_signals()
        self._update_status("System Ready")
        logger.info("MainWindow initialized")

    # ------------------------------------------------------------------
    # Service initialization
    # ------------------------------------------------------------------

    def _setup_services(self) -> None:
        """Initialize database, topology adapter, and core engine adapters."""
        db_path = str(PATHS.DB_PATH)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db = Database(db_path)
        self._db.initialize()

        self._topo_adapter = TopologyAdapter()
        self._routing_adapter = RoutingAdapter(self._topo_adapter)
        self._sim_adapter = SimulationAdapter(self._topo_adapter)
        self._failure_adapter = FailureAdapter(self._topo_adapter, self._sim_adapter)
        self._exp_manager = ExperimentManager(self._db)

        logger.info("Core services initialized")

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setWindowTitle(self.APP_TITLE)
        self.resize(1340, 840)
        self.setMinimumSize(1080, 680)
        self.setStyleSheet(get_application_stylesheet())

        # Main central widget
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── 1. Left Navigation Sidebar ───────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_BG}; border-right: 1px solid {BORDER_COLOR};")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 16, 12, 16)
        sb_layout.setSpacing(12)

        # Logo Area
        logo_frame = QFrame()
        logo_frame.setStyleSheet("border: none; background: transparent;")
        logo_v = QVBoxLayout(logo_frame)
        logo_v.setContentsMargins(4, 0, 4, 8)

        logo_lbl = QLabel("⬡ NETSIMX")
        logo_font = QFont(); logo_font.setPointSize(15); logo_font.setBold(True)
        logo_lbl.setFont(logo_font)
        logo_lbl.setStyleSheet(f"color: {ACCENT_EMERALD}; letter-spacing: 1px;")

        tag_lbl = QLabel("Network Intelligence Studio")
        tag_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; font-weight: 500;")

        logo_v.addWidget(logo_lbl)
        logo_v.addWidget(tag_lbl)
        sb_layout.addWidget(logo_frame)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER_COLOR}; background-color: {BORDER_COLOR}; border: none; min-height: 1px;")
        sb_layout.addWidget(sep)

        # Navigation List Widget
        self._nav_list = QListWidget()
        self._nav_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                color: {TEXT_SECONDARY};
                padding: 10px 12px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
                margin-bottom: 2px;
            }}
            QListWidget::item:hover {{
                background-color: {CARD_BG};
                color: {TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {CARD_BG};
                color: {ACCENT_EMERALD};
                font-weight: bold;
                border-left: 3px solid {ACCENT_EMERALD};
            }}
        """)

        for icon, title, _ in self.PAGES:
            item = QListWidgetItem(f"{icon}  {title}")
            self._nav_list.addItem(item)

        self._nav_list.currentRowChanged.connect(self._on_page_changed)
        sb_layout.addWidget(self._nav_list)
        sb_layout.addStretch()

        # Sidebar footer badge
        sb_footer = QLabel("NETSIMX v1.0 • Branch: arya")
        sb_footer.setStyleSheet(f"color: #666666; font-size: 9px; padding: 4px;")
        sb_layout.addWidget(sb_footer)

        root_layout.addWidget(sidebar)

        # ── 2. Right Workspace Area (Header + Stacked Pages + Statusbar)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header Bar
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"background-color: {SIDEBAR_BG}; border-bottom: 1px solid {BORDER_COLOR};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Header Left: Page Title & Subtitle
        header_title_v = QVBoxLayout()
        header_title_v.setSpacing(2)
        self._header_title_lbl = QLabel("Dashboard")
        ht_font = QFont(); ht_font.setPointSize(13); ht_font.setBold(True)
        self._header_title_lbl.setFont(ht_font)
        self._header_title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY};")

        self._header_sub_lbl = QLabel("Overview metrics, topology summary & live alerts")
        self._header_sub_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")

        header_title_v.addWidget(self._header_title_lbl)
        header_title_v.addWidget(self._header_sub_lbl)
        header_layout.addLayout(header_title_v)

        header_layout.addStretch()

        # Header Right: System Indicators & Quick Action Button
        self._topo_badge = QLabel("Topology: CAMPUS_01")
        self._topo_badge.setStyleSheet(f"background: {CARD_BG}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_COLOR}; border-radius: 4px; padding: 4px 10px; font-size: 10px;")

        self._sim_status_lbl = QLabel("● IDLE")
        self._sim_status_lbl.setStyleSheet(f"background: {CARD_BG}; color: {TEXT_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 4px; padding: 4px 10px; font-size: 10px; font-weight: bold;")

        self._header_action_btn = QPushButton("▶  Run Traffic Sim")
        self._header_action_btn.setStyleSheet(get_button_stylesheet(ACCENT_EMERALD, "#101010"))
        self._header_action_btn.clicked.connect(lambda: self._nav_list.setCurrentRow(3)) # Navigate to Traffic Sim

        header_layout.addWidget(self._topo_badge)
        header_layout.addWidget(self._sim_status_lbl)
        header_layout.addWidget(self._header_action_btn)

        right_layout.addWidget(header)

        # ── 3. Central Stacked Widget Pages ──────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background-color: {MAIN_BG};")

        # Instantiate all panels
        self._dashboard       = DashboardPanel(self._topo_adapter, self._sim_adapter)
        self._topology_view   = TopologyView(self._topo_adapter)
        self._routing_panel   = RoutingPanel(self._topo_adapter, self._routing_adapter, self._topology_view)
        self._traffic_panel   = TrafficPanel(self._topo_adapter, self._sim_adapter)
        self._failure_panel   = FailurePanel(self._topo_adapter, self._failure_adapter, self._topology_view)
        self._monitoring      = MonitoringPanel(self._sim_adapter)
        self._analytics       = AnalyticsPanel()
        self._experiments     = ExperimentsPanel(self._exp_manager, self._analytics)
        self._packet_tracer   = PacketTracerPanel()
        self._about_panel     = AboutPanel()

        self._stack.addWidget(self._dashboard)
        self._stack.addWidget(self._topology_view)
        self._stack.addWidget(self._routing_panel)
        self._stack.addWidget(self._traffic_panel)
        self._stack.addWidget(self._failure_panel)
        self._stack.addWidget(self._monitoring)
        self._stack.addWidget(self._analytics)
        self._stack.addWidget(self._experiments)
        self._stack.addWidget(self._packet_tracer)
        self._stack.addWidget(self._about_panel)

        right_layout.addWidget(self._stack)

        # ── 4. Bottom Status Bar ───────────────────────────────────────
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {SIDEBAR_BG};
                color: {TEXT_SECONDARY};
                border-top: 1px solid {BORDER_COLOR};
                font-size: 10px;
            }}
        """)
        self.setStatusBar(self._status_bar)

        root_layout.addWidget(right_container)

        # Select Dashboard by default
        self._nav_list.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # Dashboard request to switch to topology
        self._dashboard.open_topology_requested.connect(lambda: self._nav_list.setCurrentRow(1))

        # Simulation signals
        self._sim_adapter.tick_received.connect(self._dashboard.update_metrics)
        self._sim_adapter.tick_received.connect(self._monitoring.on_tick)
        self._sim_adapter.simulation_finished.connect(self._on_simulation_finished)
        self._sim_adapter.error_occurred.connect(
            lambda msg: self._dashboard.add_alert(f"Simulation error: {msg}", "critical"))

        # Failure signals
        self._failure_panel.failure_occurred.connect(self._on_failure_occurred)
        self._failure_panel.recovery_occurred.connect(self._on_recovery_occurred)

        # Traffic start/stop
        self._traffic_panel.simulation_started.connect(self._on_sim_started)
        self._traffic_panel.simulation_stopped.connect(self._on_sim_stopped)

    # ------------------------------------------------------------------
    # Navigation slot
    # ------------------------------------------------------------------

    def _on_page_changed(self, index: int) -> None:
        if 0 <= index < len(self.PAGES):
            _, title, subtitle = self.PAGES[index]
            self._header_title_lbl.setText(title)
            self._header_sub_lbl.setText(subtitle)
            self._stack.setCurrentIndex(index)
            self._update_status(f"Viewed {title}")

    # ------------------------------------------------------------------
    # Simulation slots
    # ------------------------------------------------------------------

    def _on_sim_started(self) -> None:
        self._sim_status_lbl.setText("● RUNNING")
        self._sim_status_lbl.setStyleSheet(f"background: {CARD_BG}; color: {ACCENT_EMERALD}; border: 1px solid {ACCENT_EMERALD}; border-radius: 4px; padding: 4px 10px; font-size: 10px; font-weight: bold;")
        self._dashboard.set_simulation_state("RUNNING")
        self._dashboard.reset_metrics()
        self._monitoring.start_monitoring()
        self._update_status("Simulation running...")

    def _on_sim_stopped(self) -> None:
        if self._sim_status_lbl.text() == "● RUNNING":
            self._sim_status_lbl.setText("● IDLE")
            self._sim_status_lbl.setStyleSheet(f"background: {CARD_BG}; color: {TEXT_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 4px; padding: 4px 10px; font-size: 10px; font-weight: bold;")

    @pyqtSlot(object)
    def _on_simulation_finished(self, stats) -> None:
        self._sim_status_lbl.setText("● COMPLETED")
        self._sim_status_lbl.setStyleSheet(f"background: {CARD_BG}; color: {ACCENT_EMERALD}; border: 1px solid {ACCENT_EMERALD}; border-radius: 4px; padding: 4px 10px; font-size: 10px; font-weight: bold;")
        self._dashboard.set_simulation_state("COMPLETED")

        snapshots = self._sim_adapter.get_snapshots()
        queue_history = self._sim_adapter.get_queue_history()
        self._analytics.load_snapshots(snapshots, queue_history)

        self._dashboard.add_alert(
            f"Simulation complete — Sent: {stats.packets_sent} | "
            f"Delivered: {stats.packets_delivered} | PDR: {stats.pdr_percent:.1f}%", "success"
        )

        self._prompt_save_experiment(stats, snapshots)
        self._update_status("Simulation completed successfully.")

    @pyqtSlot(str, str)
    def _on_failure_occurred(self, ftype: str, target: str) -> None:
        self._dashboard.add_alert(f"FAILURE: {ftype} '{target}' is now OFFLINE", "critical")
        self._dashboard.update_topology_stats()
        self._update_status(f"Fault injected: {ftype} {target}")

    @pyqtSlot(str, str)
    def _on_recovery_occurred(self, ftype: str, target: str) -> None:
        self._dashboard.add_alert(f"RESTORED: {ftype} '{target}' is back ONLINE", "success")
        self._dashboard.update_topology_stats()
        self._update_status(f"Fault restored: {ftype} {target}")

    # ------------------------------------------------------------------
    # Experiment save prompt
    # ------------------------------------------------------------------

    def _prompt_save_experiment(self, stats, snapshots: list) -> None:
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
        if self._sim_adapter.is_running():
            self._sim_adapter.stop()
        try:
            self._db.close()
        except Exception:
            pass
        logger.info("Application closed")
        event.accept()

    def _update_status(self, msg: str) -> None:
        self._status_bar.showMessage(f"  {msg}", 5000)
