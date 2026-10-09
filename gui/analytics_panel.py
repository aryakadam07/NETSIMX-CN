"""
NetSimX — Analytics Panel (Member 4 / Redesign)
Matplotlib-powered charts for simulation results in charcoal & emerald styling.
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from visualization.charts import MatplotlibCanvas
from gui.styles import (
    MAIN_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR, TEXT_PRIMARY,
    TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL,
    get_secondary_button_stylesheet
)


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
        self.setStyleSheet(f"background-color: {MAIN_BG}; color: {TEXT_PRIMARY};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Performance Analytics Studio")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        # Refresh button
        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("⟳  Refresh Charts")
        self._refresh_btn.setStyleSheet(get_secondary_button_stylesheet())
        self._refresh_btn.clicked.connect(self._refresh_all)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Tab widget with charts
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {BORDER_COLOR}; background: {CARD_BG}; border-radius: 6px; }}
            QTabBar::tab {{ background: {CONTAINER_BG}; color: {TEXT_SECONDARY}; padding: 7px 16px;
                           border-radius: 4px; margin-right: 4px; font-size: 10px; font-weight: bold; }}
            QTabBar::tab:selected {{ background: {CARD_BG}; color: {ACCENT_EMERALD}; border-bottom: 2px solid {ACCENT_EMERALD}; }}
            QTabBar::tab:hover {{ color: {TEXT_PRIMARY}; background: #2A2A2A; }}
        """)

        self._canvas_throughput = MatplotlibCanvas()
        self._canvas_latency    = MatplotlibCanvas()
        self._canvas_loss       = MatplotlibCanvas()
        self._canvas_queue      = MatplotlibCanvas()
        self._canvas_pdr        = MatplotlibCanvas()

        self._tabs.addTab(self._canvas_throughput, "Throughput (Mbps)")
        self._tabs.addTab(self._canvas_latency,    "Latency (ms)")
        self._tabs.addTab(self._canvas_loss,       "Packet Loss (%)")
        self._tabs.addTab(self._canvas_pdr,        "PDR (%)")
        self._tabs.addTab(self._canvas_queue,      "Queue Depth")

        layout.addWidget(self._tabs)

        # No data label
        self._no_data = QLabel(
            "No simulation data available yet.\n"
            "Run a simulation in Traffic Simulation panel to generate analytics curves."
        )
        self._no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_data.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; padding: 20px;")
        layout.addWidget(self._no_data)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_snapshots(self, snapshots: list,
                       queue_history: Dict[str, list] = None) -> None:
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
            title="Throughput vs Simulation Time",
            xlabel="Simulation Time (ms)",
            ylabel="Throughput (Mbps)",
            color=ACCENT_EMERALD,
            label="Throughput"
        )

    def plot_latency(self, snapshots: list) -> None:
        times, values = self._extract_series(snapshots, "latency")
        self._canvas_latency.plot_line(
            times, values,
            title="Average Latency vs Simulation Time",
            xlabel="Simulation Time (ms)",
            ylabel="Latency (ms)",
            color=ACCENT_ORANGE,
            label="Avg Latency"
        )

    def plot_packet_loss(self, snapshots: list) -> None:
        times, values = self._extract_series(snapshots, "loss")
        self._canvas_loss.plot_line(
            times, values,
            title="Packet Loss % vs Simulation Time",
            xlabel="Simulation Time (ms)",
            ylabel="Packet Loss (%)",
            color=ACCENT_CORAL,
            label="Loss %"
        )

    def plot_pdr(self, snapshots: list) -> None:
        times, values = self._extract_series(snapshots, "pdr")
        self._canvas_pdr.plot_line(
            times, values,
            title="Packet Delivery Ratio vs Simulation Time",
            xlabel="Simulation Time (ms)",
            ylabel="PDR (%)",
            color=ACCENT_EMERALD,
            label="PDR %"
        )

    def plot_queue_depth(self, queue_history: Dict[str, list]) -> None:
        self._canvas_queue.clear()
        if not queue_history:
            return

        colors = [ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL, "#34D399", "#F59E0B", "#D97706"]
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
                title="Queue Depth vs Simulation Time",
                xlabel="Simulation Time (ms)",
                ylabel="Queue Depth (packets)"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_series(self, snapshots: list, metric: str):
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
