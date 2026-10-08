"""
NetSimX — Dashboard Panel (Member 4)
Shows topology stats, live KPI cards, and the alert feed.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.widgets.metric_card import MetricCard
from gui.widgets.alert_widget import AlertWidget
from analytics.metrics import MetricsCalculator


class DashboardPanel(QWidget):
    """
    Main dashboard panel.

    Layout:
        [Title]
        [Network Status Cards row]
        [Simulation Metrics Cards row]
        [Alerts area]
    """

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
        self.setStyleSheet("background: #1A1A2A;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("NetSimX — Network Dashboard")
        tf = QFont()
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #EEEEFF;")
        layout.addWidget(title)

        sub = QLabel("Computer Networks Simulation & Performance Analysis Platform")
        sf = QFont()
        sf.setPointSize(9)
        sub.setFont(sf)
        sub.setStyleSheet("color: #7777AA;")
        layout.addWidget(sub)

        # ── Network status section ───────────────────────────────────
        net_group = QGroupBox("Network Status")
        net_group.setStyleSheet(
            "QGroupBox { color: #AAAACC; border: 1px solid #444466; "
            "border-radius: 6px; margin-top: 6px; padding-top: 10px; font-size: 10px; }"
        )
        net_row = QHBoxLayout(net_group)
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

        # ── Simulation metrics section ───────────────────────────────
        sim_group = QGroupBox("Simulation Metrics")
        sim_group.setStyleSheet(net_group.styleSheet())
        sim_row = QHBoxLayout(sim_group)
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

        # ── Simulation state ─────────────────────────────────────────
        state_row = QHBoxLayout()
        state_lbl = QLabel("Simulation State:")
        state_lbl.setStyleSheet("color: #9999BB; font-size: 10px;")
        self._state_value = QLabel("IDLE")
        sf2 = QFont()
        sf2.setBold(True)
        sf2.setPointSize(10)
        self._state_value.setFont(sf2)
        self._state_value.setStyleSheet("color: #5CB85C;")
        state_row.addWidget(state_lbl)
        state_row.addWidget(self._state_value)
        state_row.addStretch()
        layout.addLayout(state_row)

        # ── Alerts ───────────────────────────────────────────────────
        alerts_group = QGroupBox("Alerts & Events")
        alerts_group.setStyleSheet(net_group.styleSheet())
        alerts_layout = QVBoxLayout(alerts_group)
        alerts_layout.setContentsMargins(6, 8, 6, 6)

        self._alerts = AlertWidget()
        self._alerts.setMinimumHeight(160)
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
            "IDLE": "#9999BB", "RUNNING": "#5CB85C",
            "COMPLETED": "#4A90D9", "ERROR": "#CC3333",
        }
        self._state_value.setStyleSheet(
            f"color: {colors.get(state, '#FFFFFF')};"
        )

    def add_alert(self, message: str, level: str = "info") -> None:
        self._alerts.add_alert(message, level)

    def reset_metrics(self) -> None:
        """Reset all metric cards to zero."""
        for c in [self._card_sent, self._card_rcvd, self._card_dropped]:
            c.update_value("0")
        for c in [self._card_pdr, self._card_loss, self._card_throughput,
                  self._card_latency, self._card_jitter]:
            c.update_value("—")
        self._prev_snapshot = None
