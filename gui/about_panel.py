"""
NetSimX — Settings & System Architecture Panel (Member 4 Redesign)
Displays system overview, architecture, 4-member ownership matrix, and database info.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTextEdit, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.styles import (
    MAIN_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR, TEXT_PRIMARY,
    TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, get_groupbox_stylesheet
)
from config.settings import PATHS, SIM_DEFAULTS


class AboutPanel(QWidget):
    """System Architecture & Project Information panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"background-color: {MAIN_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        title = QLabel("System Architecture & Project Settings")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        sub = QLabel("NETSIMX — Intelligent Network Simulation & Performance Analysis Platform")
        sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(sub)

        # ── Group 1: Team Ownership & Responsibility Matrix ───────────
        team_group = QGroupBox("Team Ownership & Member Modules")
        team_group.setStyleSheet(get_groupbox_stylesheet())
        team_layout = QGridLayout(team_group)
        team_layout.setSpacing(10)

        members = [
            ("MEMBER 1 — Network Design & Cisco Packet Tracer",
             "Network topology, VLSM IP addressing, OSPF Area 0 configuration, Cisco Packet Tracer lab suite.",
             ACCENT_EMERALD),
            ("MEMBER 2 — Routing Algorithms & Tables",
             "Dijkstra, Bellman-Ford, Distance Vector implementations, route calculation engine, and routing tables.",
             ACCENT_ORANGE),
            ("MEMBER 3 — Discrete-Event Simulation & Fault Engine",
             "EventManager, Drop-Tail Queue model, traffic flow generation, packet lifecycle, failure manager.",
             "#34D399"),
            ("MEMBER 4 — GUI, Dashboard, Analytics & Database",
             "PyQt6 dashboard shell, Matplotlib charts, SQLite WAL persistence, experiment manager, UI redesign.",
             "#F59E0B"),
        ]

        for i, (m_title, m_desc, color) in enumerate(members):
            lbl_m = QLabel(m_title)
            lbl_m.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
            lbl_d = QLabel(m_desc)
            lbl_d.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10px;")
            lbl_d.setWordWrap(True)
            team_layout.addWidget(lbl_m, i, 0)
            team_layout.addWidget(lbl_d, i, 1)

        layout.addWidget(team_group)

        # ── Group 2: System Specifications ───────────────────────────
        specs_group = QGroupBox("System Constants & Environment")
        specs_group.setStyleSheet(get_groupbox_stylesheet())
        specs_layout = QGridLayout(specs_group)
        specs_layout.setSpacing(8)

        specs = [
            ("GUI Framework", "PyQt6 6.11 (Python 3.11+ / 3.13)"),
            ("Visualization Engine", "Matplotlib QTAgg / NetworkX Topology Layout"),
            ("Database Path", str(PATHS.DB_PATH)),
            ("Database Engine", "SQLite3 (WAL Mode Enabled)"),
            ("Default Bandwidth", f"{SIM_DEFAULTS.DEFAULT_BANDWIDTH_MBPS} Mbps"),
            ("Default Propagation Delay", f"{SIM_DEFAULTS.DEFAULT_PROPAGATION_DELAY_MS} ms"),
            ("Default Queue Capacity", f"{SIM_DEFAULTS.DEFAULT_QUEUE_CAPACITY_PACKETS} packets (Drop-Tail)"),
            ("Clock Rate", f"{1000.0 / SIM_DEFAULTS.TICK_INTERVAL_MS:.0f} Hz ({SIM_DEFAULTS.TICK_INTERVAL_MS} ms ticks)"),
        ]

        for i, (key, val) in enumerate(specs):
            r, c = divmod(i, 2)
            lbl_k = QLabel(f"• {key}:")
            lbl_k.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
            lbl_v = QLabel(val)
            lbl_v.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10px;")
            specs_layout.addWidget(lbl_k, r, c * 2)
            specs_layout.addWidget(lbl_v, r, c * 2 + 1)

        layout.addWidget(specs_group)

        # ── Group 3: Architecture & Flow Notes ───────────────────────
        arch_group = QGroupBox("Clean Architecture Principles")
        arch_group.setStyleSheet(get_groupbox_stylesheet())
        arch_layout = QVBoxLayout(arch_group)

        arch_txt = QTextEdit()
        arch_txt.setReadOnly(True)
        arch_txt.setMinimumHeight(110)
        arch_txt.setStyleSheet(f"background-color: {CONTAINER_BG}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_COLOR}; font-size: 10px;")
        arch_txt.setPlainText(
            "NETSIMX System Architecture Summary:\n\n"
            "1. Presentation Layer (GUI): PyQt6 QMainWindow shell, Dashboard, Topology Studio, Analytics & Packet Tracer Panel.\n"
            "2. Integration Layer (Adapters): TopologyAdapter, RoutingAdapter, SimulationAdapter, FailureAdapter.\n"
            "3. Business Logic Layer (Core Engines):\n"
            "   - Core Simulation Engine (EventManager, Packet lifecycle, QueueModel)\n"
            "   - Routing Engine (Dijkstra, Bellman-Ford, Distance Vector)\n"
            "   - Failure Engine (FailureManager, link/node status toggles)\n"
            "4. Data Persistence Layer (Database):\n"
            "   - SQLite database with WAL journal mode\n"
            "   - ExperimentManager storing topologies, metrics, snapshots, and algorithm benchmark comparisons."
        )
        arch_layout.addWidget(arch_txt)
        layout.addWidget(arch_group)

        layout.addStretch()
