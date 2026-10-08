"""
NetSimX — Traffic Simulation Panel (Member 4)
Controls for configuring and starting/stopping simulations using Member 3's engine.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


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
        self.setStyleSheet("background: #1A1A2A; color: #CCCCDD;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Traffic Simulation")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet("color: #EEEEFF;")
        layout.addWidget(title)

        # ── Config group ──────────────────────────────────────────────
        cfg_group = QGroupBox("Simulation Configuration")
        cfg_group.setStyleSheet(self._group_style())
        cfg_layout = QVBoxLayout(cfg_group)
        cfg_layout.setSpacing(8)

        def _row(lbl_text, widget):
            row = QHBoxLayout()
            lbl = QLabel(lbl_text)
            lbl.setMinimumWidth(120)
            lbl.setStyleSheet("color: #9999BB; font-size: 10px;")
            row.addWidget(lbl)
            row.addWidget(widget)
            row.addStretch()
            return row

        self._src_combo = QComboBox(); self._src_combo.setMinimumWidth(160)
        self._dst_combo = QComboBox(); self._dst_combo.setMinimumWidth(160)
        self._algo_combo = QComboBox(); self._algo_combo.setMinimumWidth(160)
        self._level_combo = QComboBox(); self._level_combo.setMinimumWidth(160)
        self._count_spin = QSpinBox(); self._count_spin.setRange(10, 5000)
        self._count_spin.setValue(100); self._count_spin.setSingleStep(50)
        self._size_spin = QSpinBox(); self._size_spin.setRange(64, 9000)
        self._size_spin.setValue(1024); self._size_spin.setSingleStep(512)

        for w in [self._src_combo, self._dst_combo, self._algo_combo, self._level_combo]:
            w.setStyleSheet(self._combo_style())

        for w in [self._count_spin, self._size_spin]:
            w.setStyleSheet("QSpinBox { background: #2A2A3E; color: #CCCCDD; "
                            "border: 1px solid #444466; border-radius: 4px; padding: 3px; }")

        self._algo_combo.addItems(["Dijkstra", "Bellman-Ford", "Distance Vector"])
        self._level_combo.addItems(["LOW", "MEDIUM", "HIGH", "CUSTOM"])
        self._level_combo.currentTextChanged.connect(self._on_level_changed)

        cfg_layout.addLayout(_row("Source:", self._src_combo))
        cfg_layout.addLayout(_row("Destination:", self._dst_combo))
        cfg_layout.addLayout(_row("Algorithm:", self._algo_combo))
        cfg_layout.addLayout(_row("Traffic Level:", self._level_combo))
        cfg_layout.addLayout(_row("Packet Count:", self._count_spin))
        cfg_layout.addLayout(_row("Packet Size (bytes):", self._size_spin))
        layout.addWidget(cfg_group)

        # ── Control buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start Simulation")
        self._start_btn.setStyleSheet(self._btn_style("#3A7A3A"))
        self._start_btn.clicked.connect(self._start)

        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setStyleSheet(self._btn_style("#7A2A2A"))
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── Status ────────────────────────────────────────────────────
        self._status_label = QLabel("Status: IDLE")
        self._status_label.setStyleSheet("color: #9999BB; font-size: 10px;")
        layout.addWidget(self._status_label)

        # ── Log ───────────────────────────────────────────────────────
        log_group = QGroupBox("Simulation Log")
        log_group.setStyleSheet(self._group_style())
        log_layout = QVBoxLayout(log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(150)
        self._log.setStyleSheet(
            "QTextEdit { background: #0A0A1A; color: #88AACC; "
            "border: 1px solid #333355; font-family: Consolas, monospace; font-size: 9px; }")
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
        self._status_label.setStyleSheet("color: #5CB85C; font-size: 10px; font-weight: bold;")
        self._log_msg(f"Simulation started: {src} → {dst} [{self._algo_combo.currentText()}]")
        self.simulation_started.emit()

    def _stop(self) -> None:
        self._sim.stop()
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_label.setText("Status: STOPPED")
        self._status_label.setStyleSheet("color: #FF7755; font-size: 10px;")
        self._log_msg("Simulation stopped by user.")
        self.simulation_stopped.emit()

    def _on_tick(self, snapshot) -> None:
        pass  # Handled by MonitoringPanel / DashboardPanel

    def _on_finished(self, stats) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_label.setText("Status: COMPLETED")
        self._status_label.setStyleSheet("color: #4A90D9; font-size: 10px; font-weight: bold;")
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
        self._status_label.setStyleSheet("color: #CC3333; font-size: 10px;")
        self._log_msg(f"ERROR: {msg}")

    def _log_msg(self, msg: str) -> None:
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{ts}] {msg}")

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    @staticmethod
    def _group_style() -> str:
        return ("QGroupBox { color: #AAAACC; border: 1px solid #444466; "
                "border-radius: 6px; margin-top: 6px; padding-top: 10px; font-size: 10px; }")

    @staticmethod
    def _combo_style() -> str:
        return ("QComboBox { background: #2A2A3E; color: #CCCCDD; "
                "border: 1px solid #444466; border-radius: 4px; padding: 3px 8px; font-size: 10px; }"
                "QComboBox::drop-down { border: none; }"
                "QComboBox QAbstractItemView { background: #2A2A3E; color: #CCCCDD; }")

    @staticmethod
    def _btn_style(bg: str) -> str:
        return (f"QPushButton {{ background: {bg}; color: #FFFFFF; "
                "border: none; border-radius: 4px; padding: 8px 20px; "
                "font-size: 10px; font-weight: bold; }"
                "QPushButton:disabled { background: #333344; color: #666677; }"
                "QPushButton:hover:enabled { opacity: 0.85; }")
