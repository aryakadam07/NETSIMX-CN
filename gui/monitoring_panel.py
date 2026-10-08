"""
NetSimX — Live Monitoring Panel (Member 4)
Consumes SimulationTickSnapshot via Qt signals.
Never blocks the GUI thread.
"""

from collections import deque
from typing import Deque, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from gui.widgets.metric_card import MetricCard
from analytics.metrics import MetricsCalculator
from visualization.packet_visualizer import PacketVisualizer


class MonitoringPanel(QWidget):
    """
    Real-time monitoring panel.
    Connects to SimulationAdapter.tick_received to update metrics and queue display.
    """

    MAX_LOG_LINES = 200

    def __init__(self, simulation_adapter, parent=None):
        super().__init__(parent)
        self._sim = simulation_adapter
        self._prev_snapshot = None
        self._tick_count = 0
        self._setup_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: #1A1A2A; color: #CCCCDD;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Live Network Monitor")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet("color: #EEEEFF;")
        layout.addWidget(title)

        self._status_lbl = QLabel("⬤ IDLE — Start a simulation to see live data")
        self._status_lbl.setStyleSheet("color: #9999BB; font-size: 10px;")
        layout.addWidget(self._status_lbl)

        # ── Live metrics cards ─────────────────────────────────────────
        cards_group = QGroupBox("Live Metrics")
        cards_group.setStyleSheet(self._group_style())
        cards_row = QHBoxLayout(cards_group)
        cards_row.setSpacing(8)

        self._card_active    = MetricCard("Active Pkts",  "0", "")
        self._card_delivered = MetricCard("Delivered",    "0", "pkts")
        self._card_dropped   = MetricCard("Dropped",      "0", "pkts")
        self._card_pdr       = MetricCard("PDR",          "—", "%")
        self._card_loss      = MetricCard("Loss",         "—", "%")
        self._card_latency   = MetricCard("Avg Latency",  "—", "ms")
        self._card_jitter    = MetricCard("Jitter",       "—", "ms")
        self._card_throughput = MetricCard("Throughput",  "—", "Mbps")

        for c in [self._card_active, self._card_delivered, self._card_dropped,
                  self._card_pdr, self._card_loss, self._card_latency,
                  self._card_jitter, self._card_throughput]:
            cards_row.addWidget(c)
        cards_row.addStretch()
        layout.addWidget(cards_group)

        # ── Queue depths ───────────────────────────────────────────────
        queue_group = QGroupBox("Interface Queue Depths")
        queue_group.setStyleSheet(self._group_style())
        queue_layout = QVBoxLayout(queue_group)
        self._queue_label = QLabel("No queue data yet.")
        self._queue_label.setStyleSheet(
            "color: #8888AA; font-family: Consolas, monospace; font-size: 9px;")
        self._queue_label.setWordWrap(True)
        queue_layout.addWidget(self._queue_label)
        layout.addWidget(queue_group)

        # ── Tick event log ─────────────────────────────────────────────
        log_group = QGroupBox("Tick Event Log")
        log_group.setStyleSheet(self._group_style())
        log_layout = QVBoxLayout(log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(200)
        self._log.setStyleSheet(
            "QTextEdit { background: #0A0A1A; color: #7799BB; "
            "border: 1px solid #333355; font-family: Consolas, monospace; font-size: 9px; }"
        )
        log_layout.addWidget(self._log)
        layout.addWidget(log_group)

        layout.addStretch()

    def _connect_signals(self) -> None:
        self._sim.tick_received.connect(self.on_tick)
        self._sim.simulation_finished.connect(self._on_finished)

    # ------------------------------------------------------------------
    # Tick handler — called from main thread via Qt signal
    # ------------------------------------------------------------------

    @pyqtSlot(object)
    def on_tick(self, snapshot) -> None:
        """Updates all live metric cards from a SimulationTickSnapshot."""
        self._tick_count += 1
        m = MetricsCalculator.from_tick(snapshot, self._prev_snapshot)
        self._prev_snapshot = snapshot

        self._status_lbl.setText(
            f"⬤ RUNNING — Tick #{self._tick_count} | "
            f"Time: {m['timestamp_ms']:.0f} ms"
        )
        self._status_lbl.setStyleSheet("color: #5CB85C; font-size: 10px;")

        self._card_active.update_value(str(m["active_packets"]))
        self._card_delivered.update_value(str(m["packets_delivered"]))
        self._card_dropped.update_value(str(m["packets_dropped"]))
        self._card_pdr.update_value(f"{m['pdr_percent']:.1f}")
        self._card_loss.update_value(f"{m['plr_percent']:.1f}")
        self._card_latency.update_value(f"{m['avg_latency_ms']:.1f}")
        self._card_jitter.update_value(f"{m['jitter_ms']:.1f}")
        self._card_throughput.update_value(f"{m['throughput_mbps']:.2f}")

        # Threshold alerts
        if m["plr_percent"] > 10:
            self._card_loss.set_status("critical")
        elif m["plr_percent"] > 5:
            self._card_loss.set_status("warning")
        else:
            self._card_loss.set_status("normal")

        # Queue depths
        qd = m.get("queue_depths", {})
        if qd:
            parts = [f"{lid}: {depth}" for lid, depth in qd.items()]
            self._queue_label.setText("  |  ".join(parts))

        # Events from this tick
        events = getattr(snapshot, "executed_events", [])
        for ev in events:
            self._log.append(f"[t={m['timestamp_ms']:.0f}ms] {ev}")

        # Limit log size
        doc = self._log.document()
        while doc.blockCount() > self.MAX_LOG_LINES:
            cursor = self._log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def _on_finished(self, stats) -> None:
        self._status_lbl.setText(
            f"⬤ COMPLETED — "
            f"Sent: {stats.packets_sent} | "
            f"Delivered: {stats.packets_delivered} | "
            f"Dropped: {stats.packets_dropped}"
        )
        self._status_lbl.setStyleSheet("color: #4A90D9; font-size: 10px;")

    def start_monitoring(self) -> None:
        self._tick_count = 0
        self._prev_snapshot = None

    def stop_monitoring(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------

    @staticmethod
    def _group_style() -> str:
        return ("QGroupBox { color: #AAAACC; border: 1px solid #444466; "
                "border-radius: 6px; margin-top: 6px; padding-top: 10px; font-size: 10px; }")
