"""
NetSimX — Traffic Simulation Panel (Member 4 / Redesign)
Controls for configuring and starting/stopping simulations in charcoal & emerald.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from gui.styles import (
    MAIN_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR, TEXT_PRIMARY,
    TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL,
    get_groupbox_stylesheet, get_input_stylesheet, get_button_stylesheet,
    get_secondary_button_stylesheet, get_danger_button_stylesheet, get_text_edit_stylesheet
)


class TrafficPanel(QWidget):
    """
    Traffic configuration and simulation control panel.
    Delegates actual simulation to SimulationAdapter.
    """

    simulation_started = pyqtSignal()
    simulation_stopped = pyqtSignal()

    def __init__(self, topology_adapter, simulation_adapter, parent=None):
        super().__init__(parent)
        self._topo = topology_adapter
        self._sim = simulation_adapter
        self._setup_ui()
        self._populate_nodes()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"background-color: {MAIN_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Traffic Simulation Engine")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        # ── Config group ──────────────────────────────────────────────
        cfg_group = QGroupBox("Simulation Profile & Packet Controls")
        cfg_group.setStyleSheet(get_groupbox_stylesheet())
        cfg_layout = QVBoxLayout(cfg_group)
        cfg_layout.setSpacing(10)

        def _row(lbl_text, widget):
            row = QHBoxLayout()
            lbl = QLabel(lbl_text)
            lbl.setMinimumWidth(130)
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
            row.addWidget(lbl)
            row.addWidget(widget)
            row.addStretch()
            return row

        self._src_combo = QComboBox(); self._src_combo.setMinimumWidth(180)
        self._dst_combo = QComboBox(); self._dst_combo.setMinimumWidth(180)
        self._algo_combo = QComboBox(); self._algo_combo.setMinimumWidth(180)
        self._level_combo = QComboBox(); self._level_combo.setMinimumWidth(180)
        self._count_spin = QSpinBox(); self._count_spin.setRange(10, 5000)
        self._count_spin.setValue(100); self._count_spin.setSingleStep(50)
        self._size_spin = QSpinBox(); self._size_spin.setRange(64, 9000)
        self._size_spin.setValue(1024); self._size_spin.setSingleStep(512)

        for w in [self._src_combo, self._dst_combo, self._algo_combo, self._level_combo, self._count_spin, self._size_spin]:
            w.setStyleSheet(get_input_stylesheet())

        self._algo_combo.addItems(["Dijkstra", "Bellman-Ford", "Distance Vector"])
        self._level_combo.addItems(["LOW", "MEDIUM", "HIGH", "CUSTOM"])
        self._level_combo.currentTextChanged.connect(self._on_level_changed)

        cfg_layout.addLayout(_row("Source Node:", self._src_combo))
        cfg_layout.addLayout(_row("Destination Node:", self._dst_combo))
        cfg_layout.addLayout(_row("Routing Algorithm:", self._algo_combo))
        cfg_layout.addLayout(_row("Traffic Preset:", self._level_combo))
        cfg_layout.addLayout(_row("Packet Count:", self._count_spin))
        cfg_layout.addLayout(_row("Packet Size (Bytes):", self._size_spin))
        layout.addWidget(cfg_group)

        # ── Control buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start Simulation")
        self._start_btn.setStyleSheet(get_button_stylesheet(ACCENT_EMERALD, "#101010"))
        self._start_btn.clicked.connect(self._start)

        self._stop_btn = QPushButton("■  Stop Simulation")
        self._stop_btn.setStyleSheet(get_danger_button_stylesheet())
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── Status ────────────────────────────────────────────────────
        self._status_label = QLabel("Status: IDLE")
        self._status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._status_label)

        # ── Log ───────────────────────────────────────────────────────
        log_group = QGroupBox("Live Simulation Console Log")
        log_group.setStyleSheet(get_groupbox_stylesheet())
        log_layout = QVBoxLayout(log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(150)
        self._log.setStyleSheet(get_text_edit_stylesheet(ACCENT_EMERALD))
        log_layout.addWidget(self._log)
        layout.addWidget(log_group)

        layout.addStretch()

    def _connect_signals(self) -> None:
        self._sim.tick_received.connect(self._on_tick)
        self._sim.simulation_finished.connect(self._on_finished)
        self._sim.error_occurred.connect(self._on_error)

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def _populate_nodes(self) -> None:
        node_ids = self._topo.get_node_ids()
        for c in [self._src_combo, self._dst_combo]:
            c.clear()
            c.addItems(node_ids)
        if len(node_ids) > 1:
            self._dst_combo.setCurrentIndex(len(node_ids) - 1)

    def _on_level_changed(self, level: str) -> None:
        custom = level == "CUSTOM"
        self._count_spin.setEnabled(custom)
        self._size_spin.setEnabled(custom)
        if not custom:
            presets = {"LOW": 100, "MEDIUM": 500, "HIGH": 1000}
            self._count_spin.setValue(presets.get(level, 100))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start(self) -> None:
        src = self._src_combo.currentText()
        dst = self._dst_combo.currentText()
        if not src or not dst or src == dst:
            self._log_msg("Error: Select different source and destination.")
            return

        self._sim.configure(
            source=src,
            destination=dst,
            algorithm=self._algo_combo.currentText(),
            packet_count=self._count_spin.value(),
            packet_size=self._size_spin.value(),
            traffic_level=self._level_combo.currentText(),
        )
        self._sim.start()
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_label.setText("Status: RUNNING")
        self._status_label.setStyleSheet(f"color: {ACCENT_EMERALD}; font-size: 11px; font-weight: bold;")
        self._log_msg(f"Simulation started: {src} → {dst} [{self._algo_combo.currentText()}]")
        self.simulation_started.emit()

    def _stop(self) -> None:
        self._sim.stop()
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_label.setText("Status: STOPPED")
        self._status_label.setStyleSheet(f"color: {ACCENT_CORAL}; font-size: 11px;")
        self._log_msg("Simulation stopped by user.")
        self.simulation_stopped.emit()

    def _on_tick(self, snapshot) -> None:
        pass

    def _on_finished(self, stats) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_label.setText("Status: COMPLETED")
        self._status_label.setStyleSheet(f"color: {ACCENT_EMERALD}; font-size: 11px; font-weight: bold;")
        self._log_msg(
            f"Complete — Sent: {stats.packets_sent} | "
            f"Delivered: {stats.packets_delivered} | "
            f"Dropped: {stats.packets_dropped} | "
            f"PDR: {stats.pdr_percent:.1f}%"
        )
        self.simulation_stopped.emit()

    def _on_error(self, msg: str) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_label.setText("Status: ERROR")
        self._status_label.setStyleSheet(f"color: {ACCENT_CORAL}; font-size: 11px;")
        self._log_msg(f"ERROR: {msg}")

    def _log_msg(self, msg: str) -> None:
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{ts}] {msg}")
