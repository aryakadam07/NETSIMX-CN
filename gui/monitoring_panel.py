"""
NetSimX — Live Monitoring Panel (Member 4 / Redesign)
Consumes SimulationTickSnapshot via Qt signals in charcoal & emerald styling.
"""

from collections import deque
from typing import Deque, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from gui.styles import (
    MAIN_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR, TEXT_PRIMARY,
    TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL,
    get_groupbox_stylesheet, get_text_edit_stylesheet
)
from gui.widgets.metric_card import MetricCard
from analytics.metrics import MetricsCalculator


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
        self.setStyleSheet(f"background-color: {MAIN_BG}; color: {TEXT_PRIMARY};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Live Simulation Telemetry & Queue Monitor")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        self._status_lbl = QLabel("IDLE — Start a simulation to stream live telemetry")
        self._status_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._status_lbl)

        # ── Live metrics cards ─────────────────────────────────────────
        cards_group = QGroupBox("Real-Time KPI Stream")
        cards_group.setStyleSheet(get_groupbox_stylesheet())
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
        queue_group = QGroupBox("Interface Queue Occupancy Depths")
        queue_group.setStyleSheet(get_groupbox_stylesheet())
        queue_layout = QVBoxLayout(queue_group)
        self._queue_label = QLabel("No active queue data streamed yet.")
        self._queue_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: 'Consolas', monospace; font-size: 11px;")
        self._queue_label.setWordWrap(True)
        queue_layout.addWidget(self._queue_label)
        layout.addWidget(queue_group)

        # ── Tick event log ─────────────────────────────────────────────
        log_group = QGroupBox("Tick Event & Packet Lifecycle Log")
        log_group.setStyleSheet(get_groupbox_stylesheet())
        log_layout = QVBoxLayout(log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(200)
        self._log.setStyleSheet(get_text_edit_stylesheet(ACCENT_EMERALD))
        log_layout.addWidget(self._log)
        layout.addWidget(log_group)

        layout.addStretch()

    def _connect_signals(self) -> None:
        self._sim.tick_received.connect(self.on_tick)
        self._sim.simulation_finished.connect(self._on_finished)

    # ------------------------------------------------------------------
    # Tick handler
    # ------------------------------------------------------------------

    @pyqtSlot(object)
    def on_tick(self, snapshot) -> None:
        self._tick_count += 1
        m = MetricsCalculator.from_tick(snapshot, self._prev_snapshot)
        self._prev_snapshot = snapshot

        self._status_lbl.setText(
            f"RUNNING — Tick #{self._tick_count} | Time: {m['timestamp_ms']:.0f} ms"
        )
        self._status_lbl.setStyleSheet(f"color: {ACCENT_EMERALD}; font-size: 11px; font-weight: bold;")

        self._card_active.update_value(str(m["active_packets"]))
        self._card_delivered.update_value(str(m["packets_delivered"]))
        self._card_dropped.update_value(str(m["packets_dropped"]))
        self._card_pdr.update_value(f"{m['pdr_percent']:.1f}")
        self._card_loss.update_value(f"{m['plr_percent']:.1f}")
        self._card_latency.update_value(f"{m['avg_latency_ms']:.1f}")
        self._card_jitter.update_value(f"{m['jitter_ms']:.1f}")
        self._card_throughput.update_value(f"{m['throughput_mbps']:.2f}")

        if m["plr_percent"] > 10:
            self._card_loss.set_status("critical")
        elif m["plr_percent"] > 5:
            self._card_loss.set_status("warning")
        else:
            self._card_loss.set_status("normal")

        qd = m.get("queue_depths", {})
        if qd:
            parts = [f"{lid}: {depth} pkts" for lid, depth in qd.items()]
            self._queue_label.setText("  |  ".join(parts))

        events = getattr(snapshot, "executed_events", [])
        for ev in events:
            self._log.append(f"[t={m['timestamp_ms']:.0f}ms] {ev}")

        doc = self._log.document()
        while doc.blockCount() > self.MAX_LOG_LINES:
            cursor = self._log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def _on_finished(self, stats) -> None:
        self._status_lbl.setText(
            f"COMPLETED — Sent: {stats.packets_sent} | "
            f"Delivered: {stats.packets_delivered} | Dropped: {stats.packets_dropped}"
        )
        self._status_lbl.setStyleSheet(f"color: {ACCENT_EMERALD}; font-size: 11px; font-weight: bold;")

    def start_monitoring(self) -> None:
        self._tick_count = 0
        self._prev_snapshot = None

    def stop_monitoring(self) -> None:
        pass
