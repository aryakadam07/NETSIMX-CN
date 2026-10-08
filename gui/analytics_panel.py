"""
NetSimX — Analytics Panel (Member 4)
Matplotlib-powered charts for simulation results.
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtGui import QFont

from visualization.charts import MatplotlibCanvas


class AnalyticsPanel(QWidget):
    """
    Multi-tab analytics dashboard with embedded Matplotlib charts.
    Charts are populated from SimulationTickSnapshot lists.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshots: list = []
        self._queue_history: Dict[str, list] = {}
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: #1A1A2A; color: #CCCCDD;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Performance Analytics")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet("color: #EEEEFF;")
        layout.addWidget(title)

        # Refresh button
        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("⟳  Refresh Charts")
        self._refresh_btn.setStyleSheet(
            "QPushButton { background: #2A4A6A; color: #FFFFFF; border: none; "
            "border-radius: 4px; padding: 5px 14px; font-size: 10px; }"
            "QPushButton:hover { background: #3A5A7A; }")
        self._refresh_btn.clicked.connect(self._refresh_all)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Tab widget with charts
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #444466; background: #12121E; }"
            "QTabBar::tab { background: #2A2A3E; color: #9999BB; padding: 6px 14px; "
            "border-radius: 4px; margin-right: 2px; font-size: 9px; }"
            "QTabBar::tab:selected { background: #4A4A6E; color: #EEEEFF; }"
        )

        self._canvas_throughput = MatplotlibCanvas()
        self._canvas_latency    = MatplotlibCanvas()
        self._canvas_loss       = MatplotlibCanvas()
        self._canvas_queue      = MatplotlibCanvas()
        self._canvas_pdr        = MatplotlibCanvas()

        self._tabs.addTab(self._canvas_throughput, "Throughput")
        self._tabs.addTab(self._canvas_latency,    "Latency")
        self._tabs.addTab(self._canvas_loss,       "Packet Loss")
        self._tabs.addTab(self._canvas_pdr,        "PDR")
        self._tabs.addTab(self._canvas_queue,      "Queue Depth")

        layout.addWidget(self._tabs)

        # No data label
        self._no_data = QLabel(
            "No simulation data yet.\n"
            "Run a simulation and the charts will populate automatically."
        )
        self._no_data.setAlignment(__import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignCenter)
        self._no_data.setStyleSheet("color: #555577; font-size: 11px;")
        layout.addWidget(self._no_data)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_snapshots(self, snapshots: list,
                       queue_history: Dict[str, list] = None) -> None:
        """
        Called after simulation completes.
        snapshots: list of SimulationTickSnapshot
        queue_history: {link_id: List[QueueSample]}
        """
        self._snapshots = snapshots
        self._queue_history = queue_history or {}
        if snapshots:
            self._no_data.hide()
            self._refresh_all()
        else:
            self._no_data.show()

    # ------------------------------------------------------------------
    # Chart rendering
    # ------------------------------------------------------------------

    def _refresh_all(self) -> None:
        if not self._snapshots:
            return
        self.plot_throughput(self._snapshots)
        self.plot_latency(self._snapshots)
        self.plot_packet_loss(self._snapshots)
        self.plot_pdr(self._snapshots)
        self.plot_queue_depth(self._queue_history)

    def plot_throughput(self, snapshots: list) -> None:
        times, values = self._extract_series(snapshots, "throughput")
        self._canvas_throughput.plot_line(
            times, values,
            title="Throughput vs Time",
            xlabel="Simulation Time (ms)",
            ylabel="Throughput (Mbps)",
            color="#4A90D9",
            label="Throughput"
        )

    def plot_latency(self, snapshots: list) -> None:
        times, values = self._extract_series(snapshots, "latency")
        self._canvas_latency.plot_line(
            times, values,
            title="Average Latency vs Time",
            xlabel="Simulation Time (ms)",
            ylabel="Latency (ms)",
            color="#E8A838",
            label="Avg Latency"
        )

    def plot_packet_loss(self, snapshots: list) -> None:
        times, values = self._extract_series(snapshots, "loss")
        self._canvas_loss.plot_line(
            times, values,
            title="Packet Loss % vs Time",
            xlabel="Simulation Time (ms)",
            ylabel="Packet Loss (%)",
            color="#CC3333",
            label="Loss %"
        )

    def plot_pdr(self, snapshots: list) -> None:
        times, values = self._extract_series(snapshots, "pdr")
        self._canvas_pdr.plot_line(
            times, values,
            title="Packet Delivery Ratio vs Time",
            xlabel="Simulation Time (ms)",
            ylabel="PDR (%)",
            color="#5CB85C",
            label="PDR %"
        )

    def plot_queue_depth(self, queue_history: Dict[str, list]) -> None:
        self._canvas_queue.clear()
        if not queue_history:
            return

        colors = ["#4A90D9", "#E8A838", "#CC3333", "#5CB85C", "#AA55CC", "#55CCAA"]
        series = []
        for i, (link_id, samples) in enumerate(queue_history.items()):
            if samples:
                times = [s.timestamp_ms for s in samples]
                depths = [s.depth_packets for s in samples]
                col = colors[i % len(colors)]
                series.append((times, depths, link_id, col))

        if series:
            self._canvas_queue.plot_multi_line(
                series,
                title="Queue Depth vs Time",
                xlabel="Simulation Time (ms)",
                ylabel="Queue Depth (packets)"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_series(self, snapshots: list, metric: str):
        """Extracts (times, values) from a snapshot list for a given metric."""
        times, values = [], []
        prev_sent = 0
        prev_del = 0

        for i, s in enumerate(snapshots):
            t = getattr(s, "timestamp_ms", i * 50)
            delivered = getattr(s, "packets_delivered", 0)
            dropped = getattr(s, "packets_dropped", 0)
            sent = delivered + dropped
            pdr = getattr(s, "pdr_percent", 0.0)
            avg_lat = getattr(s, "average_delay_ms", 0.0)

            plr = (dropped / sent * 100.0) if sent > 0 else 0.0

            # Instantaneous throughput
            interval_s = 0.05
            new_del = max(0, delivered - prev_del)
            tput = (new_del * 1024 * 8) / (interval_s * 1_000_000)
            prev_del = delivered
            prev_sent = sent

            times.append(t)
            if metric == "throughput":
                values.append(tput)
            elif metric == "latency":
                values.append(avg_lat)
            elif metric == "loss":
                values.append(plr)
            elif metric == "pdr":
                values.append(pdr)

        return times, values
