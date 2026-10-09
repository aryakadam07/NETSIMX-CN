"""
NetSimX — Dashboard Panel (Member 4 / Redesign)
Shows Welcome Hero banner, network status cards, KPI cards, and live event alerts in charcoal & emerald.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QScrollArea, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from gui.styles import (
    MAIN_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR, TEXT_PRIMARY,
    TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL,
    get_groupbox_stylesheet, get_button_stylesheet, get_secondary_button_stylesheet
)
from gui.widgets.metric_card import MetricCard
from gui.widgets.alert_widget import AlertWidget
from analytics.metrics import MetricsCalculator


class DashboardPanel(QWidget):
    """
    Main dashboard panel.
    Displays Hero Header, Network Status Cards, Simulation KPI Cards, State Badge, and Event Alerts.
    """

    open_topology_requested = pyqtSignal()  # Signal to switch to Topology tab

    def __init__(self, topology_adapter, simulation_adapter, parent=None):
        super().__init__(parent)
        self._topo = topology_adapter
        self._sim = simulation_adapter
        self._prev_snapshot = None
        self._setup_ui()
        self.update_topology_stats()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"background-color: {MAIN_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── 1. Welcome Hero Banner ───────────────────────────────────
        hero_card = QFrame()
        hero_card.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
        """)
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(16, 14, 16, 14)

        text_v = QVBoxLayout()
        title = QLabel("NETSIMX — Network Intelligence Studio")
        tf = QFont(); tf.setPointSize(15); tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet(f"color: {ACCENT_EMERALD}; border: none; background: transparent;")

        sub = QLabel("Design networks. Simulate traffic. Analyse performance. Understand failures.")
        sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; border: none; background: transparent;")

        text_v.addWidget(title)
        text_v.addWidget(sub)

        # Primary Action Button: Open Topology Studio
        self._open_topo_btn = QPushButton("Open Topology Studio")
        self._open_topo_btn.setStyleSheet(get_button_stylesheet(ACCENT_EMERALD, "#101010"))
        self._open_topo_btn.clicked.connect(lambda: self.open_topology_requested.emit())

        hero_layout.addLayout(text_v)
        hero_layout.addStretch()
        hero_layout.addWidget(self._open_topo_btn)

        layout.addWidget(hero_card)

        # ── 2. Network Overview Group ─────────────────────────────────
        net_group = QGroupBox("Network Topology Overview")
        net_group.setStyleSheet(get_groupbox_stylesheet())
        net_row = QHBoxLayout(net_group)
        net_row.setContentsMargins(10, 10, 10, 10)
        net_row.setSpacing(8)

        self._card_nodes    = MetricCard("Total Nodes",   "—", "")
        self._card_links    = MetricCard("Active Links",  "—", "")
        self._card_routers  = MetricCard("Routers",       "—", "")
        self._card_switches = MetricCard("Switches",      "—", "")
        self._card_pcs      = MetricCard("PCs",           "—", "")
        self._card_servers  = MetricCard("Servers",       "—", "")
        self._card_failed_n = MetricCard("Failed Nodes",  "0", "")
        self._card_failed_l = MetricCard("Failed Links",  "0", "")

        for c in [self._card_nodes, self._card_links, self._card_routers,
                  self._card_switches, self._card_pcs, self._card_servers,
                  self._card_failed_n, self._card_failed_l]:
            net_row.addWidget(c)
        net_row.addStretch()
        layout.addWidget(net_group)

        # ── 3. Simulation KPI Metrics Group ───────────────────────────
        sim_group = QGroupBox("Simulation KPI Performance")
        sim_group.setStyleSheet(get_groupbox_stylesheet())
        sim_row = QHBoxLayout(sim_group)
        sim_row.setContentsMargins(10, 10, 10, 10)
        sim_row.setSpacing(8)

        self._card_sent       = MetricCard("Pkts Sent",   "0", "pkts")
        self._card_rcvd       = MetricCard("Delivered",   "0", "pkts")
        self._card_dropped    = MetricCard("Dropped",     "0", "pkts")
        self._card_pdr        = MetricCard("PDR",         "—", "%")
        self._card_loss       = MetricCard("Pkt Loss",    "—", "%")
        self._card_throughput = MetricCard("Throughput",  "—", "Mbps")
        self._card_latency    = MetricCard("Avg Latency", "—", "ms")
        self._card_jitter     = MetricCard("Jitter",      "—", "ms")

        for c in [self._card_sent, self._card_rcvd, self._card_dropped,
                  self._card_pdr, self._card_loss, self._card_throughput,
                  self._card_latency, self._card_jitter]:
            sim_row.addWidget(c)
        sim_row.addStretch()
        layout.addWidget(sim_group)

        # ── 4. Empty State Indicator & Simulation State ───────────────
        state_row = QHBoxLayout()
        state_lbl = QLabel("Engine Status:")
        state_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self._state_value = QLabel("IDLE")
        sf2 = QFont(); sf2.setBold(True); sf2.setPointSize(10)
        self._state_value.setFont(sf2)
        self._state_value.setStyleSheet(f"color: {TEXT_SECONDARY};")

        self._empty_state_lbl = QLabel(" (No simulation run yet. Click 'Traffic Simulation' to start)")
        self._empty_state_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; font-style: italic;")

        state_row.addWidget(state_lbl)
        state_row.addWidget(self._state_value)
        state_row.addWidget(self._empty_state_lbl)
        state_row.addStretch()
        layout.addLayout(state_row)

        # ── 5. Alerts & Activity Log ─────────────────────────────────
        alerts_group = QGroupBox("System Activity & Event Alerts")
        alerts_group.setStyleSheet(get_groupbox_stylesheet())
        alerts_layout = QVBoxLayout(alerts_group)
        alerts_layout.setContentsMargins(6, 8, 6, 6)

        self._alerts = AlertWidget()
        self._alerts.setMinimumHeight(150)
        alerts_layout.addWidget(self._alerts)
        layout.addWidget(alerts_group)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Update methods (called by MainWindow)
    # ------------------------------------------------------------------

    def update_topology_stats(self) -> None:
        """Refresh node/link counts from topology adapter."""
        try:
            stats = self._topo.get_topology_stats()
            self._card_nodes.update_value(str(stats.get("total_nodes", 0)))
            self._card_links.update_value(str(stats.get("active_links", 0)))
            self._card_routers.update_value(str(stats.get("routers", 0)))
            self._card_switches.update_value(str(stats.get("switches", 0)))
            self._card_pcs.update_value(str(stats.get("pcs", 0)))
            self._card_servers.update_value(str(stats.get("servers", 0)))

            fn = stats.get("failed_nodes", 0)
            fl = stats.get("failed_links", 0)
            self._card_failed_n.update_value(str(fn))
            self._card_failed_l.update_value(str(fl))
            self._card_failed_n.set_status("critical" if fn > 0 else "normal")
            self._card_failed_l.set_status("critical" if fl > 0 else "normal")
        except Exception as exc:
            self.add_alert(f"Topology stats error: {exc}", "warning")

    def update_metrics(self, snapshot) -> None:
        """Called on each SimulationTickSnapshot from the worker thread."""
        try:
            m = MetricsCalculator.from_tick(snapshot, self._prev_snapshot)
            self._prev_snapshot = snapshot

            self._card_sent.update_value(str(m["packets_sent"]))
            self._card_rcvd.update_value(str(m["packets_delivered"]))
            self._card_dropped.update_value(str(m["packets_dropped"]))
            self._card_pdr.update_value(f"{m['pdr_percent']:.1f}")
            self._card_loss.update_value(f"{m['plr_percent']:.1f}")
            self._card_throughput.update_value(f"{m['throughput_mbps']:.2f}")
            self._card_latency.update_value(f"{m['avg_latency_ms']:.1f}")
            self._card_jitter.update_value(f"{m['jitter_ms']:.1f}")

            # Alert thresholds
            if m["plr_percent"] > 10:
                self._card_loss.set_status("critical")
                self.add_alert(f"Packet loss {m['plr_percent']:.1f}% exceeded 10% threshold", "critical")
            elif m["plr_percent"] > 5:
                self._card_loss.set_status("warning")

            if m["avg_latency_ms"] > 200:
                self._card_latency.set_status("warning")

            self.set_simulation_state("RUNNING")
        except Exception as exc:
            pass  # Swallow tick errors silently

    def set_simulation_state(self, state: str) -> None:
        self._state_value.setText(state)
        colors = {
            "IDLE": TEXT_SECONDARY,
            "RUNNING": ACCENT_EMERALD,
            "COMPLETED": ACCENT_EMERALD,
            "ERROR": ACCENT_CORAL,
        }
        self._state_value.setStyleSheet(f"color: {colors.get(state, TEXT_PRIMARY)}; font-weight: bold;")
        if state in ("RUNNING", "COMPLETED"):
            self._empty_state_lbl.hide()
        else:
            self._empty_state_lbl.show()

    def add_alert(self, message: str, level: str = "info") -> None:
        self._alerts.add_alert(message, level)

    def reset_metrics(self) -> None:
        """Reset all metric cards to zero."""
        for c in [self._card_sent, self._card_rcvd, self._card_dropped]:
            c.update_value("0")
        for c in [self._card_pdr, self._card_loss, self._card_throughput,
                  self._card_latency, self._card_jitter]:
            c.update_value("—")
            c.set_status("normal")
        self._prev_snapshot = None
