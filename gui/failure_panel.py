"""
NetSimX — Failure Simulation Panel (Member 4)
Controls for injecting node and link failures using Member 3's FailureManager.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont


class FailurePanel(QWidget):
    """Failure injection control panel."""

    failure_occurred = pyqtSignal(str, str)   # (type, target_id)
    recovery_occurred = pyqtSignal(str, str)

    def __init__(self, topology_adapter, failure_adapter,
                 topology_view=None, parent=None):
        super().__init__(parent)
        self._topo = topology_adapter
        self._failure = failure_adapter
        self._topology_view = topology_view
        self._setup_ui()
        self._populate_targets()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: #1A1A2A; color: #CCCCDD;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Failure Simulation")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet("color: #EEEEFF;")
        layout.addWidget(title)

        # ── Target type ───────────────────────────────────────────────
        type_group = QGroupBox("Target Type")
        type_group.setStyleSheet(self._group_style())
        type_row = QHBoxLayout(type_group)
        self._node_radio = QRadioButton("Node / Router")
        self._link_radio = QRadioButton("Link")
        self._node_radio.setChecked(True)
        for r in [self._node_radio, self._link_radio]:
            r.setStyleSheet("color: #CCCCDD; font-size: 10px;")
        self._btn_group = QButtonGroup()
        self._btn_group.addButton(self._node_radio, 0)
        self._btn_group.addButton(self._link_radio, 1)
        type_row.addWidget(self._node_radio)
        type_row.addWidget(self._link_radio)
        type_row.addStretch()
        self._node_radio.toggled.connect(self._on_type_changed)
        layout.addWidget(type_group)

        # ── Target selection ──────────────────────────────────────────
        tgt_group = QGroupBox("Target Selection")
        tgt_group.setStyleSheet(self._group_style())
        tgt_layout = QHBoxLayout(tgt_group)
        tgt_lbl = QLabel("Target:")
        tgt_lbl.setStyleSheet("color: #9999BB; font-size: 10px;")
        tgt_lbl.setMinimumWidth(60)
        self._target_combo = QComboBox()
        self._target_combo.setMinimumWidth(200)
        self._target_combo.setStyleSheet(self._combo_style())
        tgt_layout.addWidget(tgt_lbl)
        tgt_layout.addWidget(self._target_combo)
        tgt_layout.addStretch()
        layout.addWidget(tgt_group)

        # ── Action buttons ────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._fail_btn = QPushButton("⚡  Inject Failure")
        self._fail_btn.setStyleSheet(self._btn_style("#8B2222"))
        self._fail_btn.clicked.connect(self._inject_failure)

        self._restore_btn = QPushButton("✓  Restore")
        self._restore_btn.setStyleSheet(self._btn_style("#226622"))
        self._restore_btn.clicked.connect(self._restore)

        self._restore_all_btn = QPushButton("Restore All")
        self._restore_all_btn.setStyleSheet(self._btn_style("#334455"))
        self._restore_all_btn.clicked.connect(self._restore_all)

        btn_row.addWidget(self._fail_btn)
        btn_row.addWidget(self._restore_btn)
        btn_row.addWidget(self._restore_all_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── Status display ────────────────────────────────────────────
        status_group = QGroupBox("Current Failures")
        status_group.setStyleSheet(self._group_style())
        status_layout = QVBoxLayout(status_group)

        self._status_label = QLabel("No active failures.")
        self._status_label.setStyleSheet("color: #5CB85C; font-size: 10px;")
        self._status_label.setWordWrap(True)
        status_layout.addWidget(self._status_label)
        layout.addWidget(status_group)

        # ── Event log ─────────────────────────────────────────────────
        log_group = QGroupBox("Event Log")
        log_group.setStyleSheet(self._group_style())
        log_layout = QVBoxLayout(log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(160)
        self._log.setStyleSheet(
            "QTextEdit { background: #0A0A1A; color: #FFAA55; "
            "border: 1px solid #333355; font-family: Consolas, monospace; font-size: 9px; }")
        log_layout.addWidget(self._log)
        layout.addWidget(log_group)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def _populate_targets(self) -> None:
        self._target_combo.clear()
        if self._node_radio.isChecked():
            ids = self._topo.get_node_ids()
        else:
            ids = self._topo.get_link_ids()
        self._target_combo.addItems(ids)

    def _on_type_changed(self) -> None:
        self._populate_targets()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _inject_failure(self) -> None:
        target = self._target_combo.currentText()
        if not target:
            return

        if self._node_radio.isChecked():
            ok = self._failure.fail_node(target)
            ftype = "NODE"
        else:
            ok = self._failure.fail_link(target)
            ftype = "LINK"

        if ok:
            self._log_msg(f"FAILURE INJECTED: {ftype} '{target}' → OFFLINE")
            if self._topology_view:
                if ftype == "NODE":
                    self._topology_view.update_node_status(target, False)
                else:
                    self._topology_view.update_link_status(target, False)
            self.failure_occurred.emit(ftype, target)
        else:
            self._log_msg(f"Failed to inject failure on '{target}' (not found?)")

        self._update_status()

    def _restore(self) -> None:
        target = self._target_combo.currentText()
        if not target:
            return

        if self._node_radio.isChecked():
            ok = self._failure.restore_node(target)
            ftype = "NODE"
        else:
            ok = self._failure.restore_link(target)
            ftype = "LINK"

        if ok:
            self._log_msg(f"RESTORED: {ftype} '{target}' → ONLINE")
            if self._topology_view:
                if ftype == "NODE":
                    self._topology_view.update_node_status(target, True)
                else:
                    self._topology_view.update_link_status(target, True)
            self.recovery_occurred.emit(ftype, target)
        else:
            self._log_msg(f"Could not restore '{target}'")

        self._update_status()

    def _restore_all(self) -> None:
        for nid in list(self._failure.get_failed_nodes()):
            self._failure.restore_node(nid)
            if self._topology_view:
                self._topology_view.update_node_status(nid, True)
        for lid in list(self._failure.get_failed_links()):
            self._failure.restore_link(lid)
            if self._topology_view:
                self._topology_view.update_link_status(lid, True)
        self._log_msg("All failures restored.")
        self._update_status()

    def _update_status(self) -> None:
        fn = self._failure.get_failed_nodes()
        fl = self._failure.get_failed_links()
        parts = []
        if fn:
            parts.append(f"Failed nodes: {', '.join(fn)}")
        if fl:
            parts.append(f"Failed links: {', '.join(fl)}")
        if parts:
            self._status_label.setText("\n".join(parts))
            self._status_label.setStyleSheet("color: #FF7755; font-size: 10px;")
        else:
            self._status_label.setText("No active failures.")
            self._status_label.setStyleSheet("color: #5CB85C; font-size: 10px;")

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
                "border: none; border-radius: 4px; padding: 7px 16px; "
                "font-size: 10px; font-weight: bold; }}"
                "QPushButton:hover { opacity: 0.85; }")
